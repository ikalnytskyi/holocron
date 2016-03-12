"""
    holocron.ext.commands.init
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements an init command.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import logging
import textwrap

from distutils.dir_util import copy_tree

import holocron
from holocron.ext import abc


logger = logging.getLogger(__name__)


class Init(abc.Command):
    """
    Creates a blog skeleton in the current working directory.
    """

    _content = os.path.join(os.path.dirname(holocron.__file__), 'example')

    def execute(self, app, arguments):
        if os.listdir(os.curdir):
            return logger.error('Could not initialize non-empty directory.')

        copy_tree(self._content, os.curdir)

        print(textwrap.dedent('''
            The current working directory has been initialized with a blog
            template. Here are some commands you might be interested in:

               $ holocron build     # compile blog into static html
               $ holocron serve     # preview blog in your browser

            Look into the documentation https://holocron.readthedocs.org
            for details.

            May the Force be with you!
        '''))
