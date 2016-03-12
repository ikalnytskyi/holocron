# coding: utf-8
"""
    holocron.ext.restructuredtext
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a reStructuredText converter.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from docutils.core import publish_parts
from docutils.writers import html4css1
from docutils import nodes

from dooku.conf import Conf

from holocron.ext import abc


class ReStructuredText(abc.Extension, abc.Converter):
    """
    A reStructuredText converter.

    This class is a converter extension that is designed to convert some
    input reStructuredText into HTML, extracting some useful meta information.
    See the :class:`~holocron.ext.Converter` class for interface details.

    docutils_ is used to convert reStructuredText markup to HTML, and
    if you know it deep enough (it's hard) you can pass custom settings
    using the following option::

        ext:
           restructuredtext:
              docutils: { ... }

    The class is actually both extension and converter in terms of Holocron
    at one time. It means that this class will be discovered by Holocron as
    extension, and this class registers its instance as a converter in the
    application.

    .. _docutils: http://docutils.sourceforge.net

    :param app: an application instance for which we're creating extension
    """

    extensions = ['.rst', '.rest']

    _default_conf = {
        'docutils': {
            'initial_header_level': 2,      # start sections from <h2>
            'embed_stylesheet': False,      # do not generate css
            'syntax_highlight': 'short',    # short css classes for code blocks
        },
    }

    def __init__(self, app):
        self._conf = Conf(
            self._default_conf,
            {
                'docutils': {
                    'input_encoding': app.conf['encoding.content'],
                    'output_encoding': app.conf['encoding.output'],
                }
            },
            app.conf.get('ext.restructuredtext', {}))

        app.add_converter(self)

    def _publish_parts(self, text):
        # Creating a new Writer instance is cheap operation, since
        # its initialization is almost empty.
        writer = html4css1.Writer()

        # We need custom translator in order to override translation
        # behaviour. For instance, we don't want to have <div> wrappers
        # around sections.
        writer.translator_class = _HtmlTranslator

        # Party on, dude! Let's get converted data.
        parts = publish_parts(
            source=text,
            writer=writer,
            settings_overrides=dict(self._conf['docutils']))
        return parts

    def to_html(self, text):
        parts = self._publish_parts(text)

        meta = {}
        if parts['title']:
            meta['title'] = parts['title']

        return meta, parts['body'].strip()


class _HtmlTranslator(html4css1.HTMLTranslator):
    """
    Custom HTML translator.

    * skips <div class="section"> wrapper around sections
    * uses <code> instead of <tt> for inline code
    """

    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    def visit_literal(self, node):
        text = node.astext()

        self.body.append(self.starttag(node, 'code', '', CLASS=''))
        self.body.append(text)
        self.body.append('</code>')

        # content already processed
        raise nodes.SkipNode
