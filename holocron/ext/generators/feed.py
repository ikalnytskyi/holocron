# coding: utf-8
"""
    holocron.ext.generators.feed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements a Feed generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import datetime
import textwrap

import jinja2

from holocron.ext import abc
from holocron.utils import normalize_url, mkdir
from holocron.content import Post


class Feed(abc.Generator):
    """
    This class is designed to generate a site feed - content distribution
    technology - in Atom format.

    The Atom specification: http://www.ietf.org/rfc/rfc4287.txt
    """

    #: an atom template
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
              <title>{{ doc.title }}</title>
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

    def generate(self, documents):
        posts = (doc for doc in documents if isinstance(doc, Post))
        posts = sorted(posts, key=lambda d: d.published, reverse=True)

        posts_number = self.app.conf['generators.feed.posts_number']
        save_as = self.app.conf['generators.feed.save_as']

        credentials = {
            'siteurl_self': normalize_url(self.app.conf['site.url']) + save_as,
            'siteurl_alt': normalize_url(self.app.conf['site.url']),
            'site': self.app.conf['site'],
            'date': datetime.datetime.utcnow().replace(microsecond=0), }

        save_as = os.path.join(self.app.conf['paths.output'], save_as)
        mkdir(os.path.dirname(save_as))
        encoding = self.app.conf['encoding.output']

        with open(save_as, 'w', encoding=encoding) as f:
            f.write(self._template.render(
                documents=posts[:posts_number],
                credentials=credentials,
                encoding=encoding))
