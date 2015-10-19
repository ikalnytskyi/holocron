# coding: utf-8
"""
    holocron.ext.converters.markdown
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a Markdown converter.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import re
import markdown

from dooku.conf import Conf

from holocron.ext import abc


class Markdown(abc.Converter):
    """
    A markdown converter.

    This class is a converter extension that is designed to convert some
    input markdown text into HTML, extracting some useful meta information.
    See the :class:`~holocron.ext.Converter` class for interface details.

    The converter uses `this markdown implementation`_, so it supports some
    extensions that extends markdown language. To activate them please
    specify their names in the following option::

        ext:
           markdown:
              extensions: [ ... ]

    The class is actually both extension and converter in terms of Holocron
    at one time. It means that this class will be discovered by Holocron as
    extension, and this class register its instance as converter in the
    application.

    .. _this markdown implementation: http://pythonhosted.org/Markdown/

    :param app: an application instance for which we're creating extension
    """

    extensions = ['.md', '.mkd', '.mdown', '.markdown']

    _default_conf = {
        'extensions': [
            'codehilite',   # use pygments to highlight code-blocks
            'extra',        # enable extended features like tables
        ],
    }

    def __init__(self, app):
        self._conf = Conf(self._default_conf, app.conf.get('ext.markdown', {}))
        self._markdown = markdown.Markdown(extensions=self._conf['extensions'])
        self._re_title = re.compile('<h1>(.*?)</h1>(.*)', re.M | re.S)

        app.add_converter(self)

    def to_html(self, text):
        html = self._markdown.convert(text)
        return self._extract_meta(html)

    def _extract_meta(self, html):
        """
        Extracts some meta information from a given HTML.

        We need to cut document's title from the HTML, because we want to
        use it in different places and show it in own way. Please note that
        the method *cut* the title, and there will be no title in the HTML
        anymore.

        :param html: extracts information from the HTML
        :returns: a tuple of (meta, html)
        """
        meta = {}

        # extract title
        match = self._re_title.match(html)
        if match:
            meta['title'], html = match.groups()

        return meta, html.strip()
