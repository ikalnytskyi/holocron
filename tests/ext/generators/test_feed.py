# coding: utf-8
"""
    tests.ext.generators.test_feed
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Feed generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from datetime import datetime
from xml.dom import minidom

import mock

from holocron.app import Holocron
from holocron.content import Post, Page, Static
from holocron.ext.generators import feed

from tests import HolocronTestCase, FakeConverter


class TestFeedGenerator(HolocronTestCase):
    """
    Test feed generator.
    """

    def setUp(self):
        self.app = Holocron(conf={
            'site': {
                'title': 'MyTestSite',
                'author': 'Tester',
                'url': 'http://www.mytest.com/',
            },

            'encoding': {
                'output': 'my-enc',
            },

            'paths': {
                'output': 'path/to/output',
            },

            'ext': {
                'enabled': [],
                'feed': {
                    'save_as': 'myfeed.xml',
                    'posts_number': 3,
                },
            },
        })
        self.feed = feed.Feed(self.app)

        self.date_early = datetime(2012, 2, 2)
        self.date_moderate = datetime(2013, 4, 1)
        self.date_late = datetime(2014, 6, 12)

        self.date_early_updated = datetime(2012, 12, 6)
        self.date_moderate_updated = datetime(2013, 12, 6)
        self.date_late_updated = datetime(2014, 12, 6)

        self.post_early = mock.Mock(
            spec=Post,
            published=self.date_early,
            updated_local=self.date_early_updated,
            abs_url='http://www.post_early.com',
            title='MyEarlyPost')

        self.post_moderate = mock.Mock(
            spec=Post,
            published=self.date_moderate,
            updated_local=self.date_moderate_updated,
            abs_url='http://www.post_moderate.com')

        self.post_late = mock.Mock(
            spec=Post,
            published=self.date_late,
            updated_local=self.date_late_updated,
            url='www.post_late.com',
            abs_url='http://www.post_late.com',
            title='MyTestPost')

        self.late_id = '<id>http://www.post_late.com</id>'
        self.moderate_id = '<id>http://www.post_moderate.com</id>'
        self.early_id = '<id>http://www.post_early.com</id>'

        self.page = mock.Mock(spec=Page, url='www.page.com')
        self.static = mock.Mock(spec=Static, url='www.image.com')

        self.open_fn = 'holocron.ext.generators.feed.open'

    @mock.patch('holocron.ext.generators.feed.mkdir', mock.Mock())
    def _get_content(self, documents):
        """
        This helper method mocks the open function and returns the content
        passed as input to write function.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.feed.generate(documents)

            content, = mopen().write.call_args[0]
            return content

    def _xml_to_dict(self, xml):
        """
        Generates and returns python dict from an xml string passed as input.
        """
        parsed = minidom.parseString(xml)
        root = parsed.documentElement

        #: use this to sort DOM Elements from DOM Text containing \n and spaces
        def is_element(n):
            return n.nodeType == n.ELEMENT_NODE

        #: use this to parse <link> which contain attributes instead of values
        def is_attribute(n):
            return len(n.attributes) != 0

        #: use this to distinguish feed common elements (link, title) from post
        def has_child(n):
            return len(n.childNodes) < 2

        urls = [url for url in filter(is_element, root.childNodes)]

        entries = {}
        url_data = {}
        #: use to store dictionnaries with post data
        posts = []

        #: links in feed differ by attribute (rel or alt), use this attribute
        #: as a key to avoid dicts with same key
        key = '{link}.{fmt}'.format

        for url in urls:
            if has_child(url):
                if is_attribute(url):
                    link = key(link=url.nodeName, fmt=url.getAttribute('rel'))
                    entries[link] = url.getAttribute('href')
                else:
                    entries[url.nodeName] = url.firstChild.nodeValue
            else:
                for attr in filter(is_element, url.childNodes):
                    if is_attribute(attr):
                        url_data[attr.nodeName] = attr.getAttribute('href')
                    else:
                        url_data[attr.nodeName] = attr.firstChild.nodeValue

                posts.append(url_data)
                entries[url.nodeName] = posts

        content = {root.nodeName: entries}

        return content

    @mock.patch('holocron.ext.generators.feed.mkdir', mock.Mock())
    def test_feed_filename_and_enc(self):
        """
        Feed function has to save feed xml file to a proper location and with
        proper filename. All settings are fetched from the configuration file.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.feed.generate([])

            self.assertEqual(
                mopen.call_args[0][0], 'path/to/output/myfeed.xml')
            self.assertEqual(
                mopen.call_args[1]['encoding'], 'my-enc')

    def test_feed_encoding_attr(self):
        """
        The feed.xml has to have an XML tag with right encoding.
        """
        output = self._get_content([])

        self.assertIn('encoding="my-enc"', output)

    def test_feed_template(self):
        """
        Test that feed writes correct values to an xml template.
        """
        content = self._get_content([])
        content = self._xml_to_dict(content)

        feed = content['feed']

        self.assertEqual('MyTestSite', feed['title'])
        self.assertEqual('http://www.mytest.com/', feed['id'])
        self.assertEqual('http://www.mytest.com/myfeed.xml', feed['link.self'])
        self.assertEqual('http://www.mytest.com/', feed['link.alternate'])

    def test_feed_empty(self):
        """
        Feed runned on an empty list of documents has to create an xml file, no
        posts should be listed there.
        """
        content = self._get_content([])
        content = self._xml_to_dict(content)

        self.assertNotIn('entry', content['feed'])

    def test_feed_with_posts(self):
        """
        Feed function has to fucking work.
        """
        # here we require only one post to test its content correctness
        # we test posts in other test suites
        self.feed._conf['posts_number'] = 1

        content = self._get_content([self.post_early, self.post_late])
        content = self._xml_to_dict(content)

        self.assertIn('entry', content['feed'])
        self.assertEqual(len(content['feed']['entry']), 1)

        feed = content['feed']['entry'][0]

        self.assertEqual('http://www.post_late.com', feed['link'])
        self.assertEqual(self.date_late_updated.isoformat(), feed['updated'])

        self.assertEqual(self.date_late.isoformat(), feed['published'])

        self.assertEqual('http://www.post_late.com', feed['id'])
        self.assertEqual('MyTestPost', feed['title'])

    def test_posts_in_front_order(self):
        """
        Tests posts ordering. Feed must display older posts first.
        """
        posts = [self.post_early, self.post_moderate, self.post_late]
        content = self._get_content(posts)

        #: test that the latest post comes first
        self.assertIn(self.late_id, content)

        #: delete information about the latest post
        post_position = content.index(self.late_id) + len(self.late_id)
        content = content[post_position:]

        self.assertIn(self.moderate_id, content)

        #: another strim to delete next post
        post_position = content.index(self.moderate_id) + len(self.moderate_id)
        content = content[post_position:]

        self.assertIn(self.early_id, content)

    def test_posts_in_reverse_order(self):
        """
        Tests posts ordering. Feed must display older posts first.
        """
        posts = [self.post_late, self.post_moderate, self.post_early]
        content = self._get_content(posts)

        #: test that the latest post comes first
        self.assertIn(self.late_id, content)

        #: delete information about the latest post
        post_position = content.index(self.late_id) + len(self.late_id)
        content = content[post_position:]

        self.assertIn(self.moderate_id, content)

        #: another strim to delete next post
        post_position = content.index(self.moderate_id) + len(self.moderate_id)
        content = content[post_position:]

        self.assertIn(self.early_id, content)

    def test_mixed_documents(self):
        """
        Test that feed generator sorts out post documents out of other types.
        """
        documents = [self.page, self.post_late, self.static]
        content = self._get_content(documents)

        self.assertNotIn('www.page.com', content)
        self.assertNotIn('www.image.com', content)
        self.assertIn('www.post_late.com', content)

    @mock.patch('holocron.content.os.mkdir', mock.Mock())
    @mock.patch('holocron.content.os.path.getmtime')
    @mock.patch('holocron.content.os.path.getctime')
    def test_feed_link_in_html_header(self, _, __):
        """
        Test that html pages have the link to feed.
        """
        # since we're interested in rendered page, let's register
        # a fake converter for that purpose
        self.app.add_converter(FakeConverter())

        open_fn = 'holocron.content.open'
        with mock.patch(open_fn, mock.mock_open(read_data=''), create=True):
            page = Page('filename.fake', self.app)

        with mock.patch(open_fn, mock.mock_open(), create=True) as mopen:
            page.build()
            content = mopen().write.call_args[0][0]

        err = 'could not find link to feed in html header'
        self.assertIn(
            '<link rel="alternate" type="application/atom+xml" '
            'href="http://www.mytest.com/myfeed.xml" title="MyTestSite">',
            content, err)
