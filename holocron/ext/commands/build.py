# coding: utf-8
"""
    holocron.ext.commands.build
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a build command.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from holocron.ext import abc


class Build(abc.Command):
    """
    Generates a static site for a given Holocron instance.
    """

    def execute(self, app, arguments):
        app.run()
