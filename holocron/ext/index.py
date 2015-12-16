# coding: utf-8
"""
    holocron.ext.index
    ~~~~~~~~~~~~~~~~~~

    This module implements an Index generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os

from dooku.conf import Conf

from holocron.ext import abc
from holocron.content import Post


class Index(abc.Extension, abc.Generator):
    """
    An index page generator.

    This class is a generator extension that is designed to generate an
    index page of the web site - the page that lists all posts of a blog.
    The index page is stored stored in the root of the output folder.
    See the :class:`~holocron.ext.Generator` class for interface details.

    The generator has just one option::

        ext:
           index:
              template: document-list.html

    where

    * ``templates`` is a template name to be used for rendering index page

    The class is actually both extension and generator in terms of Holocron
    at one time. It means that this class will be discovered by Holocron as
    extension, and this class register its instance as generator in the
    application.

    :param app: an application instance for which we're creating extension
    """

    _default_conf = {
        'template': 'document-list.html',
    }

    def __init__(self, app):
        self._app = app
        self._conf = Conf(self._default_conf, app.conf.get('ext.index', {}))
        self._encoding = app.conf['encoding.output']

        # An output filename. Why this? Because we want to see this page
        # by typing site url in a browser and http servers are usually
        # looking for this file if none was specified.
        self._save_as = os.path.join(app.conf['paths.output'], 'index.html')

        app.add_generator(self)

    def generate(self, documents):
        # we are interested only in posts, because pages usually are
        # shown in a some sort of navigation bar
        posts = (doc for doc in documents if isinstance(doc, Post))

        template = self._app.jinja_env.get_template(self._conf['template'])
        with open(self._save_as, 'w', encoding=self._encoding) as f:
            f.write(template.render(posts=posts))
