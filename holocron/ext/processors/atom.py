"""Generate Atom feed."""

import os
import datetime
import textwrap

import jinja2
import pkg_resources

from ._misc import iterdocuments
from holocron import content


_template = jinja2.Template(textwrap.dedent('''\
    <?xml version="1.0" encoding="{{ encoding }}"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>{{ site.title }}</title>

      <updated>{{ date.isoformat() + "Z" }}</updated>
      <id>{{ siteurl_alt }}</id>

      <link href="{{ siteurl_self }}" rel="self" type="application/atom+xml" />
      <link href="{{ siteurl_alt }}" rel="alternate" type="text/html" />

      <generator uri="{{ app_uri }}" version="{{ app_version }}">
        Holocron
      </generator>

      {% for doc in documents %}
      <entry>
        <title>{{ doc.title | default('Untitled') }}</title>
        <link href="{{ doc.abs_url }}" rel="alternate" />
        <id>{{ doc.abs_url }}</id>

        <published>{{ doc.published.isoformat() }}</published>
        <updated>{{ doc.updated.isoformat() }}</updated>

        <author>
          <name>{{ doc.author }}</name>
        </author>

        <content type="html">
          {{ doc.content | e }}
        </content>
      </entry>
      {% endfor %}
    </feed>'''))


def process(app, documents, **options):
    when = options.pop('when', None)
    save_as = options.pop('save_as', 'atom.xml')
    posts_number = options.pop('posts_number', 5)
    encoding = options.pop('encoding', 'utf-8')

    selected = iterdocuments(documents, when)

    # In order to speed up feed fetching and decrease amount of traffic to
    # deliver its content the feed is usually limited to "N" latest posts
    # where "N" is passed as option.
    selected = sorted(selected, key=lambda d: d['published'], reverse=True)
    selected = selected[:posts_number]

    # These two lines will be gone once state mechanism is implemented to
    # share parameters between pipeline processors.
    url = os.path.join(app.conf['site.url'], save_as)
    app.add_theme_ctx(feedurl=url)

    # Produce a virtual document with Feed.
    feed = content.Document(app)
    feed['content'] = _template.render(
        documents=selected,
        siteurl_self=url,
        siteurl_alt=app.conf['site.url'],
        app_uri='https://holocron.readthedocs.io',
        app_version=pkg_resources.get_distribution('holocron').version,
        site=app.conf['site'],
        date=datetime.datetime.utcnow().replace(microsecond=0),
        encoding=encoding)
    feed['source'] = 'virtual://feed'
    feed['destination'] = save_as

    return documents + [feed]
