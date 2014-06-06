# coding: utf-8
"""
    holocron.ext.generators.feed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The package implements a Feed generator.

    :copyright: (c) 2014, Andrii Gamaiunov
    :license: BSD, see LICENSE for details
"""

import os
import jinja2
import datetime

from holocron.ext import Generator
from holocron.content import Convertible
from holocron.utils import fix_siteurl, mkdir


class Feed(Generator):
    """
    A feed extension.

    The class is a generator extension for Holocron that is designed to
    generate a site feed - content distribution technology - in Atom format.

    The Atom specification: http://www.ietf.org/rfc/rfc4287.txt

    See the :class:`~holocron.ext.Generator` class for interface details.
    """
    #: an atom template
    template = jinja2.Template('\n'.join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '  <feed xmlns="http://www.w3.org/2005/Atom" >',
        '    <title>{{ credentials.sitename }} Feed</title>',
        '    <updated>{{ credentials.date.isoformat() + "Z" }}</updated>',
        '    <id>{{ credentials.siteurl_alt }}</id>',
        '    ',
        '    <link href="{{ credentials.siteurl_self }}" rel="self" />',
        '    <link href="{{ credentials.siteurl_alt }}" rel="alternate" />',
        '    ',
        '    <generator>Holocron</generator>',

        '    {% for doc in documents %}',
        '    <entry>',
        '      <title>{{ doc.meta["title"] }}</title>',
        '      <link href="{{ doc.abs_url }}" rel="alternate" />',
        '      <id>{{ doc.abs_url }}</id>',

        '      <published>{{',
        '        doc.get_created_datetime(localtime=True).isoformat()',
        '      }}</published>',
        '      <updated>{{',
        '        doc.get_modified_datetime(localtime=True).isoformat()',
        '      }}</updated>',

        '      <author>',
        '        <name>{{ doc.meta["author"] }}</name>',
        '      </author>',

        '      <content type="html">',
        '        {{ doc.html | e }}',
        '      </content>',
        '    </entry>',
        '    {% endfor %}',
        '  </feed>',
    ]))

    def generate(self, documents):
        save_as = self.conf['generators.feed.save_as']
        posts_number = self.conf['generators.feed.posts_number']
        output_path = self.conf['paths.output']

        documents = (doc for doc in documents if isinstance(doc, Convertible))
        documents = sorted(
            documents, key=lambda d: d.get_created_datetime(), reverse=True)
        documents = documents[:posts_number]

        save_to_path = os.path.join(output_path, save_as)
        path = os.path.split(save_to_path)[0]

        if path:
            mkdir(path)

        credentials = {
            'siteurl_self': fix_siteurl(self.conf['siteurl']) + save_as,
            'siteurl_alt': fix_siteurl(self.conf['siteurl']),
            'sitename': self.conf['sitename'],
            'date': datetime.datetime.utcnow().replace(microsecond=0)
        }

        with open(save_to_path, 'w', encoding='utf-8') as f:
            f.write(self.template.render(
                documents=documents,
                credentials=credentials
            ))
