# coding: utf-8
"""
    tests.ext.converters.test_markdown
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Markdown converter.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import textwrap

from holocron.app import Holocron
from holocron.ext.converters import markdown

from tests import HolocronTestCase


class TestMarkdownConverter(HolocronTestCase):
    """
    Test Markdown converter.
    """

    def setUp(self):
        self.conv = markdown.Markdown(Holocron(conf={
            'ext': {
                'markdown': {
                    'extensions': [],
                },
            },
        }))

    def test_markdown_simple_post(self):
        """
        Markdown function has to fucking work.
        """
        meta, html = self.conv.to_html(textwrap.dedent('''\
            # some title

            some text with **bold**
        '''))

        self.assertEqual(meta['title'], 'some title')
        self.assertEqual(html, '<p>some text with <strong>bold</strong></p>')

    def test_markdown_without_title(self):
        """
        Converter has to work even if there's no title in the document.
        """
        meta, html = self.conv.to_html(
            'some text with **bold** and *italic*\n')

        self.assertEqual(meta, {})
        self.assertEqual(html, (
            '<p>some text with <strong>bold</strong> and <em>italic</em></p>'))

    def test_markdown_codehilite_extension(self):
        """
        Converter has to use Pygments to highlight code blocks.
        """
        self.conv = markdown.Markdown(Holocron(conf={
            'ext': {
                'markdown': {
                    'extensions': ['codehilite'],
                },
            },
        }))

        _, html = self.conv.to_html(textwrap.dedent('''\
            test codeblock

                :::python
                lambda x: pass
        '''))

        self.assertIn('codehilite', html)

    def test_markdown_extra_code(self):
        """
        Converter has to support GitHub's fence code syntax.
        """
        self.conv = markdown.Markdown(Holocron(conf={
            'ext': {
                'markdown': {
                    'extensions': ['codehilite', 'extra'],
                },
            },
        }))

        _, html = self.conv.to_html(textwrap.dedent('''\
            ```python
            lambda x: pass
            ```
        '''))

        self.assertIn('codehilite', html)

    def test_markdown_extra_tables(self):
        """
        Converter has to support tables syntax.
        """
        self.conv = markdown.Markdown(Holocron(conf={
            'ext': {
                'markdown': {
                    'extensions': ['extra'],
                },
            },
        }))

        _, html = self.conv.to_html(textwrap.dedent('''\
            column a | column b
            ---------|---------
               foo   |   bar
        '''))

        self.assertIn('table', html)

        self.assertIn('<th>column a</th>', html)
        self.assertIn('<th>column b</th>', html)

        self.assertIn('<td>foo</td>', html)
        self.assertIn('<td>bar</td>', html)
