"""Factory functions to create core instances."""

import stevedore

from . import Application


def create_app(metadata, processors=None, pipes=None):
    """Return an application instance with processors & pipes setup."""

    instance = Application(metadata)

    for ext in stevedore.ExtensionManager(namespace="holocron.processors"):
        instance.add_processor(ext.name, ext.plugin)

    for ext in stevedore.ExtensionManager(namespace="holocron.pipes"):
        instance.add_pipe(ext.name, ext.plugin)

    for name, processor in (processors or {}).items():
        instance.add_processor(name, processor)

    for name, pipeline in (pipes or {}).items():
        instance.add_pipe(name, pipeline)

    return instance
