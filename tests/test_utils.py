# coding: utf-8
"""
    tests.test_utils
    ~~~~~~~~~~~~~~~~

    Tests Holocron's utils.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
from unittest import mock

from holocron.utils import mkdir, normalize_url
from tests import HolocronTestCase


class TestMkdir(HolocronTestCase):

    @mock.patch('holocron.utils.os.path.exists', return_value=False)
    @mock.patch('holocron.utils.os.makedirs')
    def test_makedirs_is_called(self, makedirs, _):

        mkdir('path/to/dir')
        makedirs.assert_called_with('path/to/dir')

    @mock.patch('holocron.utils.os.path.exists', return_value=True)
    @mock.patch('holocron.utils.os.makedirs')
    def test_makedirs_is_not_called(self, makedirs, _):

        mkdir('path/to/dir')
        self.assertFalse(makedirs.called)


class TestNormalizeUrl(HolocronTestCase):

    def test_default(self):
        """
        Tests that func works correctly with default parameters.
        """
        self.assertEqual(normalize_url('test.com'), 'http://test.com/')
        self.assertEqual(normalize_url('http://test.com'), 'http://test.com/')
        self.assertEqual(normalize_url('https://test.com'), 'https://test.com/')

    def test_trailing_slash(self):
        """
        Tests that trailing slash works correctly: ensures that present or not.
        """
        self.assertEqual(
            normalize_url('http://test.com', trailing_slash=True),
            'http://test.com/')
        self.assertEqual(
            normalize_url('http://test.com/', trailing_slash=True),
            'http://test.com/')

        self.assertEqual(
            normalize_url('http://test.com', trailing_slash=False),
            'http://test.com')
        self.assertEqual(
            normalize_url('http://test.com/', trailing_slash=False),
            'http://test.com')

        self.assertEqual(
            normalize_url('http://test.com', trailing_slash='keep'),
            'http://test.com')
        self.assertEqual(
            normalize_url('http://test.com/', trailing_slash='keep'),
            'http://test.com/')
