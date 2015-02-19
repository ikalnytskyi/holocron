# coding: utf-8
"""
    holocron.ext.commands.init
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements an init command.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import logging

from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError

import holocron
from holocron.ext import abc


logger = logging.getLogger(__name__)


class Init(abc.Command):
    """
    Creates a blog skeleton in the current working directory.
    """

    #: path to an example content
    content = os.path.join(os.path.dirname(holocron.__file__), 'example')

    def execute(self, app):
        if os.listdir(os.curdir) != []:
            logger.error('Init command cannot run in a non-empty directory.')
            return

        try:
            copied_files = copy_tree(self.content, os.curdir)
            for file_ in copied_files:
                logger.info('%s: created', file_)

        except DistutilsFileError:
            logger.error('Holocron example content was not found.')
