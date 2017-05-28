"""
    holocron.ext.feed
    ~~~~~~~~~~~~~~~~~

    This module implements a Feed generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import datetime
import textwrap

import jinja2
from dooku.conf import Conf

from holocron.ext import abc
from holocron.utils import normalize_url, mkdir
from holocron.content import Post


class Feed(abc.Extension, abc.Generator):
    """
    An Atom feed generator.

    This class is a generator extension that is designed to generate a site
    feed - content distribution technology - in the `Atom`_  format.
    See the :class:`~holocron.ext.Generator` class for interface details.

    The generator has several options::

        ext:
           feed:
              save_as: feed.xml
              posts_number: 5

    where

    * ``save_as`` is a path to output file relative to output directory
    * ``posts_number`` is a number of latest post to be shown in feed

    The class is actually both extension and generator in terms of Holocron
    at one time. It means that this class will be discovered by Holocron as
    extension, and this class register its instance as generator in the
    application.

    .. _Atom: http://www.ietf.org/rfc/rfc4287.txt

    :param app: an application instance for which we're creating extension
    """

    _template = jinja2.Template(textwrap.dedent('''\
        <?xml version="1.0" encoding="{{ encoding }}"?>
          <feed xmlns="http://www.w3.org/2005/Atom" >
            <title>{{ credentials.site.title }}</title>

            <updated>{{ credentials.date.isoformat() + "Z" }}</updated>
            <id>{{ credentials.siteurl_alt }}</id>

            <link href="{{ credentials.siteurl_self }}" rel="self" />
            <link href="{{ credentials.siteurl_alt }}" rel="alternate" />

            <generator>Holocron</generator>

            {% for doc in documents %}
            <entry>
              <title>{{ doc.title | default('Untitled') }}</title>
              <link href="{{ doc.abs_url }}" rel="alternate" />
              <id>{{ doc.abs_url }}</id>

              <published>{{ doc.published.isoformat() }}</published>
              <updated>{{ doc.updated_local.isoformat() }}</updated>

              <author>
                <name>{{ doc.author }}</name>
              </author>

              <content type="html">
                {{ doc.content | e }}
              </content>
            </entry>
            {% endfor %}
          </feed>'''))

    _default_conf = {
        'save_as': 'feed.xml',
        'posts_number': 5,
    }

    def __init__(self, app):
        self._appconf = app.conf
        self._conf = Conf(self._default_conf, app.conf.get('ext.feed', {}))
        self._url = normalize_url(app.conf['site.url']) + self._conf['save_as']

        app.add_generator(self)
        app.add_theme_ctx(feedurl=self._url)

    def generate(self, documents):
        posts_number = self._conf['posts_number']
        save_as = self._conf['save_as']

        # we are interested only in 'post' documents because 'pages'
        # usually are not a part of feed since they are not intended
        # to deliver content with regular updates
        posts = (doc for doc in documents if isinstance(doc, Post))

        # since we could have a lot of posts, it's a common practice to
        # use in feed only last N posts
        posts = sorted(posts, key=lambda d: d.published, reverse=True)
        posts = posts[:posts_number]

        credentials = {
            'siteurl_self': self._url,
            'siteurl_alt': normalize_url(self._appconf['site.url']),
            'site': self._appconf['site'],
            'date': datetime.datetime.utcnow().replace(microsecond=0), }

        save_as = os.path.join(self._appconf['paths.output'], save_as)
        mkdir(os.path.dirname(save_as))
        encoding = self._appconf['encoding.output']

        with open(save_as, 'w', encoding=encoding) as f:
            f.write(self._template.render(
                documents=posts,
                credentials=credentials,
                encoding=encoding))
