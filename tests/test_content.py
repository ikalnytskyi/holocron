# coding: utf-8
"""
    tests.test_content
    ~~~~~~~~~~~~~~~~~~

    Tests Holocron's content types.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import datetime
from unittest import mock

from dooku.conf import Conf
from holocron import app, content
from holocron.ext.converters import markdown

from tests import HolocronTestCase


class DocumentTestCase(HolocronTestCase):
    """
    A testcase helper that prepares a document instance.
    """

    _getcwd = 'cwd'         # fake current working dir, used by abspath
    _getctime = 662739000   # UTC: 1991/01/01 2:10pm
    _getmtime = 1420121400  # UTC: 2015/01/01 2:10pm

    _fake_conf = Conf(app.Holocron.default_conf, {
        'siteurl': 'http://example.com',
        'paths': {
            'content': './content',
            'output': './_output',
        }
    })

    document_class = None       # a document constructor
    document_filename = None    # a document filename, relative to the content

    @mock.patch('holocron.content.os.path.getmtime', return_value=_getmtime)
    @mock.patch('holocron.content.os.path.getctime', return_value=_getctime)
    @mock.patch('holocron.content.os.getcwd', return_value=_getcwd)
    def setUp(self, getcwd, getctime, getmtime):
        """
        Prepares a document instance with a fake config.
        """
        filename = os.path.join(
            self._fake_conf['paths.content'], self.document_filename)

        self.doc = self.document_class(filename, mock.Mock(
            _converters={
                '.mdown': markdown.Markdown(self._fake_conf['converters']), },
            conf=self._fake_conf))


class TestDocument(DocumentTestCase):
    """
    Tests for an abstract document base class.
    """

    class DocumentImpl(content.Document):
        url = '/url/to/doc'
        build = lambda: 42
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
    Tests for a Page document.
    """

    _open_fn = 'holocron.content.open'

    _document_raw = '\n'.join((line.strip() for line in'''\
    ---
    author: Luke Skywalker
    template: mypage.html
    myattr: value
    ---

    My Path
    =======

    the Force is my path...
    '''.splitlines()))

    _document_no_meta_raw = 'the Force is my path...'

    document_class = content.Page
    document_filename = 'about/cv.mdown'

    def setUp(self):
        """
        Prepares a document instance with a fake config. We need to mock
        open function to simulate reading from the file.
        """
        mopen = mock.mock_open(read_data=self._document_raw)
        with mock.patch(self._open_fn, mopen, create=True):
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
        mopen = mock.mock_open(read_data=self._document_no_meta_raw)
        with mock.patch(self._open_fn, mopen, create=True):
            super(TestPage, self).setUp()

        self.assertEqual(self.doc.author, self._fake_conf['author'])
        self.assertEqual(self.doc.template, self.document_class.template)
        self.assertEqual(self.doc.title, self.document_class.title)

    def test_custom_attributes(self):
        """
        The page instance has to has both default and custom attributes.
        Moreover, the default attributes should be overriden by custom
        ones.
        """
        self.assertEqual(self.doc.author, 'Luke Skywalker')
        self.assertEqual(self.doc.template, 'mypage.html')
        self.assertEqual(self.doc.myattr, 'value')
        self.assertEqual(self.doc.title, 'My Path')

    @mock.patch('holocron.content.mkdir')
    def test_build(self, mkdir):
        """
        The page instance has to be rendered in the right place.
        """
        mopen = mock.mock_open(read_data=self._document_no_meta_raw)
        with mock.patch(self._open_fn, mopen, create=True):
            self.doc.build()

        filename, *_ = mopen.call_args[0]
        self.assertEqual(filename, './_output/about/cv/index.html')


class TestPost(TestPage):
    """
    Tests for a Post document.
    """

    document_class = content.Post


class TestStatic(DocumentTestCase):
    """
    Tests for a Static document.
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
    Tests for the create_document functions.
    """

    @mock.patch('holocron.content.Page._parse_document', return_value={})
    @mock.patch('holocron.content.os.path.getmtime')
    @mock.patch('holocron.content.os.path.getctime')
    @mock.patch('holocron.content.os.getcwd', return_value='cwd')
    def _create_document(self, filename, getcwd, getctime, getmtime, _):
        fake_app = mock.Mock(
            _converters={
                '.mdown': mock.Mock(),
            },
            conf=Conf(app.Holocron.default_conf, {
                'paths': {
                    'content': './content',
                }
            }))
        return content.create_document(filename, fake_app)

    def test_create_post(self):
        """
        Tests that create_document creates a Post instance in right cases.
        """
        document = self._create_document('content/2015/01/04/test.mdown')
        self.assertIsInstance(document, content.Post)

    def test_create_page(self):
        """
        Tests that create_document creates a Page instance in right cases.
        """
        corner_cases = (
            'content/test/test.mdown',
            'content/2014/test.mdown',
            'content/2014/01/test.mdown', )

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
            'content/test/test.png', )

        for case in corner_cases:
            document = self._create_document(case)
            self.assertIsInstance(document, content.Static)
