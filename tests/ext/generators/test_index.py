# coding: utf-8
"""
    tests.ext.generators.test_index
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Index generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from datetime import datetime

import mock
from dooku.conf import Conf

from holocron.ext.generators import index
from holocron.content import Post, Page, Static
from holocron.app import Holocron

from tests import HolocronTestCase


class TestIndexGenerator(HolocronTestCase):
    """
    Test index generator.
    """
    #: tag that preceds a group of posts with the same year
    year_tag = '<h2>'

    #: generate html header with year that is used for grouping in templates
    h_year = '<h2>{0}</h2>'.format

    def setUp(self):
        """
        Creates generator object and number of posts which will be further used
        in test sets.
        """

        self.index = index.Index(Holocron(conf=Conf({
            'sitename': 'MyTestSite',
            'siteurl': 'www.mytest.com',
            'author': 'Tester',

            'encoding': {
                'output': 'my-enc',
            },

            'paths': {
                'output': 'path/to/output',
            },
        })))

        self.open_fn = 'holocron.ext.generators.index.open'

        self.date_early = datetime(2012, 2, 2)
        self.date_late = datetime(2014, 6, 12)
        self.date_moderate = datetime(2013, 4, 1)

        self.post_early = mock.Mock(
            spec=Post, published=self.date_early, url='www.post_early.com',)

        self.post_moderate = mock.Mock(
            spec=Post,
            published=self.date_moderate,
            url='www.post_moderate.com')

        self.post_late = mock.Mock(
            spec=Post, published=self.date_late, url='www.post_late.com')

        self.page = mock.Mock(spec=Page)
        self.static = mock.Mock(spec=Static)

    def _get_content(self, documents):
        """
        This helper method mocks the open function and return the content
        passed as input to write function.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.index.generate(documents)

            content, = mopen().write.call_args[0]
            return content

    def test_save_index_to_filesystem_and_enc(self):
        """
        Test that index function saves index.html file to a proper location.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.index.generate([])

            self.assertEqual(
                mopen.call_args[0][0], 'path/to/output/index.html')
            self.assertEqual(
                mopen.call_args[1]['encoding'], 'my-enc')

    def test_index_encoding_meta_tag(self):
        """
        The index.html has to have a tag with right encoding.
        """
        output = self._get_content([])

        self.assertIn('charset="my-enc"', output)

    def test_index_empty(self):
        """
        Test that running input on empty list of documents doesn't cause crash.
        """
        content = self._get_content([])

        self.assertNotIn(self.year_tag, content)

    def test_index_with_posts(self):
        """
        Index function has to form an html file, where all posts are displayed.
        """
        posts = [self.post_early, self.post_moderate, self.post_late]
        content = self._get_content(posts)

        self.assertIn('<a href="www.post_late.com">', content)
        self.assertIn(self.h_year(2014), content)

        self.assertIn(self.h_year(2013), content)
        self.assertIn('<a href="www.post_moderate.com">', content)

        self.assertIn(self.h_year(2012), content)
        self.assertIn('<a href="www.post_early.com">', content)

    def test_mixed_documents(self):
        """
        Test that Index sorts out post documents from documents of other types.
        """
        documents = [self.page, self.static, self.post_late]
        content = self._get_content(documents)

        self.assertIn(self.h_year(2014), content)
        self.assertIn('<a href="www.post_late.com">', content)
