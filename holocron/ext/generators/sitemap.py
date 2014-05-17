# coding: utf-8
"""
    holocron.ext.generators.sitemap
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The package implements a Sitemap generator.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
import os
import jinja2

from holocron.content import Convertible
from holocron.ext import Generator


class Sitemap(Generator):
    #: a sitemap template
    template = jinja2.Template('\n'.join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  {%- for doc in documents %}',
        '    <url>',
        '      <loc>{{ doc.url }}</loc>',
        '      <lastmod>{{ doc.modified.isoformat() }}</lastmod>',
        '    </url>',
        '  {% endfor -%}',
        '  </urlset>',
    ]))

    def generate(self, documents):
        # it make sense to keep only convertible documents in the sitemap
        documents = (
            doc for doc in documents if isinstance(doc, Convertible)
        )

        # write sitemap to the file
        sitemap_path = os.path.join(
            self.conf['paths']['output'], 'sitemap.xml')

        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(self.template.render(documents=documents))
