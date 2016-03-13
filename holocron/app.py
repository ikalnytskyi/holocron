"""
    holocron.app
    ~~~~~~~~~~~~

    This module implements the central Holocron application class.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import logging

# shutil.copytree doesn't fit our needs since it requires destination
# directory to do not exist, while we need it to be existed in order
# to collect static files from different themes
from distutils.dir_util import copy_tree

import yaml
import jinja2

from dooku.conf import Conf
from dooku.decorator import cached_property
from dooku.ext import ExtensionManager

from .content import create_document
from .utils import iterfiles, mkdir


logger = logging.getLogger(__name__)


def create_app(confpath=None):
    """
    Creates a Holocron instance from a given settings file.

    :param confpath: a path to the settings file; use defaults in case of None
    :returns: a :class:`holocron.app.Holocron` instance or None
    """
    try:
        conf = None
        if confpath is not None:
            with open(confpath, 'r', encoding='utf-8') as f:
                # the conf may contain the {here} macro, so we have to
                # replace it with actual value.
                here = os.path.dirname(os.path.abspath(confpath))
                conf = yaml.safe_load(f.read().format(here=here))

    except (FileNotFoundError, PermissionError) as exc:
        # it's ok that a user doesn't have a settings file or doesn't have
        # permissions to read it, so just treat a warning and continue
        # execution.
        logger.warning('%s: %s', exc.filename, exc.strerror)
        logger.warning('Fallback to default settings')

    except (IsADirectoryError, ) as exc:
        # well, if we try to read settings from a directory, it's probably
        # a user have a wrong setup. we have no choice but treat error and
        # do not create application instance.
        logger.error('%s: %s', exc.filename, exc.strerror)
        return None

    except (yaml.YAMLError, ) as exc:
        # we have an ill-formed settings file, thus we can't apply users'
        # settings. in this case it's better show errors and do not create
        # application instance.
        logger.error('%s: %s', confpath, str(exc))
        return None

    return Holocron(conf)


class Holocron(object):
    """
    The Holocron class implements a blog instance.

    Once it's created it will act as a central registry for the extensions,
    converters, template configuration and much more.

    Here the interaction workflow for end-users:

    * create instance with default or custom settings
    * register extensions: converters and/or generators
    * call :meth:`run` method in order to build weblog

    :param conf: (dict) a user configuration, that overrides a default one
    """

    #: The factory function that is used to create a new document instance.
    document_factory = create_document

    #: Default settings.
    default_conf = {
        'site': {
            'title': "Kenobi's Thoughts",
            'author': 'Obi-Wan Kenobi',
            'url': 'http://obi-wan.jedi',
        },

        'encoding': {
            'content': 'utf-8',
            'output': 'utf-8',
        },

        'paths': {
            'content': '.',
            'output': '_build',
        },

        'theme': {},

        'ext': {
            'enabled': [
                'markdown',
                'restructuredtext',

                'index',
                'feed',
                'sitemap',
                'tags',
            ],
        },

        'commands': {
            'serve': {
                'host': '0.0.0.0',
                'port': 5000,
                'wakeup': 1,
            },
        },
    }

    def __init__(self, conf=None):
        #: The configuration dictionary.
        self.conf = Conf(self.default_conf, conf or {})

        #: name -> extension instance
        #:
        #: Contains all registered extensions and is used for preventing them
        #: to be handled by garbage collector. Also I believe it might be
        #: useful for extension developers in future.
        self._extensions = {}

        #: file extension -> converter instance
        #:
        #: Contains all registered converters and is used for retrieving
        #: converters for specific file types (by its extension).
        self._converters = {}

        #: generator instance, ...
        #:
        #: Contains all registered generators and is used for executing them.
        self._generators = []

        #: theme path, ...
        #:
        #: Contains all registered themes. Initially it has only a default one.
        #: Each further added theme will override the previous one, i.e.
        #: it'll have higher priority for templates lookup and static
        #: overwriting.
        #:
        #: .. versionadded:: 0.3.0
        self._themes = [
            os.path.join(os.path.dirname(__file__), 'theme'),
        ]

        #: key -> value
        #:
        #: Contains context values to be passed to theme renderer.
        #:
        #: .. versionadded:: 0.3.0
        self._theme_ctx = {
            'site': self.conf['site'],
            'theme': self.conf['theme'],
            'encoding': self.conf['encoding.output'],
        }

        # discover and execute all found extensions
        for name, ext in ExtensionManager(
            namespace='holocron.ext',
            names=self.conf['ext']['enabled'],
        ):
            if name in self._extensions:
                logger.warning(
                    '%s extension skipped: already registered', name)
                continue
            self._extensions[name] = ext(self)

    def add_converter(self, converter, _force=False):
        """
        Registers a given converter in the application instance.

        :param converter: a converter to be registered
        :param _force: allows to override already registered converters
        """
        for ext in converter.extensions:
            if ext in self._converters and not _force:
                logger.warning(
                    '%s converter skipped for %s: already registered',
                    type(converter).__name__, ext)
                continue

            self._converters[ext] = converter

    def add_generator(self, generator):
        """
        Registers a given generator in the application instance.

        :param generator: a generator to be registered
        """
        self._generators.append(generator)

    def add_theme_ctx(self, **kwargs):
        """
        Pass given keyword arguments to theme templates.

        :param kwargs: key-value argumnets to be passed to theme templates
        """
        overwritten = set(kwargs.keys()) & set(self.jinja_env.globals.keys())
        if overwritten:
            logger.warning(
                'the following theme context is going to be overwritten: %s',
                ', '.join(overwritten))

        self._theme_ctx.update(**kwargs)
        self.jinja_env.globals.update(**kwargs)

    def add_theme(self, theme_path):
        """
        Registers a given theme in the application instance.

        :param theme_path: a path to theme to be registered
        """
        self._themes.append(theme_path)

        # remove evaluated value, so next time we access 'jinja_env' it'll
        # be re-evaluated and new themes will be taken into account
        self.__dict__.pop('jinja_env', None)

    @cached_property
    def jinja_env(self):
        """
        Gets a Jinja2 environment based on Holocron's settings.
        """
        # Themes are consumed in reverse order because jinja2.ChoiceLoader
        # will stop looking for templates as soon as it finds one in current
        # path. Since we want default theme to be low-prio, processing is
        # started from user themes paths.
        loaders = [
            jinja2.FileSystemLoader(os.path.join(theme, 'templates'))
            for theme in reversed(self._themes)
        ]

        # Let's make default theme always available for inheritance
        # via '!default' prefix.
        loaders.append(jinja2.PrefixLoader('!default', loaders[-1]))

        env = jinja2.Environment(loader=jinja2.ChoiceLoader(loaders))
        env.globals.update(**self._theme_ctx)
        return env

    def _get_documents(self):
        """
        Iterates over files in the content directory except files/dirs
        starting with underscore or dot and converts files into document
        objects.
        """
        documents_paths = list(
            iterfiles(self.conf['paths.content'], '[!_.]*', True))

        # create document objects from raw files
        documents = []
        for index, document_path in enumerate(documents_paths):
            try:
                document = self.__class__.document_factory(document_path, self)
                documents.append(document)

            except Exception:
                logger.warning('skip %s: invalid file', document_path)

        return documents

    def run(self):
        """
        Starts build process.
        """
        mkdir(self.conf['paths.output'])
        documents = self._get_documents()

        # use generators to generate additional stuff
        for generator in self._generators:
            generator.generate(documents)

        # build all documents found
        for document in documents:
            document.build()

        self._copy_theme()

        print('Documents were built successfully')

    def _copy_theme(self):
        """
        Copy themes' static files to output directory. Each next copy
        overwrites the previous one, that's why we're going to copy
        base theme first.
        """
        out_static = os.path.join(self.conf['paths.output'], 'static')

        for theme in self._themes:
            static = os.path.join(theme, 'static')

            # not all themes are mandatory to distribute static
            if os.path.exists(static):
                copy_tree(static, out_static)
