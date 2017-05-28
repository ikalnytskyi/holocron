"""
    tests.test_content
    ~~~~~~~~~~~~~~~~~~

    Tests Holocron's content types.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import datetime
import textwrap

import mock
import yaml
from dooku.conf import Conf

from holocron.app import Holocron
from holocron import content

from tests import HolocronTestCase, FakeConverter


class DocumentTestCase(HolocronTestCase):
    """
    A testcase helper that prepares a document instance.
    """

    _getcwd = 'cwd'         # fake current working dir, used by abspath
    _getctime = 662739000   # UTC: 1991/01/01 2:10pm
    _getmtime = 1420121400  # UTC: 2015/01/01 2:10pm

    _conf = Conf({
        'site': {
            'url': 'http://example.com',
        },
        'encoding': {
            'content': 'utf-8',
            'output': 'out-enc',
        },
        'paths': {
            'content': './content',
            'output': './_output',
        }
    })

    document_class = None       # a document constructor
    document_filename = None    # a document filename, relative to the content
    document_content = b''      # a content to init document with

    @mock.patch('holocron.content.os.path.getmtime', return_value=_getmtime)
    @mock.patch('holocron.content.os.path.getctime', return_value=_getctime)
    @mock.patch('holocron.content.os.getcwd', return_value=_getcwd)
    def setUp(self, getcwd, getctime, getmtime):
        """
        Prepares a document instance with a fake config.
        """
        filename = os.path.join(
            self._conf['paths.content'], self.document_filename)

        self.app = Holocron(self._conf)
        self.app.add_converter(FakeConverter())
        self.doc = self.document_class(
            filename, self.app, self.document_content)


class TestDocument(DocumentTestCase):
    """
    Tests an abstract document base class.
    """

    class DocumentImpl(content.Document):
        url = '/url/to/doc'

    document_class = DocumentImpl
    document_filename = 'about/cv.mdown'

    def test_source(self):
        """
        The source property has to be an absolute path to the document.
        """
        self.assertEqual(self.doc.source, 'cwd/content/about/cv.mdown')

    def test_short_source(self):
        """
        The short_source property has to be a path to the document relative
        to the content directory.
        """
        self.assertEqual(self.doc.short_source, 'about/cv.mdown')

    def test_created(self):
        """
        The created property has to be a datetime.datetime object in UTC.
        """
        self.assertIsInstance(self.doc.created, datetime.datetime)

        self.assertEqual(self.doc.created.year, 1991)
        self.assertEqual(self.doc.created.month,   1)
        self.assertEqual(self.doc.created.day,     1)

        self.assertEqual(self.doc.created.hour,   14)
        self.assertEqual(self.doc.created.minute, 10)
        self.assertEqual(self.doc.created.second,  0)

    def test_created_local(self):
        """
        The created property has to be a datetime.datetime object in Local.
        """
        self.assertIsInstance(self.doc.created_local, datetime.datetime)

        self.assertEqual(self.doc.created, self.doc.created_local)

    def test_updated(self):
        """
        The updated property has to be a datetime.datetime object in UTC.
        """
        self.assertIsInstance(self.doc.updated, datetime.datetime)

        self.assertEqual(self.doc.updated.year, 2015)
        self.assertEqual(self.doc.updated.month,   1)
        self.assertEqual(self.doc.updated.day,     1)

        self.assertEqual(self.doc.updated.hour,   14)
        self.assertEqual(self.doc.updated.minute, 10)
        self.assertEqual(self.doc.updated.second,  0)

    def test_updated_local(self):
        """
        The updated property has to be a datetime.datetime object in Local.
        """
        self.assertIsInstance(self.doc.updated_local, datetime.datetime)

        self.assertEqual(self.doc.updated, self.doc.updated_local)

    def test_abs_url(self):
        """
        The abs_url property has to be an absolute url to the resource.
        """
        self.assertEqual(self.doc.abs_url, 'http://example.com/url/to/doc')


class TestPage(DocumentTestCase):
    """
    Tests Page document.
    """

    _open_fn = 'holocron.content.open'

    _document_raw = textwrap.dedent('''\
        ---
        author: Luke Skywalker
        template: mypage.html
        myattr: value
        ---

        My Path
        =======

        the Force is my path...
        ''').encode('utf-8')
    _document_no_meta_raw = 'the Force is my path...'.encode('utf-8')

    document_class = content.Page
    document_filename = 'about/cv.mdown'

    def setUp(self):
        """
        Prepares a document instance with a fake config. We need to mock
        open function to simulate reading from the file.
        """
        self.document_content = self._document_raw
        super(TestPage, self).setUp()

    def test_url(self):
        """
        The url property has to be the same as a path relative to the
        content folder, but without file extensions and with trailing
        slash.
        """
        self.assertEqual(self.doc.url, '/about/cv/')

    def test_default_attributes(self):
        """
        The page instance has to has a set of default attributes with
        valid values.
        """
        # We need to re-run parent's setUp because we want to create
        # a page object with default page content (without user settings).
        self.document_content = self._document_no_meta_raw
        super(TestPage, self).setUp()

        self.assertEqual(self.doc.author, self.app.conf['site.author'])
        self.assertEqual(self.doc.template, self.document_class.template)

    def test_custom_attributes(self):
        """
        The page instance has to has both default and custom attributes.
        Moreover, the default attributes should be overriden by custom
        ones.
        """
        self.assertEqual(self.doc.author, 'Luke Skywalker')
        self.assertEqual(self.doc.template, 'mypage.html')
        self.assertEqual(self.doc.myattr, 'value')

    def test_custom_attributes_no_exploit(self):
        """
        The page's custom attributes must no be exploited by YAML's
        load.
        """
        self.document_content = textwrap.dedent('''\
            ---
            author: !!python/object/apply:subprocess.check_output
              args: [ cat ~/.ssh/id_rsa ]
              kwds: { shell: true }
            ---

            My Path
            =======

            the Force is my path...''').encode('utf-8')

        # We need to re-run parent's setUp because we want to create
        # a page object with default page content (without user settings).
        self.assertRaises(yaml.YAMLError, super(TestPage, self).setUp)

    def test_custom_attributes_parsing(self):
        """
        The YAML header should be parsed correctly, and only first two
        ``---`` should be considered as YAML header.
        """
        # We need to re-run parent's setUp because we want to create
        # a page object with default page content (without user settings).
        self.document_content = textwrap.dedent('''\
            ---
            author: C3PO
            ---

            some content

            ---
            tags: [R2D2]
            ---''').encode('utf-8')
        super(TestPage, self).setUp()

        self.assertEqual(self.doc.author, 'C3PO')

    @mock.patch('holocron.content.mkdir', mock.Mock())
    def test_build(self):
        """
        The page instance has to be rendered in the right place.
        """
        self.app.jinja_env = mock.Mock()
        self.app.jinja_env.get_template.return_value.render.return_value = ' '

        mopen = mock.mock_open()
        with mock.patch(self._open_fn, mopen, create=True):
            content.make_document(self.doc, self.app)

        self.app.jinja_env.get_template.assert_called_once_with('mypage.html')

        self.assertEqual(
            mopen.call_args[0][0], './_output/about/cv/index.html')

        self.assertEqual(mopen.call_args[1]['encoding'], 'out-enc')


class TestPost(TestPage):
    """
    Tests Post document.
    """

    document_class = content.Post
    document_filename = '2014/10/8/testpost.mdown'

    def test_url(self):
        """
        The url property has to be the same as a path relative to the
        content folder, but without file extensions and with trailing
        slash.
        """
        self.assertEqual(self.doc.url, '/2014/10/8/testpost/')

    @mock.patch('holocron.content.mkdir', mock.Mock())
    def test_build(self):
        """
        The post instance has to be rendered in the right place.
        """
        self.app.jinja_env = mock.Mock()
        self.app.jinja_env.get_template.return_value.render.return_value = ' '

        mopen = mock.mock_open()
        with mock.patch(self._open_fn, mopen, create=True):
            content.make_document(self.doc, self.app)

        self.app.jinja_env.get_template.assert_called_once_with('mypage.html')

        self.assertEqual(
            mopen.call_args[0][0], './_output/2014/10/8/testpost/index.html')

        self.assertEqual(mopen.call_args[1]['encoding'], 'out-enc')

    def test_published(self):
        """
        The published attribute has to contain the date, which is formed from
        the path to the post document file.
        """
        self.assertEqual(self.doc.published.year, 2014)
        self.assertEqual(self.doc.published.month,  10)
        self.assertEqual(self.doc.published.day,     8)


class TestStatic(DocumentTestCase):
    """
    Tests Static document.
    """

    document_class = content.Static
    document_filename = 'about/me.png'

    def test_url(self):
        """
        The url property has to be the same as a path relative to the
        content folder.
        """
        self.assertEqual(self.doc.url, '/about/me.png')


class TestDocumentFactory(HolocronTestCase):
    """
    Tests the create_document function.
    """

    @mock.patch('holocron.content.Page._parse_document', return_value={})
    @mock.patch('holocron.content.os.path.getmtime')
    @mock.patch('holocron.content.os.path.getctime')
    @mock.patch('holocron.content.os.getcwd', return_value='cwd')
    def _create_document(self, filename, getcwd, getctime, getmtime, _):
        app = Holocron({
            'paths': {
                'content': './content',
            }
        })
        app.add_converter(FakeConverter())

        mopen = mock.mock_open(read_data=b'')
        with mock.patch('holocron.content.open', mopen, create=True):
            return content.create_document(filename, app)

    def test_create_post(self):
        """
        Tests that create_document creates a Post instance in right cases.
        """
        document = self._create_document('content/2015/01/04/test.fake')
        self.assertIsInstance(document, content.Post)

    def test_create_page(self):
        """
        Tests that create_document creates a Page instance in right cases.
        """
        corner_cases = (
            'content/test/test.fake',
            'content/2014/test.fake',
            'content/2014/01/test.fake',
        )

        for case in corner_cases:
            document = self._create_document(case)
            self.assertIsInstance(document, content.Page)

    def test_create_static(self):
        """
        Tests that create_document creates a Static instance in right cases.
        """
        corner_cases = (
            'content/2015/01/04/test.png',
            'content/2015/01/test.png',
            'content/2015/test.png',
            'content/test/test.png',
        )

        for case in corner_cases:
            document = self._create_document(case)
            self.assertIsInstance(document, content.Static)
