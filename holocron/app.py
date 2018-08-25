"""
    holocron.app
    ~~~~~~~~~~~~

    This module implements the central Holocron application class.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import logging

import yaml
import jinja2

from dooku.conf import Conf
from dooku.decorator import cached_property
from dooku.ext import ExtensionManager

from .ext.processors import source


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

    app = Holocron(conf)

    for name, ext in ExtensionManager(namespace='holocron.ext.processors'):
        app.add_processor(name, ext)

    return app


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

    #: Default settings.
    default_conf = {
        'site': {
            'title': "Kenobi's Thoughts",
            'author': 'Obi-Wan Kenobi',
            'url': 'http://obi-wan.jedi',
        },

        'paths': {
            'content': '.',
            'output': '_build',
        },

        'theme': {},

        'pipelines': {},

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

        #: processor name -> processor function
        #:
        #: Processors are stateless functions that receive a list of documents
        #: and return a list of documents. Each output of one processor goes
        #: as input to next one. This property is intended to keep track of
        #: known processors, the one that could be used by application
        #: instance.
        #:
        #: .. versionadded:: 0.4.0
        self._processors = {}

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
        }

        # discover and execute all found extensions
        for name, ext in ExtensionManager(
            namespace='holocron.ext',
            names=self.conf.get('ext.enabled', []),
        ):
            if name in self._extensions:
                logger.warning(
                    '%s extension skipped: already registered', name)
                continue
            self._extensions[name] = ext(self)

    def add_processor(self, name, processor):
        """Register a given processor in the application instance.

        Application instance comes with no registered processors by default.
        The usual place where they are registered is create_app function.

        :param name: a name to be used to call the processor
        :param processor: a process function to be registered
        """
        if name in self._processors:
            logger.warning('%s processor skipped: already registered', name)
            return

        self._processors[name] = processor

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

    def invoke_processors(self, documents, pipeline):
        for processor in pipeline:
            processor = processor.copy()
            processfn = self._processors[processor.pop('name')]
            documents = processfn(self, documents, **processor)
        return documents

    def run(self):
        """
        (DEPRECATED) Starts build process.
        """
        documents = []

        # These lines are temporal measure until jinja2 processor is
        # implemented. The idea here is to inject theme static files,
        # like stylesheet, javascript or images into processor pipeline
        # so they will be persisted on the filesystem.
        for theme in self._themes:
            documents = source.process(self, documents, path=theme, when=[{
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^static/',
            }])

        processors = self.conf['pipelines.build']
        documents = self.invoke_processors(documents, processors)

        print('Documents were built successfully')
