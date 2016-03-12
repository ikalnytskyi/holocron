"""
    holocron.ext.user_theme
    ~~~~~~~~~~~~~~~~~~~~~~~

    This module implements an extension that allows to consume some
    external theme and use it to render site content.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from dooku.conf import Conf

from holocron.ext import abc


class UserTheme(abc.Extension):
    """
    Setup external theme for content rendering.

    The extenstion supports only one option - ``path``::

        ext:
           user-theme:
              path: 'path/to/external/theme'

    .. versionadded:: 0.3.0

    :param app: an application instance for which we're creating extension
    """

    _default_conf = {
        'path': '_theme',
    }

    def __init__(self, app):
        conf = Conf(self._default_conf, app.conf.get('ext.user-theme', {}))
        app.add_theme(conf['path'])
