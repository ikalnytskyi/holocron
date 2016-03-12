"""
    tests.ext.test_markdown
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tests Markdown converter.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import textwrap

from holocron.app import Holocron
from holocron.ext import Markdown

from tests import HolocronTestCase


class TestMarkdownConverter(HolocronTestCase):
    """
    Test Markdown converter.
    """

    def setUp(self):
        self.conv = Markdown(Holocron(conf={
            'ext': {
                'enabled': [],
                'markdown': {
                    'extensions': [],
                },
            },
        }))

    def test_simple_post(self):
        """
        Markdown converter has to fucking work.
        """
        meta, html = self.conv.to_html(textwrap.dedent('''\
            # some title

            some text with **bold**
        '''))

        self.assertEqual(meta['title'], 'some title')
        self.assertEqual(html, '<p>some text with <strong>bold</strong></p>')

    def test_post_with_sections(self):
        """
        Title must be gone, section must be converted into <h2>.
        """
        meta, html = self.conv.to_html(textwrap.dedent('''\
            some title
            ==========

            some section 1
            --------------

            xxx

            some section 2
            --------------

            yyy
        '''))

        self.assertEqual(meta['title'], 'some title')
        self.assertRegexpMatches(html, (
            '^<h2>some section 1</h2>\s*'
            '<p>xxx</p>\s*'
            '<h2>some section 2</h2>\s*'
            '<p>yyy</p>$'))

    def test_two_titles(self):
        """
        Only first <h1> should be considered as title, other <h1> should
        be kept as is.
        """
        meta, html = self.conv.to_html(textwrap.dedent('''\
            some title
            ==========

            other title
            ===========

            xxx
        '''))

        self.assertEqual(meta['title'], 'some title')
        self.assertRegexpMatches(html, (
            '^<h1>other title</h1>\s*'
            '<p>xxx</p>$'))

    def test_no_title_in_the_middle(self):
        """
        Only <h1> on the beginning should be considered as title, <h1> in
        the middle of content should be kept as is.
        """
        meta, html = self.conv.to_html(textwrap.dedent('''\
            xxx

            some title
            ==========

            yyy
        '''))

        self.assertNotIn('title', meta)
        self.assertRegexpMatches(html, (
            '^<p>xxx</p>\s*'
            '<h1>some title</h1>\s*'
            '<p>yyy</p>$'))

    def test_post_without_title(self):
        """
        Converter has to work even if there's no title in the document.
        """
        meta, html = self.conv.to_html(
            'some text with **bold** and *italic*\n')

        self.assertEqual(meta, {})
        self.assertEqual(html, (
            '<p>some text with <strong>bold</strong> and <em>italic</em></p>'))

    def test_codehilite_extension(self):
        """
        Converter has to use Pygments to highlight code blocks.
        """
        self.conv = Markdown(Holocron(conf={
            'ext': {
                'enabled': [],
                'markdown': {
                    'extensions': ['markdown.extensions.codehilite'],
                },
            },
        }))

        _, html = self.conv.to_html(textwrap.dedent('''\
            test codeblock

                :::python
                lambda x: pass
        '''))

        self.assertRegexpMatches(html, '.*codehilite.*<pre>[\s\S]+</pre>.*')

    def test_extra_code(self):
        """
        Converter has to support GitHub's fence code syntax.
        """
        self.conv = Markdown(Holocron(conf={
            'ext': {
                'enabled': [],
                'markdown': {
                    'extensions': [
                        'markdown.extensions.codehilite',
                        'markdown.extensions.extra',
                    ],
                },
            },
        }))

        _, html = self.conv.to_html(textwrap.dedent('''\
            ```python
            lambda x: pass
            ```
        '''))

        self.assertRegexpMatches(html, '.*codehilite.*<pre>[\s\S]+</pre>.*')

    def test_extra_tables(self):
        """
        Converter has to support tables syntax.
        """
        self.conv = Markdown(Holocron(conf={
            'ext': {
                'enabled': [],
                'markdown': {
                    'extensions': ['markdown.extensions.extra'],
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

    def test_post_with_inline_code(self):
        """
        Converter has to use <code> for inline code.
        """
        _, html = self.conv.to_html('test ``code``\n')

        self.assertEqual(html, '<p>test <code>code</code></p>')
