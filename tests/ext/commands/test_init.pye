# coding: utf-8
"""
    tests.ext.commands.test_init
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Init command.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os

import mock

from holocron.app import Holocron
from holocron.ext.commands import init

from tests import HolocronTestCase


@mock.patch.object(os, 'curdir', '/path/to/curdir')
class TestInitCommand(HolocronTestCase):

    @mock.patch('holocron.ext.commands.init.copy_tree')
    @mock.patch('holocron.ext.commands.init.os.listdir', return_value=[])
    def test_curdir_was_initialized(self, _, copy_tree):
        command = init.Init()
        command.execute(app=mock.Mock(spec=Holocron), arguments=None)

        self.assertEqual(copy_tree.call_args[0][1], '/path/to/curdir')

    @mock.patch('holocron.ext.commands.init.copy_tree')
    @mock.patch('holocron.ext.commands.init.os.listdir', return_value=['a'])
    def test_curdir_wasnot_initialized(self, _, copy_tree):
        command = init.Init()
        command.execute(app=mock.Mock(spec=Holocron), arguments=None)

        # it shouldn't work for non-empty directories
        self.assertEqual(copy_tree.call_count, 0)
