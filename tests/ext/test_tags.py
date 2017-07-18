"""
    tests.ext.test_tags
    ~~~~~~~~~~~~~~~~~~~

    Tests Tags generator.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from datetime import datetime

import mock

from holocron.app import Holocron
from holocron.content import Post, Page, Document, make_document
from holocron.ext.tags import Tags, Tag

from tests import HolocronTestCase, FakeConverter


class TestTagObjects(HolocronTestCase):
    """
    Test tag wrapper class.
    """
    def setUp(self):
        # fake tags
        self.tag1 = 'tag1'
        self.tag2 = 'tag2'

        # some directory where all tag pages locates
        self.output = 'test/tags/{tag}'

    def test_tag_name(self):
        """
        Test that tag object returns correct tag name.
        """
        tag1_obj = Tag(self.tag1, self.output)
        tag2_obj = Tag(self.tag2, self.output)

        self.assertEquals(tag1_obj.name, self.tag1)
        self.assertEquals(tag2_obj.name, self.tag2)

    def test_tag_url(self):
        """
        Tag object should return correct url with leading and closing slashes.
        """
        tag1_obj = Tag(self.tag1, self.output)

        self.assertEquals(tag1_obj.url, '/test/tags/tag1/')


class TestTagsGenerator(HolocronTestCase):
    """
    Test tags generator.
    """
    #: generate html headers with years that is used for grouping in templates
    h_year = '<span class="year">{0}</span>'.format

    def setUp(self):
        self.app = Holocron(conf={
            'sitename': 'MyTestSite',
            'siteurl': 'www.mytest.com',
            'author': 'Tester',

            'encoding': {
                'output': 'my-enc',
            },

            'paths': {
                'output': 'path/to/output',
            },

            'ext': {
                'enabled': [],
                'tags': {
                    'output': 'mypath/tags/{tag}',
                },
            },
        })
        self.tags = Tags(self.app)

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

        self.post_malformed = mock.Mock(
            spec=Post,
            source='test',
            tags='testtag')

        self.page = mock.Mock(spec=Page)
        self.static = mock.Mock(spec=Document)

        self.open_fn = 'holocron.ext.tags.open'

    @mock.patch('holocron.ext.tags.mkdir', mock.Mock())
    def _get_content(self, documents):
        """
        This helper method mocks the open function and return the content
        passed as input to write function.
        """
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.tags.generate(documents)

            # extract what was generated and what was passed to f.write()
            content, = mopen().write.call_args[0]
            return content

    @mock.patch('holocron.ext.tags.mkdir')
    def _get_tags_content(self, documents, mock_mkdir):
        with mock.patch(self.open_fn, mock.mock_open(), create=True) as mopen:
            self.tags.generate(documents)

            open_calls = [c[0][0] for c in mopen.call_args_list if c != '']
            write_calls = [c[0][0] for c in mopen().write.call_args_list]
            mkdir_calls = [c[0][0] for c in mock_mkdir.call_args_list]

            # form a tuple that contains corresponding open and write calls
            # and sort it aplhabetically, so the testtag1 comes first
            content = list(zip(open_calls, write_calls, mkdir_calls))
            content.sort()

            return content

    def test_tag_template_building(self):
        """
        Test that tags function writes a post to a tag template.
        """
        posts = [self.post_early, self.post_moderate]

        content = self._get_tags_content(posts)

        # check that open, write and mkdir functions were called three times
        # according to the number of different tags in test documents
        for entry in content:
            self.assertEqual(len(entry), 3)

        # test that output html contains early_post with its unique tag
        self.assertEqual(
            'path/to/output/mypath/tags/testtag1/index.html', content[0][0])

        self.assertIn(self.h_year(2012), content[0][1])
        self.assertIn('<a href="www.post_early.com">', content[0][1])

        self.assertEqual('path/to/output/mypath/tags/testtag1', content[0][2])

        # test that output html contains posts with common tag
        self.assertEqual(
            'path/to/output/mypath/tags/testtag2/index.html', content[1][0])

        self.assertIn(self.h_year(2012), content[1][1])
        self.assertIn(self.h_year(2013), content[1][1])

        self.assertIn('<a href="www.post_early.com">', content[1][1])
        self.assertIn('<a href="www.post_moderate.com">', content[1][1])

        self.assertEqual('path/to/output/mypath/tags/testtag2', content[1][2])

        # test that output html contains moderate_post with its unique tag
        self.assertEqual(
            'path/to/output/mypath/tags/testtag3/index.html', content[2][0])

        self.assertIn(self.h_year(2013), content[2][1])
        self.assertIn('<a href="www.post_moderate.com">', content[2][1])

        self.assertEqual('path/to/output/mypath/tags/testtag3', content[2][2])

    def test_sorting_out_mixed_documents(self):
        """
        Test that Tags sorts out post documents from documents of other types.
        """
        documents = [self.page, self.static, self.post_late]
        content = self._get_content(documents)

        self.assertIn(self.h_year(2014), content)
        self.assertIn('<a href="www.post_late.com">', content)

    def test_posts_patching_with_tag_objects(self):
        """
        Test that Tags patches post's tags attribute.
        """
        posts = [self.post_late]

        self._get_tags_content(posts)

        self.assertEquals(self.post_late.tags[0].name, 'testtag2')
        self.assertEquals(self.post_late.tags[0].url, '/mypath/tags/testtag2/')

    @mock.patch('holocron.content.os.mkdir', mock.Mock())
    @mock.patch('holocron.content.os.path.getmtime')
    @mock.patch('holocron.content.os.path.getctime')
    def test_tags_are_shown_in_post(self, _, __):
        """
        Test that tags are actually get to the output.
        """
        # since we're interested in rendered page, let's register
        # a fake converter for that purpose
        self.app.add_converter(FakeConverter())

        post = Post(self.app)
        setattr(post, 'destination', '2015/05/23/filename.fake')
        setattr(post, 'published', datetime.now())
        setattr(post, 'tags', ['tag1', 'tag2'])

        self._get_content([post])

        open_fn = 'holocron.content.open'
        with mock.patch(open_fn, mock.mock_open(), create=True) as mopen:
            make_document(post, self.app)
            content = mopen().write.call_args[0][0]

        err = 'Could not find link for #tag1.'
        self.assertIn('<a href="/mypath/tags/tag1/">#tag1</a>', content, err)

        err = 'Could not find link for #tag2.'
        self.assertIn('<a href="/mypath/tags/tag2/">#tag2</a>', content, err)

    @mock.patch('holocron.ext.tags.mkdir')
    def test_malformed_tags_are_skipped(self, mock_mkdir):
        """
        Test if tags formatting is correct.
        """
        content = self._get_tags_content([self.post_malformed])

        self.assertEqual(content, [])
