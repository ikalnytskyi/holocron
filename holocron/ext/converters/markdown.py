# coding: utf-8
"""
    holocron.ext.converters.markdown
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The package implements a Markdown converter.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
import re
import markdown

from holocron.ext import Converter


class Markdown(Converter):
    extensions = ['.md', '.mkd', '.mdown', '.markdown']

    def __init__(self, *args, **kwargs):
        super(Markdown, self).__init__(*args, **kwargs)

        #: create markdown instance with enabled extensions
        self._markdown = markdown.Markdown(
            self.conf['markdown']['extensions']
        )

        #: compile regex for extracting post title
        self._re_title = re.compile('<h1>(.*)</h1>(.*)', re.M | re.S)

    def to_html(self, text):
        html = self._markdown.convert(text)
        return self._extract_meta(html)

    def _extract_meta(self, html):
        """
        Extracts some meta information from a given HTML.

        It's important to note, that the method not only extracts a meta
        information, but also modify an input HTML. For example, we need
        to extract a post title (cut title between <h1>) and remove it
        from an HTML, since the tittle will be used latter for printing
        post title in templates.

        :param html: extracts information from this HTML
        :returns: a tuple of `(meta, html)`
        """
        title, html = self._re_title.match(html).groups()
        return {'title': title, }, html
