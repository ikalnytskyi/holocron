# coding: utf-8
"""
    tests.ext.commands.test_serve
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Serve command.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
from unittest import mock

from dooku.conf import Conf

from holocron.app import Holocron
from holocron.ext.commands import serve

from tests import HolocronTestCase


class TestServeCommand(HolocronTestCase):

    def setUp(self):
        self.fake_app = mock.Mock(conf=Conf({
            'paths': {
                'content': 'path/content',
                'theme': 'path/theme',
                'output': 'path/output',
            },

            'commands': {
                'serve': {
                    'host': '192.168.1.1',
                    'port': 42,
                },
            },
        }), spec=Holocron)
        self.fake_arguments = mock.Mock(conf='blog/_config.yml')

    def test_execute_runs_needed_parts(self):
        command = serve.Serve()
        command._watch = mock.Mock()
        command._serve = mock.Mock()

        command.execute(self.fake_app, self.fake_arguments)

        self.fake_app.run.assert_called_with()
        command._watch.assert_called_with(self.fake_app, self.fake_arguments)
        command._serve.assert_called_with(self.fake_app)

    @mock.patch('holocron.ext.commands.serve._ChangeWatcher')
    @mock.patch('holocron.ext.commands.serve.Observer')
    def test_watch_for_content_and_theme(self, fake_observer, fake_watcher):
        import holocron
        theme_path = os.path.join(
            os.path.abspath(os.path.dirname(holocron.__file__)), 'theme')

        command = serve.Serve()
        command._watch(self.fake_app, self.fake_arguments)

        fake_observer().schedule.assert_has_calls([
            mock.call(fake_watcher(), 'path/content', recursive=True),
            mock.call(fake_watcher(), theme_path, recursive=True),
        ], any_order=True)

        fake_watcher.assert_has_calls([
            mock.call(
                self.fake_app, ignore=[os.path.abspath('blog/_config.yml')]),
            mock.call(
                self.fake_app, ignore=[os.path.abspath('blog/_config.yml')]),
        ], any_order=True)

        fake_observer().start.assert_called_once_with()

    @mock.patch('holocron.ext.commands.serve.os.path.exists',
                side_effect=[True, False])
    @mock.patch('holocron.ext.commands.serve._ChangeWatcher')
    @mock.patch('holocron.ext.commands.serve.Observer')
    def test_watch_for_user_theme(self, fake_observer, fake_watcher, _):
        command = serve.Serve()
        command._watch(self.fake_app, self.fake_arguments)

        fake_observer().schedule.assert_any_call(
            fake_watcher(), 'path/theme', recursive=True)

        fake_watcher.assert_has_calls([
            mock.call(
                self.fake_app, ignore=[os.path.abspath('blog/_config.yml')]),
            mock.call(
                self.fake_app, ignore=[os.path.abspath('blog/_config.yml')]),
            mock.call(
                self.fake_app, ignore=[os.path.abspath('blog/_config.yml')]),
        ], any_order=True)

    @mock.patch('holocron.ext.commands.serve.os.path.exists',
                side_effect=[False, True])
    @mock.patch('holocron.ext.commands.serve._ChangeWatcher')
    @mock.patch('holocron.ext.commands.serve.Observer')
    def test_watch_for_user_conf(self, fake_observer, fake_watcher, _):
        command = serve.Serve()
        command._watch(self.fake_app, self.fake_arguments)

        fake_observer().schedule.assert_any_call(
            fake_watcher(), os.path.abspath('blog'))

        fake_watcher.assert_any_call(
            self.fake_app, recreate_app=True, watch_for=[
                os.path.abspath('blog/_config.yml'),
            ])

    @mock.patch('holocron.ext.commands.serve.HTTPServer')
    def test_serve(self, fake_httpserver):
        command = serve.Serve()
        command._serve(self.fake_app)

        address, handler = fake_httpserver.call_args[0]
        self.assertEqual(address, ('192.168.1.1', 42))
        self.assertEqual(handler.serve, 'path/output')

        fake_httpserver().serve_forever.assert_called_once_with()


class TestChangeWatcher(HolocronTestCase):

    def setUp(self):
        self.fake_app = mock.Mock(conf=Conf({
            'paths': {
                'output': 'path/output',
            },
        }), spec=Holocron)
        self.watcher = serve._ChangeWatcher(self.fake_app)

    def test_do_not_process_directories(self):
        self.watcher.process = mock.Mock()

        self.watcher.on_created(mock.Mock(is_directory=True, src_path='d'))
        self.watcher.on_modified(mock.Mock(is_directory=True, src_path='d'))

        self.assertEqual(self.watcher.process.call_count, 0)

    def test_process_not_directories(self):
        self.watcher.process = mock.Mock()

        self.watcher.on_created(mock.Mock(is_directory=False, src_path='f'))
        self.assertEqual(self.watcher.process.call_count, 1)

        self.watcher.on_modified(mock.Mock(is_directory=False, src_path='f'))
        self.assertEqual(self.watcher.process.call_count, 2)

    def test_process(self):
        self.watcher.process('a')
        self.fake_app.run.assert_called_with()

    def test_process_watch_for(self):
        self.watcher = serve._ChangeWatcher(self.fake_app, watch_for=['a'])

        self.watcher.process('x')
        self.assertEqual(self.fake_app.run.call_count, 0)

        self.watcher.process('a')
        self.fake_app.run.assert_called_with()

    def test_process_ignore(self):
        self.watcher = serve._ChangeWatcher(self.fake_app, ignore=['a'])

        self.watcher.process('a')
        self.assertEqual(self.fake_app.run.call_count, 0)

        self.watcher.process('x')
        self.fake_app.run.assert_called_with()

    def test_process_watch_for_and_ignore(self):
        self.watcher = serve._ChangeWatcher(
            self.fake_app, watch_for=['a', 'b'], ignore=['a'])

        self.watcher.process('a')
        self.assertEqual(self.fake_app.run.call_count, 0)

        self.watcher.process('b')
        self.fake_app.run.assert_called_with()

    def test_process_skips_output(self):
        self.watcher.process(os.path.abspath('path/output/doc.txt'))
        self.assertEqual(self.fake_app.run.call_count, 0)

    @mock.patch(
        'holocron.ext.commands.serve.app.create_app', return_value=mock.Mock())
    def test_recreate_app(self, _):
        self.watcher = serve._ChangeWatcher(self.fake_app, recreate_app=True)
        self.watcher.process('a')

        self.assertNotEqual(id(self.fake_app), id(self.watcher._app))

    @mock.patch(
        'holocron.ext.commands.serve.app.create_app', return_value=None)
    def test_recreate_app_failed(self, _):
        self.watcher = serve._ChangeWatcher(self.fake_app, recreate_app=True)
        self.watcher.process('a')

        self.assertEqual(id(self.fake_app), id(self.watcher._app))


class TestCreateHolocronHandler(HolocronTestCase):

    def test_generate_different_classes(self):
        a = serve.create_holocron_handler('a')
        b = serve.create_holocron_handler('b')

        self.assertNotEqual(id(a), id(b))
