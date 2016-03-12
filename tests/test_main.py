"""
    tests.test_main
    ~~~~~~~~~~~~~~~

    Tests the Holocron's command line interface.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import logging

import mock
from dooku.ext import ExtensionManager

from holocron.app import Holocron
from holocron.main import main, parse_command_line

from tests import HolocronTestCase


class _FakeExtensionManager(ExtensionManager):
    def __init__(self, *args, **kwargs):
        super(_FakeExtensionManager, self).__init__(*args, **kwargs)

        self._extensions = {
            'cmd1': [mock.Mock()],
            'cmd2': [mock.Mock()],
        }


class TestCli(HolocronTestCase):

    def _get_fake_extension_manager(self):
        ext_manager = ExtensionManager('holocron.fake')
        ext_manager._extensions = \
            {name: [command] for name, command in self._commands.items()}
        return ext_manager

    def setUp(self):
        self._commands = {
            'cmd1': mock.Mock(),
            'cmd2': mock.Mock(),
            'init': mock.Mock(),
        }
        self._extension_manager = mock.patch(
            'holocron.main.ExtensionManager',
            return_value=self._get_fake_extension_manager())
        self._extension_manager.start()

    def tearDown(self):
        self._extension_manager.stop()

    def test_logger_default_level(self):
        main(['cmd1'])

        self.assertEqual(logging.getLogger().level, logging.WARNING)

    def test_logger_verbose_level(self):
        main(['-v', 'cmd1'])

        self.assertEqual(logging.getLogger().level, logging.INFO)

    def test_logger_debug_level(self):
        main(['-d', 'cmd1'])

        self.assertEqual(logging.getLogger().level, logging.DEBUG)

    def test_logger_quite_level(self):
        main(['-q', 'cmd1'])

        self.assertEqual(logging.getLogger().level, logging.CRITICAL)

    def test_cmd1_was_executed(self):
        main(['cmd1'])

        self.assertEqual(self._commands['cmd1']().execute.call_count, 1)
        self.assertEqual(self._commands['cmd2']().execute.call_count, 0)

        holocron, arguments = self._commands['cmd1']().execute.call_args[0]

        self.assertIsInstance(holocron, Holocron)
        self.assertEqual(arguments.conf, '_config.yml')

    def test_cmd2_was_executed(self):
        main(['cmd2'])

        self.assertEqual(self._commands['cmd1']().execute.call_count, 0)
        self.assertEqual(self._commands['cmd2']().execute.call_count, 1)

        holocron, arguments = self._commands['cmd2']().execute.call_args[0]

        self.assertIsInstance(holocron, Holocron)
        self.assertEqual(arguments.conf, '_config.yml')

    def test_init_skips_conf(self):
        main(['init'])

        arguments = self._commands['init']().execute.call_args[0][1]
        self.assertIsNone(arguments.conf)

    @mock.patch('holocron.main.create_app', return_value=None)
    @mock.patch('holocron.main.sys.exit')
    def test_failed_create_app(self, sys_exit, _):
        main(['cmd1'])

        sys_exit.assert_called_once_with(1)

    @mock.patch('holocron.main.argparse.ArgumentParser.print_help')
    @mock.patch('holocron.main.argparse.ArgumentParser.exit')
    def test_just_parent_command(self, exit, help):
        parse_command_line([], {})

        help.assert_called_once_with()
        exit.assert_called_once_with(1)
