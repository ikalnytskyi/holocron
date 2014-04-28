# coding: utf-8
"""
    holocron.utils
    ~~~~~~~~~~~~~~

    This module contains various useful stuff.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
import os
import copy
import itertools
from fnmatch import fnmatch


class cached_property(object):
    """
    Decorator that converts a function into a lazy property.

    The function wrapped is called the first time to retrieve the result and
    then that calculated result is used the next time you access the value::

        class Holocron:
            @cached_property
            def jinja_env(self):
                # create and configure jinja environment
                return jinja_env


    .. admonition:: Implementation details

        The property is implemented as non-data descriptor. That's mean, the
        descriptor is invoked if there's no entry with the same name in the
        instance's ``__dict__``.

        This trick helps us to get rid of the function call overhead.
    """
    def __init__(self, func):
        self.func = func

        self.__name__ = func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        if self.__name__ not in obj.__dict__:
            obj.__dict__[self.__name__] = self.func(obj)
        return obj.__dict__[self.__name__]


def merge_dict(a, b, *args):
    """
    Takes at lest two dictionaries and recursively merge it.

    An internal helper function is needed to prevent calling ``copy.deepcopy``
    each recursive call. I haven't tested, but it should reduce memory usage.
    """
    def _merge(a, *args):
        for key, value in itertools.chain(*[x.items() for x in args]):
            if key in a and isinstance(value, dict):
                value = _merge(a[key], value)
            a[key] = value
        return a

    return _merge(copy.deepcopy(a), b, *args)


def iterfiles(path, pattern=None, exclude_folders=False):
    """Iterate over all files in the ``path`` directory which satisfy
    a given ``pattern``.

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
    """A little wrapper for `os.makedirs` function. Create directory only
    if the desired path is not exists.
    """
    if not os.path.exists(path):
        os.makedirs(path)


def fix_siteurl(siteurl):
    """
        Fix siteurl format and returns the result. This function ensures that
        siteurl starts with `http://`.

        :param siteurl: a siteurl to be fixed
    """
    if not siteurl.startswith(('http://', 'https://',)):
        siteurl = 'http://' + siteurl
    return siteurl
