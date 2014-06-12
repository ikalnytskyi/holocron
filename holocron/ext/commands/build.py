# coding: utf-8
"""
    holocron.ext.commands.build
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a build command.

    :copyright: (c) 2014, Andrii Gamaiunov
    :license: BSD, see LICENSE for details
"""

from holocron.ext import Command


class Build(Command):
    """
    Build class implements the build command.
    It is responsibe for running the application instance.
    """

    def execute(self, app):
        app.run()
