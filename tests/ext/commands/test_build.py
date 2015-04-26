# coding: utf-8
"""
    tests.ext.commands.test_build
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Build command.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import argparse
from unittest import mock

from dooku.conf import Conf

from holocron.app import Holocron
from holocron.ext.commands import build

from tests import HolocronTestCase


class TestBuildCommand(HolocronTestCase):

    def setUp(self):
        self.fake_app = mock.Mock(conf=Conf({
            'paths': {
                'output': 'path/output',
            },
        }), spec=Holocron)

    @mock.patch('holocron.ext.commands.build.shutil.rmtree')
    def test_run_holocron(self, fake_rmtree):
        command = build.Build()
        command.execute(self.fake_app, argparse.Namespace(clear=False))

        self.fake_app.run.assert_called_with()
        self.assertEqual(fake_rmtree.call_count, 0)

    @mock.patch('holocron.ext.commands.build.shutil.rmtree')
    def test_clear_output(self, fake_rmtree):
        command = build.Build()
        command.execute(self.fake_app, argparse.Namespace(clear=True))

        self.fake_app.run.assert_called_once_with()
        fake_rmtree.assert_called_once_with('path/output', ignore_errors=True)
