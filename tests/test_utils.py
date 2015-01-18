# coding: utf-8
"""
    tests.test_utils
    ~~~~~~~~~~~~~~~~

    Tests Holocron's utils.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from unittest import mock

from holocron.utils import mkdir, normalize_url, iterfiles
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
        corner_cases = (
            ('test.com', 'http://test.com/'),
            ('http://test.com', 'http://test.com/'),
            ('https://test.com', 'https://test.com/'), )

        for url, expected in corner_cases:
            self.assertEqual(normalize_url(url), expected)

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


class TestIterFiles(HolocronTestCase):

    # iterfiles is implemented on top of os.walk. the last one is based on
    # combinations of listdir, isdir, islink calls. so, in order to test the
    # iterfiles we need to mock some primitive calls to return filesystem
    # information.

    _listdir = [
        ['a', '_b', 'c', '_d'],     # root call
        ['e', '_f'],                # call for a
        ['g'],                      # call for b
    ]

    _isdir = [
        True,                       # for a
        True,                       # for _b
        False,                      # for c
        False,                      # for _d

        False,                      # for e
        False,                      # for _f

        False,                      # for g
    ]

    def _get_files(self, *args, **kwargs):
        """
        Returns a list of files produced by iterfiles.
        """
        a = mock.patch('holocron.utils.os.path.isdir', side_effect=self._isdir)
        b = mock.patch('holocron.utils.os.listdir', side_effect=self._listdir)

        with a, b:
            return [i for i in iterfiles(*args, **kwargs)]

    def test_default(self):
        """
        The iterfiles with no arguments has to return all files.
        """
        items = self._get_files('/root')

        self.assertEqual(items, [
            '/root/c',
            '/root/_d',
            '/root/a/e',
            '/root/a/_f',
            '/root/_b/g',
        ])

    def test_pattern(self):
        """
        The iterfiles with pattern has to return all files that satisfies
        a given pattern.
        """
        items = self._get_files('/root', pattern='[!_]*')

        self.assertEqual(items, [
            '/root/c',
            '/root/a/e',
            '/root/_b/g',
        ])

    def test_pattern_exclude_folders(self):
        """
        The iterfiles with pattern has to return all files that satisfies
        a given pattern, and looks for files in those folder that satisfies
        a given pattern too.
        """
        items = self._get_files('/root', pattern='[!_]*', exclude_folders=True)

        self.assertEqual(items, [
            '/root/c',
            '/root/a/e',
        ])
