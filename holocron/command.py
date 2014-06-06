# coding: utf-8
"""
    holocron.command
    ~~~~~~~~~~~~~~~~

    This module contains a command manager class which implements
    dynamic loading of commands depending on the command name
    provided in command line interface.

    :copyright: (c) 2014, Andrii Gamaiunov
    :license: BSD, see LICENSE for details
"""

import stevedore


class CommandManager(object):
    """
    This class manages available commands.
    """

    def __init__(self):
        """
        Initialize the command list in order to have
        all available commands.
        """
        self._commands = []

        for command in stevedore.ExtensionManager(
            namespace='holocron.ext.commands',
            invoke_on_load=False,
        ):
            self._commands.append(command.name)

    def get_commands(self):
        """
        Returns the list of available python module names,
        which are meant to be implementations of commands for Holocron.

        :returns: a list of available commands
        """
        return self._commands

    def call(self, command_name, app):
        """
        Calls the execute method of a given command if such exists.
        """
        try:
            stevedore.DriverManager(
                namespace='holocron.ext.commands',
                name=command_name,
                invoke_on_load=True,
            ).driver.execute(app)

        except KeyError:
            app.logger.error(
                'execute() method not found in %s module',
                command_name
            )
