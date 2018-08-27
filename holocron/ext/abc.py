"""
    holocron.ext.abc
    ~~~~~~~~~~~~~~~~

    Abstract Base Classes (ABC) for Holocron extensions. They are not
    mandatory for usage, but strongly recommended.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import abc


class Extension(object, metaclass=abc.ABCMeta):
    """
    Abstract base class for Holocron extensions.

    Holocron uses entry points based approach for extensions discovering.
    Thus, entry points that are exported to ``holocron.ext`` namespace
    will be considered as extensions, and Holocron will call them and pass
    its instance as argument. Further, it will be up to extension to decide
    what to do (it can register a converter, generator, etc).

    .. versionadded:: 0.2.0

    :param app: an application instance
    """

    @abc.abstractmethod
    def __init__(self, app):
        """Initialize extension."""


class Command(object, metaclass=abc.ABCMeta):
    """
    Abstract base class for 'Command' extensions.

    Commands are used to interact with Holocron application instance.
    They could be used to build application (generate html blog entries),
    serve the application at a local webserver or online, etc.

    Example::

        from holocron.ext import abc

        class MyCoolCommand(abc.Command):
            def execute(self, app):
                # perform some actions

    TODO: revise the docstring
    """

    def set_arguments(self, parser):
        """
        Declare additional command line arguments for the command. By default,
        there are no arguments. Each command has to overwite this method in
        order to add new arguments.

        :param parser: an :class:`argparse.ArgumentParser` for the command
        """

    @abc.abstractmethod
    def execute(self, app, arguments):
        """
        Execute is a uniform method used to execute commands.

        :param app: an application instance
        :param arguments: a Namespace object with parsed command line arguments
        """
