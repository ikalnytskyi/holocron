"""
    tests.test_content
    ~~~~~~~~~~~~~~~~~~

    Tests Holocron's content types.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from holocron.app import Holocron
from holocron import content

from tests import HolocronTestCase


class DocumentTestCase(HolocronTestCase):
    """
    A testcase helper that prepares a document instance.
    """

    _metadata = {
        'url': 'http://example.com',
    }

    document_class = None       # a document constructor
    document_filename = None    # a document filename, relative to the content

    def setUp(self):
        """
        Prepares a document instance with a fake config.
        """
        self.app = Holocron(metadata=self._metadata)
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
