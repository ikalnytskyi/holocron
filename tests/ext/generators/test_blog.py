# coding: utf-8
"""
    tests.ext.generators.test_blog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Blog generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""
from unittest import mock
from datetime import datetime
from xml.dom import minidom

from dooku.conf import Conf
from holocron.ext.generators import blog
from holocron.content import Page, Post, Static
from holocron.app import Holocron

from tests import HolocronTestCase


class BlogTestCase(HolocronTestCase):
    """
    Base class for tests where common data, generator instance is created and
    some helper methods are provided.
    """

    # generate html headers with years that is used for grouping in templates
    h_year = '<h2>{0}</h2>'.format

    def setUp(self):
        """
        Creates generator object and number of posts which will be further used
        in test sets.
        """

        self.blog = blog.Blog(Holocron(conf=Conf({
            'sitename': 'MyTestSite',
            'siteurl': 'www.mytest.com',
            'author': 'Tester',

            'paths': {
                'output': 'path/to/output',
            },

            'theme': {
                'navigation': [
                    ('feed', '/feed.xml'),
                ],
            },

            'generators': {

                'blog': {
                    'feed': {
                        'save_as': 'myfeed.xml',
                        'posts_number': 1,
                    },

                    'index': {
                        'save_as': 'myindex.html',
                    },

                    'tags': {
                        'output': 'mypath/tags/',
                        'save_as': 'myindex.html',
                    },
                },
            },
        })))

        self.open_fn = 'holocron.ext.generators.blog.open'

        self.date_early = datetime(2012, 2, 2)
        self.date_late = datetime(2014, 6, 12)
        self.date_moderate = datetime(2013, 4, 1)

        self.date_early_updated = datetime(2012, 4, 4)

        self.post_early = mock.Mock(
            spec=Post,
            created=self.date_early,
            created_local=self.date_early,
            updated_local=self.date_early_updated,
            tags=['testtag1', 'testtag2'],
            title='MyTestPost',
            url='www.post_early.com',
            abs_url='http://www.post_early.com')

        self.post_moderate = mock.Mock(
            spec=Post,
            created=self.date_moderate,
            url='www.post_moderate.com',
            tags=['testtag2', 'testtag3'])

        self.post_late = mock.Mock(
            spec=Post, created=self.date_late, url='www.post_late.com')

    @mock.patch('holocron.ext.generators.blog.mkdir')
    def _get_content(self, documents, test_function, _):
        """
        This helper method mocks the open function and return the content
        passed as input to write function.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            test_function(documents)

            content, = mopen().write.call_args[0]
            return content


class TestExtractPosts(BlogTestCase):
    """
    Test extract posts function.
    """

    def setUp(self):
        super(TestExtractPosts, self).setUp()

        self.page = mock.Mock(spec=Page)
        self.static = mock.Mock(spec=Static)

    def test_extract_posts_with_empty_list(self):
        """
        Test extract_posts should process correctly empty lists.
        """
        documents = self.blog.extract_posts([])

        self.assertEqual(len(documents), 0)

    def test_extract_posts_with_all_doc_types(self):
        """
        The extract_posts has to separate posts from all other types
        of documents passed as input.
        """
        documents = self.blog.extract_posts(
            [self.page, self.static, self.post_moderate])

        self.assertEqual(len(documents), 1)
        self.assertIn(self.post_moderate, documents)

    def test_extract_posts_arragement_by_date(self):
        """
        The extract_posts has to sort separated documents according to their
        creation date.
        """
        documents = self.blog.extract_posts([
            self.post_late, self.post_early, self.post_moderate])

        self.assertEqual(len(documents), 3)
        self.assertEqual(documents[0], self.post_late)
        self.assertEqual(documents[1], self.post_moderate)
        self.assertEqual(documents[2], self.post_early)


