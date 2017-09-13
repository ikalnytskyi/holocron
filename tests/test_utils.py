"""
    tests.test_utils
    ~~~~~~~~~~~~~~~~

    Tests Holocron's utils.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import mock

from holocron.utils import mkdir
from tests import HolocronTestCase


class TestMkdir(HolocronTestCase):

    @mock.patch('holocron.utils.os.path.exists', return_value=False)
    @mock.patch('holocron.utils.os.makedirs')
    def test_makedirs_is_called(self, makedirs, _):
        """
        Tests that os.makedirs has been called if path not exists.
        """
        mkdir('path/to/dir')
        makedirs.assert_called_with('path/to/dir')

    @mock.patch('holocron.utils.os.path.exists', return_value=True)
    @mock.patch('holocron.utils.os.makedirs')
    def test_makedirs_is_not_called(self, makedirs, _):
        """
        Tests that os.makedirs hasn't been called if path exist.
        """
        mkdir('path/to/dir')
        makedirs.assert_not_called()
