# coding: utf-8
"""
    holocron.ext.commands.init
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements an init command.

    :copyright: (c) 2014, Andrii Gamaiunov
    :license: BSD, see LICENSE for details
"""
import os
import logging

from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError

from holocron import app
from holocron.ext import Command


logger = logging.getLogger(__name__)


class Init(Command):
    """
    Init is command class responsible for creation of a blog skeleton.

    Init command is an entry point for the user's workflow. It initializes
    current folder with a basic _config.yml file and creates an example post.
    """
    default_content = os.path.join(os.path.dirname(app.__file__), 'example/')

    def execute(self, app):
        # if holocron content exists, copy it to current directory
        try:
            copied_files = copy_tree(self.default_content, os.curdir)
            for file_ in copied_files:
                print('File {file} created.'.format(file=file_))
        except DistutilsFileError:
            logger.error('Holocron example content was not found.')
