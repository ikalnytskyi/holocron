"""
    holocron.app
    ~~~~~~~~~~~~

    This module implements the central Holocron application class.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import logging
import collections

import yaml

from dooku.conf import Conf
from dooku.ext import ExtensionManager

from .processors import _misc


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

    metadata = conf.pop('metadata', None) if conf else None
    app = Holocron(conf, metadata)

    for name, ext in ExtensionManager(namespace='holocron.processors'):
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

    def __init__(self, conf=None, metadata=None):
        #: The configuration dictionary.
        self.conf = Conf(self.default_conf, conf or {})

        #: metadata store
        #:
        #: The metadata dictionary is a kv store shared across processors of a
        #: pipeline, and that is designed to contain application level (i.e.
        #: site level) data. A chain map is used in order to is to separate
        #: initial metadata from possible overwrites.
        #:
        #: .. versionadded:: 0.4.0
        self.metadata = collections.ChainMap({}, metadata or {})

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

    def invoke_processors(self, documents, pipeline):
        stream = documents

        for processor in pipeline:
            processor = processor.copy()
            processfn = self._processors[processor.pop('name')]

            # Resolve every JSON reference we encounter in a processor's
            # parameters. Please note, we're doing this so late because we
            # want to take into account metadata and other changes produced
            # by previous processors in the pipeline.
            processor = _misc.resolve_json_references(
                processor, {'metadata:': self.metadata})

            stream = processfn(self, stream, **processor)

        yield from stream

    def run(self):
        """
        (DEPRECATED) Starts build process.
        """
        processors = self.conf['pipelines.build']

        # Since processors are generators and thus are lazy evaluated, we need
        # to force evaluate them. Otherwise, the pipeline will produce nothing.
        for _ in self.invoke_processors([], processors):
            pass
