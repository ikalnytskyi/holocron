"""Generate Sitemap XML."""

import textwrap

import jinja2

from ._misc import iterdocuments
from holocron import content


_template = jinja2.Template(textwrap.dedent('''\
    <?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {%- for doc in documents %}
      <url>
        <loc>{{ doc.abs_url | e }}</loc>
        <lastmod>{{ doc.updated_local.isoformat() | e }}</lastmod>
      </url>
    {% endfor -%}
    </urlset>
'''))


def process(app, documents, **options):
    save_as = options.pop('save_as', 'sitemap.xml')
    when = options.pop('when', None)

    selected = iterdocuments(documents, when)

    sitemap = content.Document(app)
    sitemap['source'] = 'virtual://sitemap'
    sitemap['destination'] = save_as

    # According to the Sitemap protocol, the output encoding must be UTF-8.
    # Since this processor does not perform any I/O, the only thing we can
    # do here is to provide bytes representing UTF-8 encoded XML.
    sitemap['content'] = _template.render(documents=selected).encode('UTF-8')

    return documents + [sitemap]
