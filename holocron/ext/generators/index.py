# coding: utf-8
"""
    holocron.ext.generators.index
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements an Index generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os

from holocron.ext import abc
from holocron.content import Post


class Index(abc.Generator):
    """
    Generates an index page - page which lists all posts in a blog. This page
    will be stored in the root of the output folder.
    """

    #: a template name to be used for rendering index page
    _template_name = 'document-list.html'

    #: a filename to be used for html output file
    _save_as = 'index.html'

    def generate(self, documents):
        posts = (doc for doc in documents if isinstance(doc, Post))

        #: output path for index page
        save_as = os.path.join(self.app.conf['paths.output'], self._save_as)
        encoding = self.app.conf['encoding.output']

        #: load template for rendering index page
        _template = self.app.jinja_env.get_template(self._template_name)

        with open(save_as, 'w', encoding=encoding) as f:
            f.write(_template.render(posts=posts))
