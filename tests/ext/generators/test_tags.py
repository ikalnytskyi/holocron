# coding: utf-8
"""
    tests.ext.generators.test_tags
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Tags generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from unittest import mock
from datetime import datetime

from dooku.conf import Conf
from holocron.ext.generators import tags
from holocron.content import Post, Page, Static
from holocron.app import Holocron

from tests import HolocronTestCase


class TestTagsGenerator(HolocronTestCase):
    """
    Test tags generator.
    """
    #: generate html headers with years that is used for grouping in templates
    h_year = '<h2>{0}</h2>'.format

    def setUp(self):

        self.tags = tags.Tags(Holocron(conf=Conf({
            'sitename': 'MyTestSite',
            'siteurl': 'www.mytest.com',
            'author': 'Tester',

            'encoding': {
                'output': 'my-enc',
            },

            'paths': {
                'output': 'path/to/output',
            },

            'generators': {

                'tags': {
                    'output': 'mypath/tags/',
                },

            },
        })))

        self.date_early = datetime(2012, 2, 2)
        self.date_moderate = datetime(2013, 4, 1)
        self.date_late = datetime(2014, 6, 12)

        self.post_early = mock.Mock(
            spec=Post,
            published=self.date_early,
            tags=['testtag1', 'testtag2'],
            title='MyTestPost',
            url='www.post_early.com')

        self.post_moderate = mock.Mock(
            spec=Post,
            published=self.date_moderate,
            url='www.post_moderate.com',
            tags=['testtag2', 'testtag3'])

        self.post_late = mock.Mock(
            spec=Post,
            published=self.date_late,
            url='www.post_late.com',
            tags=['testtag2'])

        self.page = mock.Mock(spec=Page)
        self.static = mock.Mock(spec=Static)

        self.open_fn = 'holocron.ext.generators.tags.open'

    @mock.patch('holocron.ext.generators.tags.mkdir', mock.Mock())
    def _get_content(self, documents):
        """
        This helper method mocks the open function and return the content
        passed as input to write function.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.tags.generate(documents)

            #: extract what was generated and what was passed to f.write()
            content, = mopen().write.call_args[0]
            return content

    @mock.patch('holocron.ext.generators.tags.mkdir')
    def _get_tags_content(self, documents, mock_mkdir):
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.tags.generate(documents)

            open_calls = [c[0][0] for c in mopen.call_args_list if c != '']
            write_calls = [c[0][0] for c in mopen().write.call_args_list]
            mkdir_calls = [c[0][0] for c in mock_mkdir.call_args_list]

            #: form a tuple that contains corresponding open and write calls
            #: and sort it aplhabetically, so the testtag1 comes first
            content = list(zip(open_calls, write_calls, mkdir_calls))
            content.sort()

            return content

    def test_tags_with_posts(self):
        """
        Test that tags function writes a post to a tag template.
        """
        posts = [self.post_early, self.post_moderate]

        content = self._get_tags_content(posts)

        #: check that open, write and mkdir functions were called three times
        #: according to the number of different tags in test documents
        for entry in content:
            self.assertEqual(len(entry), 3)

        #: test that output html contains early_post with its unique tag
        self.assertEqual(
            'path/to/output/mypath/tags/testtag1/index.html', content[0][0])

        self.assertIn(self.h_year(2012), content[0][1])
        self.assertIn('<a href="www.post_early.com">', content[0][1])

        self.assertEqual('path/to/output/mypath/tags/testtag1', content[0][2])

        #: test that output html contains posts with common tag
        self.assertEqual(
            'path/to/output/mypath/tags/testtag2/index.html', content[1][0])

        self.assertIn(self.h_year(2012), content[1][1])
        self.assertIn(self.h_year(2013), content[1][1])

        self.assertIn('<a href="www.post_early.com">', content[1][1])
        self.assertIn('<a href="www.post_moderate.com">', content[1][1])

        self.assertEqual('path/to/output/mypath/tags/testtag2', content[1][2])

        #: test that output html contains moderate_post with its unique tag
        self.assertEqual(
            'path/to/output/mypath/tags/testtag3/index.html', content[2][0])

        self.assertIn(self.h_year(2013), content[2][1])
        self.assertIn('<a href="www.post_moderate.com">', content[2][1])

        self.assertEqual('path/to/output/mypath/tags/testtag3', content[2][2])

    def test_mixed_documents(self):
        """
        Test that Tags sorts out post documents from documents of other types.
        """
        documents = [self.page, self.static, self.post_late]
        content = self._get_content(documents)

        self.assertIn(self.h_year(2014), content)
        self.assertIn('<a href="www.post_late.com">', content)
