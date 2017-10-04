"""
    holocron.ext
    ~~~~~~~~~~~~

    The package provides a namespace for extensions. It contains both
    abstract base classes and built-in implementations.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from .tags import Tags

from .user_theme import UserTheme


__all__ = [
    'Tags',

    'UserTheme',
]
