# coding: utf-8
"""
    holocron.utils
    ~~~~~~~~~~~~~~

    This module contains various useful stuff.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
import os
from fnmatch import fnmatch


def iterfiles(path, pattern=None, exclude_folders=False):
    """
    Iterate over all files in the `path` dir which satisfy a given `pattern`.

    :param path: a path to find in
    :param pattern: a pattern which all the files should satisfy
    :param exclude_folders: exclude folders from the search if it isn't
                            satisfy a pattern
    """
    for root, dirnames, filenames in os.walk(path, topdown=True):
        # skip not satisfied directories
        if exclude_folders and pattern is not None:
            dirnames[:] = [d for d in dirnames if fnmatch(d, pattern)]

        # yield satisfied files
        for filename in filenames:
            if pattern is not None and not fnmatch(filename, pattern):
                continue

            yield os.path.join(root, filename)


def mkdir(path):
    """
    Creates a directory for a given `path` if not exists.

    :param path: a path to directory to create
    """
    if not os.path.exists(path):
        os.makedirs(path)


def normalize_url(url, trailing_slash=True):
    """
    Ensures that url is in normal form and transforms to it if not.

    :param url: a url to normalize
    :param trailing_slash: add trailing slash if True; remove it if False
                           and keep unchanged if 'keep'
    :returns: a normalized url
    """
    assert trailing_slash in (True, False, 'keep')

    # ensures that url is started with an http prefix
    if not url.startswith(('http://', 'https://', )):
        url = '{prefix}{url}'.format(prefix='http://', url=url)

    # an additional logic for adding trailing slash or not
    if not url.endswith('/') and trailing_slash is True:
        url = '{url}/'.format(url=url)
    elif url.endswith('/') and trailing_slash is False:
        url = url[:-1]

    return url
