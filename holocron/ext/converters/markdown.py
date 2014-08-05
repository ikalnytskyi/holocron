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
    """
    A markdown converters.

    This class is a converter extension that is designed to convert some
    input markdown text into HTML, extracting some useful meta information.
    See the :class:`~holocron.ext.Converter` class for interface details.

    The converter uses `this markdown implementation`_, so it supports some
    extension that extends markdown language. For activating markdown
    extension, please specify its name in the following option::

        converters.markdown.extensions

    The converter has a contract-based design, so we should always pass
    the settings even if they are default.

    .. _this markdown implementation: http://pythonhosted.org/Markdown/
    """

    #: a list of supported files
    extensions = ['.md', '.mkd', '.mdown', '.markdown']

    def __init__(self, *args, **kwargs):
        super(Markdown, self).__init__(*args, **kwargs)

        #: create markdown instance with enabled extensions
        self._markdown = markdown.Markdown(
            extensions=self.conf['markdown.extensions'])

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
        meta = {}

        # extract title
        match = self._re_title.match(html)
        if match:
            meta['title'], html = match.groups()

        return meta, html.lstrip()
