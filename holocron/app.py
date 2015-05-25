# coding: utf-8
"""
    holocron.app
    ~~~~~~~~~~~~

    This module implements the central Holocron application class.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import shutil
import logging

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
                conf = yaml.load(f.read().format(here=here))

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
            'title': "Kenobi's Thought",
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
            'theme': '_theme',
        },

        'theme': {},

        'ext': {
            'enabled': ['markdown', 'feed', 'index', 'sitemap', 'tags'],
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
        #: Keeps all registered extensions and is used for preventing them
        #: to be handled by garbage collector. Also I believe it might be
        #: useful for extension developers in future.
        self._extensions = {}

        #: file extension -> converter instance
        #:
        #: Keeps all registered converters and is used for retrieving
        #: converters for specific file types (by its extension).
        self._converters = {}

        #: generator instance, ...
        #:
        #: Keeps all registered generators and is used for executing them.
        self._generators = []

        #: Discover and execute all found extensions.
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
        """
        overwritten = set(kwargs.keys()) & set(self.jinja_env.globals.keys())
        if overwritten:
            logger.warning(
                'the following theme context is going to be overwritten: %s',
                ', '.join(overwritten))

        self.jinja_env.globals.update(**kwargs)

    @cached_property
    def jinja_env(self):
        """
        Gets a Jinja2 environment based on Holocron's settings.
        Calculates only once, since it's a cached property.
        """
        # makes a default template loader
        templates_path = os.path.join('theme', 'templates')
        loader = jinja2.PackageLoader('holocron', templates_path)

        # PrefixLoader provides a direct access to the default templates
        loaders = [loader, jinja2.PrefixLoader({'!default': loader})]

        # makes a user template loader
        path = self.conf.get('paths.theme')
        if path is not None:
            path = os.path.join(path, 'templates')
            loaders.insert(0, jinja2.FileSystemLoader(path))

        env = jinja2.Environment(loader=jinja2.ChoiceLoader(loaders))
        env.globals.update(
            # pass some useful conf options to the template engine
            site=self.conf['site'],
            theme=self.conf['theme'],
            encoding=self.conf['encoding.output'])
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
        Copy theme's static files to the output folder. If the user's statics
        aren't exists then base statics will be copied.
        """
        root = os.path.dirname(__file__)

        base_static = os.path.join(root, 'theme', 'static')
        user_static = os.path.join(self.conf['paths.theme'], 'static')

        if not os.path.exists(user_static):
            user_static = base_static
        out_static = os.path.join(self.conf['paths.output'], 'static')

        shutil.rmtree(out_static, ignore_errors=True)
        shutil.copytree(user_static, out_static)
