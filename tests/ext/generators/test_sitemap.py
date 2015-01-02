# coding: utf-8
"""
    tests.ext.generators.test_sitemap
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Sitemap generator.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from datetime import datetime
from unittest import mock
from xml.dom import minidom

from dooku.conf import Conf
from holocron.ext.generators import sitemap
from holocron.content import Page, Post, Static

from tests import HolocronTestCase


class TestSitemapGenerator(HolocronTestCase):

    def setUp(self):
        """
        Prepares a sitemap instance with a fake config.
        """
        self.sitemap = sitemap.Sitemap(mock.Mock(conf=Conf({
            'paths': {
                'output': 'path/to/output',
            }
        })))

        self.open_fn = 'holocron.ext.generators.sitemap.open'

        self.post_url = 'http://example.com/post/'
        self.page_url = 'http://example.com/page/'

        self.page_date = datetime(2014, 12, 27)
        self.post_date = datetime(2013, 4, 1)

        self.post = mock.Mock(
            spec=Post, abs_url=self.post_url, updated_local=self.post_date)
        self.page = mock.Mock(
            spec=Page, abs_url=self.page_url, updated_local=self.page_date)
        self.static = mock.Mock(spec=Static)

    def _get_output_content(self, documents):
        """
        Generates a sitemap.xml for given documents and returns what was
        generated - the sitemap.xml content as string.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.sitemap.generate(documents)

            # extract what was generated and what was passed to f.write()
            content, = mopen().write.call_args[0]
            return content

    def _get_sitemap_dict(self, xml):
        """
        Generates and returns python dict from an xml string passed as input.
        """
        parsed = minidom.parseString(xml)
        root = parsed.documentElement

        content = {root.nodeName: []}

        is_element = lambda n: n.nodeType == n.ELEMENT_NODE

        for url in filter(is_element, root.childNodes):
            url_data = {attr.nodeName: attr.firstChild.nodeValue
                        for attr in url.childNodes if is_element(attr)}
            content[root.nodeName].append({url.nodeName: url_data})

        return content

    def test_sitemap_save_to_path(self):
        """
        The sitemap generator has to place "sitemap.xml" file in the output
        folder, which is specified in holocron settings.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.sitemap.generate([])

            self.assertEqual(
                mopen.call_args[0][0], 'path/to/output/sitemap.xml')

    def test_sitemap_wo_documents(self):
        """
        The sitemap geneterator has to generate a valid XML even if we don't
        have any documents.
        """
        output = self._get_output_content([])
        sitemap = self._get_sitemap_dict(output)

        self.assertEqual(sitemap['urlset'], [])

    def test_sitemap_with_static_document(self):
        """
        The sitemap geneterator has to omit static documents when forming XML.
        """
        output = self._get_output_content([self.static])
        sitemap = self._get_sitemap_dict(output)

        self.assertEqual(sitemap['urlset'], [])

    def test_sitemap_with_post_document(self):
        """
        The sitemap geneterator has to generate valid XML from post documents.
        """
        output = self._get_output_content([self.post])
        sitemap = self._get_sitemap_dict(output)

        self.assertEqual(len(sitemap['urlset']), 1)

        post_url = sitemap['urlset'][0]['url']
        self.assertIn('loc', post_url)
        self.assertIn('lastmod', post_url)
        self.assertEqual(self.post_url, post_url['loc'])
        self.assertEqual(self.post_date.isoformat(), post_url['lastmod'])

    def test_sitemap_with_page_document(self):
        """
        The sitemap geneterator has to generate valid XML from page documents.
        """
        output = self._get_output_content([self.page])
        sitemap = self._get_sitemap_dict(output)

        self.assertEqual(len(sitemap['urlset']), 1)

        page_url = sitemap['urlset'][0]['url']
        self.assertIn('loc', page_url)
        self.assertIn('lastmod', page_url)
        self.assertEqual(self.page_url, page_url['loc'])
        self.assertEqual(self.page_date.isoformat(), page_url['lastmod'])

    def test_sitemap_with_all_documents(self):
        """
        The sitemap generator has to form vaild xml from an array of documents
        of different types.
        """
        output = self._get_output_content([self.page, self.static, self.post])
        sitemap = self._get_sitemap_dict(output)

        self.assertEqual(len(sitemap['urlset']), 2)

        page_url = sitemap['urlset'][0]['url']
        self.assertIn('loc', page_url)
        self.assertIn('lastmod', page_url)
        self.assertEqual(self.page_url, page_url['loc'])
        self.assertEqual(self.page_date.isoformat(), page_url['lastmod'])

        post_url = sitemap['urlset'][1]['url']
        self.assertIn('loc', post_url)
        self.assertIn('lastmod', post_url)
        self.assertEqual(self.post_url, post_url['loc'])
        self.assertEqual(self.post_date.isoformat(), post_url['lastmod'])
