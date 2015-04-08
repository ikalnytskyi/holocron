# coding: utf-8
"""
    holocron.ext.generators.tags
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The package implements a Tags generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
from collections import defaultdict

from holocron.ext import abc
from holocron.content import Post
from holocron.utils import mkdir


class Tag(object):
    """
    Simple wrapper to provide useful methods for manipulating with tag.
    """
    def __init__(self, tags_dir, tag):
        self.name = tag
        self.url = '/{path}/'.format(path=os.path.join(tags_dir, self.name))


class Tags(abc.Generator):
    """
    This class generates tag pages.
    """

    #: default template for tags pages
    _template_name = 'document-list.html'

    #: default filename for html output file
    _save_as = 'index.html'

    def generate(self, documents):
        posts = (doc for doc in documents if isinstance(doc, Post))

        #: output path directory for tags directory
        output_path = self.app.conf['paths.output']
        tags_dir = self.app.conf['generators.tags.output']

        #: load template for rendering tag pages
        template = self.app.jinja_env.get_template(self._template_name)

        #: create a dictionnary of tags to corresponding posts
        tags = defaultdict(list)

        for post in posts:

            if hasattr(post, 'tags'):
                tag_objects = []
                for tag in post.tags:
                    tag = Tag(tags_dir, tag)
                    tags[tag.name].append(post)
                    tag_objects.append(tag)

                post.tags = tag_objects

        for tag in tags:
            path = os.path.join(output_path, tags_dir, tag)
            mkdir(path)

            save_as = os.path.join(path, self._save_as)
            encoding = self.app.conf['encoding.output']

            with open(save_as, 'w', encoding=encoding) as f:
                f.write(template.render(posts=tags[tag]))
