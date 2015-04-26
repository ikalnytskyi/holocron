# coding: utf-8
"""
    holocron.ext.commands.build
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a build command.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import shutil

from holocron.ext import abc


class Build(abc.Command):
    """
    Generates a static site for a given Holocron instance.
    """

    def set_arguments(self, parser):
        """
        :param parser: an :class:`argparse.ArgumentParser` for the command
        """
        parser.add_argument(
            '--clear', action='store_true',
            help='clear output folder before building')

    def execute(self, app, arguments):
        """
        :param app: a :class:`holocron.app.Holocron` instance
        :param arguments: an object with parsed command line arguments
        """
        # remove output folder if --clear was passed
        if arguments.clear:
            shutil.rmtree(app.conf['paths.output'], ignore_errors=True)

        # From API point of view, all we have to do is just to run
        # Holocron's .run() method. So the command is nothing more
        # than a CLI handler for calling it.
        app.run()
