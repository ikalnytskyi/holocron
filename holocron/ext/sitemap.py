# coding: utf-8
"""
    holocron.ext.sitemap
    ~~~~~~~~~~~~~~~~~~~~

    This module implements a Sitemap generator.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import textwrap

import jinja2

from holocron.content import Page, Post
from holocron.ext import abc


class Sitemap(abc.Extension, abc.Generator):
    """
    A sitemap generator.

    This class is a generator extension that is designed to generate a site
    map - a list of public web pages accessible to crawlers or users.
    See the :class:`~holocron.ext.Generator` class for interface details.

    Sitemap can be represented in various formats, but this implementation
    uses the most popular one - XML-based representation - 'sitemap.xml'.
    The protocol details: http://www.sitemaps.org/protocol.html

    The class is actually both extension and generator in terms of Holocron
    at one time. It means that this class will be discovered by Holocron as
    extension, and this class register its instance as generator in the
    application.

    :param app: an application instance for which we're creating extension
    """

    #: An output filename is defined by the Sitemap protocol.
    _save_as = 'sitemap.xml'

    _template = jinja2.Template(textwrap.dedent('''\
        <?xml version="1.0" encoding="{{ encoding }}"?>
          <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

          {%- for doc in documents %}
            <url>
              <loc>{{ doc.abs_url }}</loc>
              <lastmod>{{ doc.updated_local.isoformat() }}</lastmod>
            </url>
          {% endfor -%}

          </urlset>'''))

    def __init__(self, app):
        self._encoding = app.conf['encoding.output']
        self._save_as = os.path.join(app.conf['paths.output'], self._save_as)

        app.add_generator(self)

    def generate(self, documents):
        # we are interested only in web pages, so let's filter by post
        # and pages
        documents = (
            doc for doc in documents if isinstance(doc, (Page, Post)))

        with open(self._save_as, 'w', encoding=self._encoding) as f:
            f.write(self._template.render(
                documents=documents,
                encoding=self._encoding))
