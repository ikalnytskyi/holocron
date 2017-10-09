"""
    holocron.ext.abc
    ~~~~~~~~~~~~~~~~

    Abstract Base Classes (ABC) for Holocron extensions. They are not
    mandatory for usage, but strongly recommended.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import abc


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
