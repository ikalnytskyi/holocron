# coding: utf-8
"""
    tests.ext.commands.test_serve
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests Serve command.

    :copyright: (c) 2015 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os

import mock
from dooku.conf import Conf

from holocron.app import Holocron
from holocron.ext.commands import serve

from tests import HolocronTestCase


class TestServeCommand(HolocronTestCase):

    def setUp(self):
        self.fake_app = mock.Mock(
            conf=Conf({
                'paths': {
                    'content': 'path/content',
                    'output': 'path/output',
                },

                'commands': {
                    'serve': {
                        'host': '192.168.1.1',
                        'port': 42,
                        'wakeup': 13,
                    },
                },
            }),
            _themes=[
                'theme_a',
                'theme_b',
            ],
            spec=Holocron)

        self.fake_arguments = mock.Mock(conf='blog/_config.yml')
        self.fake_builder = mock.Mock(_app=self.fake_app, spec=serve._Builder)

    @mock.patch('holocron.ext.commands.serve._Builder')
    def test_execute_runs_needed_parts(self, fake_builder):
        command = serve.Serve()
        command._watch = mock.Mock()
        command._serve = mock.Mock()

        command.execute(self.fake_app, self.fake_arguments)

        # test created builder
        fake_builder.assert_called_once_with(
            self.fake_app, 'blog/_config.yml', 13)

        # test serve executed with right args
        self.fake_app.run.assert_called_with()
        command._watch.assert_called_with(
            self.fake_app, self.fake_arguments, fake_builder())
        command._serve.assert_called_with(self.fake_app)

        # test deamons
        fake_builder().start.assert_called_once_with()
        command._watch().start.assert_called_once_with()
        command._serve().serve_forever.assert_called_once_with()

    @mock.patch('holocron.ext.commands.serve.os.path.exists',
                side_effect=[
                    True,   # theme_a
                    True,   # theme_b
                    False,  # blog/config.yml
                ])
    @mock.patch('holocron.ext.commands.serve._ChangeWatcher')
    @mock.patch('holocron.ext.commands.serve.Observer')
    def test_watch_for_content_and_themes(
            self, fake_observer, fake_watcher, _):
        command = serve.Serve()
        command._watch(self.fake_app, self.fake_arguments, self.fake_builder)

        fake_observer().schedule.assert_has_calls([
            mock.call(fake_watcher(), 'path/content', recursive=True),
            mock.call(fake_watcher(), 'theme_a', recursive=True),
            mock.call(fake_watcher(), 'theme_b', recursive=True),
        ], any_order=True)

        fake_watcher.assert_has_calls([
            mock.call(
                self.fake_builder, ignore=[
                    os.path.abspath('blog/_config.yml')]),
            mock.call(
                self.fake_builder, ignore=[
                    os.path.abspath('blog/_config.yml')]),
        ], any_order=True)

    @mock.patch('holocron.ext.commands.serve.os.path.exists',
                return_value=True)
    @mock.patch('holocron.ext.commands.serve._ChangeWatcher')
    @mock.patch('holocron.ext.commands.serve.Observer')
    def test_watch_for_user_conf(self, fake_observer, fake_watcher, _):
        command = serve.Serve()
        command._watch(self.fake_app, self.fake_arguments, self.fake_builder)

        fake_observer().schedule.assert_any_call(
            fake_watcher(), os.path.abspath('blog'))

        fake_watcher.assert_any_call(
            self.fake_builder, recreate_app=True, watch_for=[
                os.path.abspath('blog/_config.yml'),
            ])

    @mock.patch('holocron.ext.commands.serve.HTTPServer')
    def test_serve(self, fake_httpserver):
        command = serve.Serve()
        command._serve(self.fake_app)

        address, handler = fake_httpserver.call_args[0]
        self.assertEqual(address, ('192.168.1.1', 42))
        self.assertEqual(handler.serve, 'path/output')


class TestChangeWatcher(HolocronTestCase):

    def setUp(self):
        self.fake_app = mock.Mock(conf=Conf({
            'paths': {
                'output': 'path/output',
            },
        }), spec=Holocron)
        self.fake_builder = mock.Mock(_app=self.fake_app, spec=serve._Builder)
        self.watcher = serve._ChangeWatcher(self.fake_builder)

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
        self.fake_builder.rebuild.assert_called_once_with()

    def test_process_watch_for(self):
        self.watcher = serve._ChangeWatcher(self.fake_builder, watch_for=['a'])

        self.watcher.process('x')
        self.assertEqual(self.fake_builder.rebuild.call_count, 0)

        self.watcher.process('a')
        self.fake_builder.rebuild.assert_called_once_with()

    def test_process_ignore(self):
        self.watcher = serve._ChangeWatcher(self.fake_builder, ignore=['a'])

        self.watcher.process('a')
        self.assertEqual(self.fake_builder.rebuild.call_count, 0)

        self.watcher.process('x')
        self.fake_builder.rebuild.assert_called_once_with()

    def test_process_watch_for_and_ignore(self):
        self.watcher = serve._ChangeWatcher(
            self.fake_builder, watch_for=['a', 'b'], ignore=['a'])

        self.watcher.process('a')
        self.assertEqual(self.fake_builder.rebuild.call_count, 0)

        self.watcher.process('b')
        self.fake_builder.rebuild.assert_called_once_with()

    def test_process_skips_output(self):
        self.watcher.process(os.path.abspath('path/output/doc.txt'))
        self.assertEqual(self.fake_builder.rebuild.call_count, 0)

    def test_recreate_app(self):
        self.watcher = serve._ChangeWatcher(
            self.fake_builder, recreate_app=True)
        self.watcher.process('a')

        self.fake_builder.recreate_app.assert_called_once_with()


class TestBuilder(HolocronTestCase):

    def setUp(self):
        self.fake_app = mock.Mock(spec=Holocron)
        self.builder = serve._Builder(self.fake_app, 'blog/_config.yml',  0)

    def test_recreate_app(self):
        self.assertIs(self.builder._app, self.fake_app)

        with mock.patch.object(
                type(self.builder), '_quit',
                mock.PropertyMock(side_effect=[False, True]),
                create=True):
            self.builder.recreate_app()
            self.builder.run()

        self.assertIsNot(self.builder._app, self.fake_app)

    def test_do_not_recreate_twice(self):
        self.test_recreate_app()

        prev_app = self.builder._app
        with mock.patch.object(
                type(self.builder), '_quit',
                mock.PropertyMock(side_effect=[False, True]),
                create=True):
            self.builder.run()

        self.assertIs(self.builder._app, prev_app)

    @mock.patch(
        'holocron.ext.commands.serve.app.create_app', return_value=None)
    def test_use_prev_app_if_recreate_has_been_failed(self, _):
        self.assertIs(self.builder._app, self.fake_app)

        with mock.patch.object(
                type(self.builder), '_quit',
                mock.PropertyMock(side_effect=[False, True]),
                create=True):
            self.builder.recreate_app()
            self.builder.run()

        self.assertIs(self.builder._app, self.fake_app)

    def test_rebuild(self):
        with mock.patch.object(
                type(self.builder), '_quit',
                mock.PropertyMock(side_effect=[False, False, True]),
                create=True):
            self.builder.rebuild()
            self.builder.run()

        self.fake_app.run.assert_called_once_with()

    @mock.patch('holocron.ext.commands.serve.time.sleep')
    def test_sleep(self, msleep):
        self.builder = serve._Builder(self.fake_app, 'blog/_config.yml',  42)

        with mock.patch.object(
                type(self.builder), '_quit',
                mock.PropertyMock(side_effect=[False, True]),
                create=True):
            self.builder.run()

        msleep.assert_called_once_with(42)

    def test_shutdown(self):
        self.assertFalse(self.builder._quit)
        self.builder.shutdown()
        self.assertTrue(self.builder._quit)


class TestCreateHolocronHandler(HolocronTestCase):

    def test_generate_different_classes(self):
        a = serve._create_holocron_handler('a')
        b = serve._create_holocron_handler('b')

        self.assertNotEqual(id(a), id(b))
