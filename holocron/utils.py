"""
    holocron.utils
    ~~~~~~~~~~~~~~

    This module contains various useful stuff.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os


def mkdir(path):
    """
    Creates a directory for a given `path` if not exists.

    :param path: a path to directory to create
    """
    if not os.path.exists(path):
        os.makedirs(path)
