# coding: utf-8
"""
    tests.ext.converters.test_restructuredtext
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests reStructuredText converter.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import textwrap

from holocron.app import Holocron
from holocron.ext.converters import restructuredtext

from tests import HolocronTestCase


class TestReStructuredTextConverter(HolocronTestCase):
    """
    Test restructuredtext converter.
    """

    def setUp(self):
        self.conv = restructuredtext.ReStructuredText(Holocron())

    def test_simple_post(self):
        """
        reStructuredText has to fucking work.
        """
        meta, html = self.conv.to_html(textwrap.dedent('''\
            some title
            ==========

            some text with **bold**
        '''))

        self.assertEqual(meta['title'], 'some title')
        self.assertEqual(html, '<p>some text with <strong>bold</strong></p>')

    def test_post_without_title(self):
        """
        Converter has to work even if there's no title in the document.
        """
        meta, html = self.conv.to_html(
            'some text with **bold** and *italic*\n')

        self.assertNotIn('title', meta)
        self.assertEqual(html, (
            '<p>some text with <strong>bold</strong> and <em>italic</em></p>'))

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

    def test_post_with_code(self):
        """
        Converter has to use Pygments to highlight code blocks.
        """
        _, html = self.conv.to_html(textwrap.dedent('''\
            test codeblock

            .. code:: python

                lambda x: pass
        '''))

        self.assertRegexpMatches(html, (
            r'^<p>test codeblock</p>\s*<pre.*python[^>]*>[\s\S]+</pre>$'))

    def test_post_with_inline_code(self):
        """
        Converter has to use <code> for inline code.
        """
        _, html = self.conv.to_html('test ``code``\n')

        self.assertEqual(html, '<p>test <code>code</code></p>')

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
            '<h2>some title</h2>\s*'
            '<p>yyy</p>$'))
