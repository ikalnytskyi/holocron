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
import stevedore

from . import core


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
            with open(confpath, "r", encoding="utf-8") as f:
                # the conf may contain the {here} macro, so we have to
                # replace it with actual value.
                here = os.path.dirname(os.path.abspath(confpath))
                conf = yaml.safe_load(f.read().format(here=here))

    except (FileNotFoundError, PermissionError) as exc:
        # it's ok that a user doesn't have a settings file or doesn't have
        # permissions to read it, so just treat a warning and continue
        # execution.
        logger.warning("%s: %s", exc.filename, exc.strerror)
        logger.warning("Fallback to default settings")

    except (IsADirectoryError, ) as exc:
        # well, if we try to read settings from a directory, it's probably
        # a user have a wrong setup. we have no choice but treat error and
        # do not create application instance.
        logger.error("%s: %s", exc.filename, exc.strerror)
        return None

    except (yaml.YAMLError, ) as exc:
        # we have an ill-formed settings file, thus we can't apply users'
        # settings. in this case it's better show errors and do not create
        # application instance.
        logger.error("%s: %s", confpath, str(exc))
        return None

    metadata = conf.pop("metadata", None) if conf else None
    app = core.Application(metadata)

    for ext in stevedore.ExtensionManager(namespace="holocron.processors"):
        app.add_processor(ext.name, ext.plugin)

    if conf:
        for name, pipeline in conf.get("pipelines", {}).items():
            app.add_pipeline(name, pipeline)

    return app
