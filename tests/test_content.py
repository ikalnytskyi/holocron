"""
    tests.test_content
    ~~~~~~~~~~~~~~~~~~

    Tests Holocron's content types.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from dooku.conf import Conf

from holocron.app import Holocron
from holocron import content

from tests import HolocronTestCase, FakeConverter


class DocumentTestCase(HolocronTestCase):
    """
    A testcase helper that prepares a document instance.
    """

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

    def setUp(self):
        """
        Prepares a document instance with a fake config.
        """
        self.app = Holocron(self._conf)
        self.app.add_converter(FakeConverter())
        self.doc = self.document_class(self.app)
        self.doc['destination'] = self.document_filename


class TestDocument(DocumentTestCase):
    """
    Tests an abstract document base class.
    """

    document_class = content.Document
    document_filename = 'about/cv.mdown'

    def test_url(self):
        """
        The url property has to be the same as a path relative to the
        content folder.
        """
        self.assertEqual(self.doc.url, '/about/cv.mdown')

    def test_abs_url(self):
        """
        The abs_url property has to be an absolute url to the resource.
        """
        self.assertEqual(self.doc.abs_url, 'http://example.com/about/cv.mdown')


class TestPage(DocumentTestCase):
    """
    Tests Page document.
    """

    _open_fn = 'holocron.content.open'

    document_class = content.Page
    document_filename = 'about/cv.mdown'

    def setUp(self):
        """
        Prepares a document instance with a fake config. We need to mock
        open function to simulate reading from the file.
        """
        super(TestPage, self).setUp()

    def test_default_attributes(self):
        """
        The page instance has to has a set of default attributes with
        valid values.
        """
        self.assertEqual(self.doc['author'], self.app.conf['site.author'])
        self.assertEqual(self.doc['template'], self.document_class.template)


class TestPost(TestPage):
    """
    Tests Post document.
    """

    document_class = content.Post
