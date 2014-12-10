# coding: utf-8
"""
    tests.ext.converters.markdown
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Markdown converter.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from holocron.ext.converters import markdown

from dooku.conf import Conf
from tests import HolocronTestCase


class TestMarkdownConverter(HolocronTestCase):

    def setUp(self):
        self.conv = markdown.Markdown(Conf({
            'markdown': {
                'extensions': [],
            }
        }))

    def test_markdown_simple_post(self):
        meta, html = self.conv.to_html(
            '# some title\n'
            '\n'
            'some text with **bold**\n')

        self.assertEqual(meta['title'], 'some title')
        self.assertEqual(html, '<p>some text with <strong>bold</strong></p>')

    def test_markdown_without_title(self):
        meta, html = self.conv.to_html(
            'some text with **bold** and *italic*\n')

        self.assertEqual(meta, {})
        self.assertEqual(
            html, '<p>some text with <strong>bold</strong> and <em>italic</em></p>')

    def test_markdown_codehilite_extension(self):
        self.conv = markdown.Markdown(Conf({
            'markdown': {
                'extensions': ['codehilite', 'extra'],
            }
        }))

        _, html = self.conv.to_html(
            '```python\n'
            'lambda x: pass\n'
            '```\n')

        self.assertIn('codehilite', html)
