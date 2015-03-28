# coding: utf-8
"""
    tests.ext.commands.test_build
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Build command.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

from unittest import mock

from holocron.app import Holocron
from holocron.ext.commands import build

from tests import HolocronTestCase


class TestBuildCommand(HolocronTestCase):

    def test_run_holocron(self):
        fake_app = mock.Mock(spec=Holocron)

        command = build.Build()
        command.execute(app=fake_app, arguments=None)

        fake_app.run.assert_called_with()
