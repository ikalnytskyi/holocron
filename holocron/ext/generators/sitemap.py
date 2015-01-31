# coding: utf-8
"""
    holocron.ext.generators.sitemap
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements a Sitemap generator.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import jinja2

from holocron.content import Page, Post
from holocron.ext import abc


class Sitemap(abc.Generator):
    """
    A sitemap extension.

    The class is a generator extension for Holocron that is designed to
    generate a site map - a list of pages of a web site accessible to
    crawlers or users.

    Sitemaps can be represented in various formats, but this implementation
    uses the most popular one - XML-based representation - 'sitemap.xml'.

    The protocol details: http://www.sitemaps.org/protocol.html

    See the :class:`~holocron.ext.Generator` class for interface details.
    """
    #: an output filename
    save_as = 'sitemap.xml'

    #: a sitemap template
    template = jinja2.Template('\n'.join([
        '<?xml version="1.0" encoding="{{ encoding }}"?>',
        '  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  {%- for doc in documents %}',
        '    <url>',
        '      <loc>{{ doc.abs_url }}</loc>',
        '      <lastmod>{{ doc.updated_local.isoformat() }}</lastmod>',
        '    </url>',
        '  {% endfor -%}',
        '  </urlset>', ]))

    def generate(self, documents):
        # it make sense to keep only convertible documents in the sitemap
        documents = (
            doc for doc in documents if isinstance(doc, (Page, Post)))

        # write sitemap to the file
        save_as = os.path.join(self.app.conf['paths.output'], self.save_as)
        encoding = self.app.conf['encoding.output']

        with open(save_as, 'w', encoding=encoding) as f:
            f.write(
                self.template.render(documents=documents, encoding=encoding))