class TestIndexGenerator(BlogTestCase):
    """
    Test index generator.
    """
    # tag that preceds a group of posts with the same year
    year_tag = '<h2>'

    def test_save_index_to_filesystem(self):
        """
        Test that index function saves index.html file to a proper location.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.blog.index([])

            self.assertEqual(
                mopen.call_args[0][0], 'path/to/output/myindex.html')

    def test_index_empty(self):
        """
        Test that running input on empty list of documents doesn't cause crash.
        """
        content = self._get_content([], self.blog.index)

        self.assertNotIn(self.year_tag, content)

    def test_index_with_posts(self):
        """
        Index function has to form an html files, where all posts are displayed
        and grouped by year, from the newest on top, to the oldest in the
        bottom.
        """
        posts = [self.post_late, self.post_moderate, self.post_early]

        # assume that extract_posts sorted the posts by date
        content = self._get_content(posts, self.blog.index)

        # test that the latesr post comes first
        self.assertIn('<a href="www.post_late.com">', content)
        self.assertIn(self.h_year(2014), content)

        # delete information about the latest post
        post_position = content.index(
            self.h_year(2014)) + len(self.h_year(2014))
        content = content[post_position:]

        self.assertIn(self.h_year(2013), content)
        self.assertIn('<a href="www.post_moderate.com">', content)

        # another strim to delete next post
        post_position = content.index(
            self.h_year(2013)) + len(self.h_year(2013))
        content = content[post_position:]

        self.assertIn(self.h_year(2012), content)
        self.assertIn('<a href="www.post_early.com">', content)


class TestTagGenerator(BlogTestCase):
    """
    Test tag generator.
    """

    @mock.patch('holocron.ext.generators.blog.mkdir')
    def test_tags_with_posts(self, mock_mkdir):
        """
        Test that tags function writes a post to a tag template.
        """
        posts = [self.post_early, self.post_moderate]

        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.blog.tags(posts)

            open_calls = [c[0][0] for c in mopen.call_args_list if c != '']
            write_calls = [c[0][0] for c in mopen().write.call_args_list]
            mkdir_calls = [c[0][0] for c in mock_mkdir.call_args_list]

            # check that open function was called three times according to
            # number of tags in test documents
            self.assertEqual(len(open_calls), 3)

            # same as previous applies to write
            self.assertEqual(len(write_calls), 3)

            # same as previous applies to mkdir
            self.assertEqual(len(mkdir_calls), 3)

            # form a tuple that contains corresponding open and write calls
            # and sort it aplhabetically, so the testtag1 comes first
            content = list(zip(open_calls, write_calls, mkdir_calls))
            content.sort()

            # test that output html contains early_post with its unique tag
            self.assertEqual(
                'path/to/output/mypath/tags/testtag1/myindex.html',
                content[0][0])

            self.assertIn(self.h_year(2012), content[0][1])
            self.assertIn('<a href="www.post_early.com">', content[0][1])

            self.assertEqual(
                'path/to/output/mypath/tags/testtag1', content[0][2])

            # test that output html contains posts with common tag
            self.assertEqual(
                'path/to/output/mypath/tags/testtag2/myindex.html',
                content[1][0])

            self.assertIn(self.h_year(2012), content[1][1])
            self.assertIn(self.h_year(2013), content[1][1])

            self.assertIn('<a href="www.post_early.com">', content[1][1])
            self.assertIn('<a href="www.post_moderate.com">', content[1][1])

            self.assertEqual(
                'path/to/output/mypath/tags/testtag2', content[1][2])

            # test that output html contains moderate_post with its unique tag
            self.assertEqual(
                'path/to/output/mypath/tags/testtag3/myindex.html',
                content[2][0])

            self.assertIn(self.h_year(2013), content[2][1])
            self.assertIn('<a href="www.post_moderate.com">', content[2][1])

            self.assertEqual(
                'path/to/output/mypath/tags/testtag3', content[2][2])


class TestFeedGenerator(BlogTestCase):
    """
    Test feed generator.
    """

    def _xml_to_dict(self, xml):
        """
        Generates and returns python dict from an xml string passed as input.
        """
        parsed = minidom.parseString(xml)
        root = parsed.documentElement

        # use this to sort DOM Elements from DOM Text containing '\n' and space
        is_element = lambda n: n.nodeType == n.ELEMENT_NODE
        # use this to parse <link> which contain attributes instead of values
        is_attribute = lambda n: len(n.attributes) != 0
        # use this to distinguish feed common elements (link, title) from posts
        has_child = lambda n: len(n.childNodes) < 2

        urls = [url for url in filter(is_element, root.childNodes)]

        entries = {}
        url_data = {}
        # use to store dictionnaries with post data
        posts = []

        # links in feed differ by attribute (rel or alt), use this attribute
        # as a key to avoid dicts with same key
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

    @mock.patch('holocron.ext.generators.blog.mkdir')
    def test_save_feed_to_filesystem(self, _):
        """
        Feed function has to save feed xml file to a proper location and with
        proper filename. All settings are fetched from the configuration file.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.blog.feed([])

            self.assertEqual(
                mopen.call_args[0][0], 'path/to/output/myfeed.xml')

    def test_feed_template(self):
        """
        Test that feed writes correct values to an xml template.
        """
        content = self._get_content([], self.blog.feed)
        content = self._xml_to_dict(content)

        feed = content['feed']

        self.assertEqual('MyTestSite Feed', feed['title'])
        self.assertEqual('http://www.mytest.com/', feed['id'])
        self.assertEqual('http://www.mytest.com/myfeed.xml', feed['link.self'])
        self.assertEqual('http://www.mytest.com/', feed['link.alternate'])

    def test_feed_empty(self):
        """
        Feed runned on an empty list of documents has to create an xml file, no
        posts should be listed there.
        """
        content = self._get_content([], self.blog.feed)
        content = self._xml_to_dict(content)

        self.assertNotIn('entry', content['feed'])

    def test_feed_with_posts(self):
        """
        Feed function has to funcking work.
        """
        content = self._get_content(
            [self.post_early, self.post_late], self.blog.feed)

        content = self._xml_to_dict(content)

        self.assertIn('entry', content['feed'])
        self.assertEqual(len(content['feed']['entry']), 1)

        feed = content['feed']['entry'][0]

        self.assertEqual('http://www.post_early.com', feed['link'])
        self.assertEqual(self.date_early_updated.isoformat(), feed['updated'])

        self.assertEqual(self.date_early.isoformat(), feed['published'])

        self.assertEqual('http://www.post_early.com', feed['id'])
        self.assertEqual('MyTestPost', feed['title'])
