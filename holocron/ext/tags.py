# coding: utf-8
"""
    holocron.ext.tags
    ~~~~~~~~~~~~~~~~~

    The module implements a Tags generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import logging
from collections import defaultdict

from dooku.conf import Conf

from holocron.ext import abc
from holocron.content import Post
from holocron.utils import mkdir


logger = logging.getLogger(__name__)


class Tag(object):
    """
    Simple wrapper to provide useful methods for manipulating with tag.
    """
    def __init__(self, name, output):
        self.name = name
        self.url = '/{0}/'.format(
            output.format(tag=name).lstrip('/').rstrip('/'))


class Tags(abc.Extension, abc.Generator):
    """
    A tags generator.

    This class is a generator extension that is designed to generate special
    web pages - one page per tag - which list posts marked by some tag.
    See the :class:`~holocron.ext.Generator` class for interface details.

    The generator has several options::

        ext:
           tags:
              template: document-list.html
              output: tags/{tag}

    where

    * ``templates`` is a template name to be used for rendering tags page
    * ``output`` is an output path for tags page

    The class is actually both extension and generator in terms of Holocron
    at one time. It means that this class will be discovered by Holocron as
    extension, and this class register its instance as generator in the
    application.

    :param app: an application instance for which we're creating extension
    """

    _default_conf = {
        'template': 'document-list.html',
        'output': 'tags/{tag}',
    }

    def __init__(self, app):
        self._app = app
        self._conf = Conf(self._default_conf, app.conf.get('ext.tags', {}))
        self._encoding = app.conf['encoding.output']
        self._save_as = os.path.join(
            app.conf['paths.output'], self._conf['output'], 'index.html')

        app.add_generator(self)
        app.add_theme_ctx(show_tags=True)

    def generate(self, documents):
        # we are interested only in 'post' documents because 'pages'
        # usually are not marked with tags
        posts = (doc for doc in documents if isinstance(doc, Post))

        # map: tag -> [posts]
        tags = defaultdict(list)

        for post in posts:
            if hasattr(post, 'tags'):

                if not isinstance(post.tags, (list, tuple)):
                    logger.warning(
                        'Tags must be wrapped with list or tuple in %s',
                        post.short_source)
                    continue

                tag_objects = []
                for tag in post.tags:
                    tags[tag].append(post)
                    tag_objects.append(Tag(tag, self._conf['output']))

                post.tags = tag_objects

        template = self._app.jinja_env.get_template(self._conf['template'])

        for tag in tags:
            save_as = self._save_as.format(tag=tag)
            mkdir(os.path.dirname(save_as))

            with open(save_as, 'w', encoding=self._encoding) as f:
                f.write(template.render(posts=tags[tag]))
