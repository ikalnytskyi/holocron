"""Generate Sitemap XML."""

import textwrap

import jinja2

from ._misc import iterdocuments
from holocron import content


_template = jinja2.Template(textwrap.dedent('''\
    <?xml version="1.0" encoding="{{ encoding }}"?>
     <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
     {%- for doc in documents %}
       <url>
         <loc>{{ doc.abs_url }}</loc>
         <lastmod>{{ doc.updated_local.isoformat() }}</lastmod>
       </url>
     {% endfor -%}
     </urlset>
'''))


def process(app, documents, **options):
    when = options.pop('when', None)
    encoding = options.pop('encoding', 'utf-8')

    selected = iterdocuments(documents, when)

    # Produce a virtual document with Feed.
    sitemap = content.Document(app)
    sitemap.content = _template.render(documents=selected, encoding=encoding)
    sitemap.source = 'virtual://sitemap'
    sitemap.destination = 'sitemap.xml'

    return documents + [sitemap]
