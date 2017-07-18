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
