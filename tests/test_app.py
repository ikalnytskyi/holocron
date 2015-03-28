# coding: utf-8
"""
    tests.test_app
    ~~~~~~~~~~~~~~

    Tests the Holocron instance.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import copy
from unittest import mock

import holocron
from holocron.app import Holocron, create_app
from holocron.ext.abc import Converter, Generator

from tests import HolocronTestCase


class TestHolocron(HolocronTestCase):

    def setUp(self):
        """
        Creates a pure holocron instance withot any extension stuff for
        each testcase.
        """
        self.app = Holocron({
            'converters': {
                'enabled': [],
            },

            'generators': {
                'enabled': [],
            },
        })

    def test_user_settings(self):
        """
        Tests creating an instance with custom settings: check for settings
        overriding.
        """
        app = Holocron({
            'sitename': 'Luke Skywalker',
            'paths': {
                'content': 'path/to/content',
            },
        })

        conf = copy.deepcopy(app.default_conf)
        conf['sitename'] = 'Luke Skywalker'
        conf['paths']['content'] = 'path/to/content'

        self.assertEqual(app.conf, conf)

    def test_register_converter(self):
        """
        Tests converter registration process.
        """
        def to_html(self, text):
            return {}, text

        # create converter class
        TestConverter = type('TestConverter', (Converter,), {
            'extensions': ['.tst', '.test'],
            'to_html': to_html,
        })

        # test registration process
        self.assertEqual(len(self.app._converters), 0)
        self.app.register_converter(TestConverter)
        self.assertEqual(len(self.app._converters), 2)

        self.assertIn('.tst', self.app._converters)
        self.assertIn('.test', self.app._converters)

        self.assertIsInstance(self.app._converters['.tst'], TestConverter)

        # test double registering protection
        converter_id = id(self.app._converters['.tst'])
        self.app.register_converter(TestConverter)
        self.assertEqual(converter_id, id(self.app._converters['.tst']))

        # test force re-registering
        converter_id = id(self.app._converters['.tst'])
        self.app.register_converter(TestConverter, _force=True)
        self.assertNotEqual(converter_id, id(self.app._converters['.tst']))

    def test_register_generator(self):
        """
        Tests generator registration process.
        """
        def generate(self, text):
            return

        # create converter class
        TestGenerator = type('TestGenerator', (Generator, ), {
            'generate': generate,
        })

        # test registration process
        self.assertEqual(len(self.app._generators), 0)
        self.app.register_generator(TestGenerator)
        self.assertEqual(len(self.app._generators), 1)

        self.assertIn(TestGenerator, self.app._generators)
        self.assertIsInstance(
            self.app._generators[TestGenerator], TestGenerator)

        # test double registering protection
        generator_id = id(self.app._generators[TestGenerator])
        self.app.register_generator(TestGenerator)
        self.assertEqual(generator_id, id(self.app._generators[TestGenerator]))

        # test force re-registering
        generator_id = id(self.app._generators[TestGenerator])
        self.app.register_generator(TestGenerator, _force=True)
        self.assertNotEqual(
            generator_id, id(self.app._generators[TestGenerator]))

    @mock.patch('holocron.app.mkdir')
    @mock.patch('holocron.app.iterfiles')
    def test_run(self, iterfiles, mkdir):
        """
        Tests build process.
        """
        iterfiles.return_value = ['doc_a', 'doc_b', 'doc_c']
        self.app.__class__.document_factory = mock.Mock()
        self.app._copy_theme = mock.Mock()
        self.app._generators = {
            mock.Mock(): mock.Mock(),
            mock.Mock(): mock.Mock(),
        }

        self.app.run()

        # check iterfiles call signature
        iterfiles.assert_called_with(
            self.app.conf['paths']['content'], '[!_.]*', True)

        # check mkdir create ourpur dir
        mkdir.assert_called_with(self.app.conf['paths.output'])

        # check that generators was used
        for _, generator in self.app._generators.items():
            self.assertEqual(generator.generate.call_count, 1)

        self.app.__class__.document_factory.assert_has_calls([
            # check that document class was used to generate class instances
            mock.call('doc_a', self.app),
            mock.call('doc_b', self.app),
            mock.call('doc_c', self.app),
            # check that document instances were built
            mock.call().build(),
            mock.call().build(),
            mock.call().build(),
        ])
        self.assertEqual(self.app.__class__.document_factory.call_count, 3)

        # check that _copy_theme was called
        self.app._copy_theme.assert_called_once_with()

    @mock.patch('holocron.app.shutil.os.path.exists', return_value=False)
    @mock.patch('holocron.app.shutil.rmtree')
    @mock.patch('holocron.app.shutil.copytree')
    def test_copy_base_theme(self, mcopytree, mrmtree, _):
        output = os.path.join(self.app.conf['paths.output'], 'static')
        theme = os.path.join(
            os.path.dirname(holocron.__file__), 'theme', 'static')

        self.app._copy_theme()

        mrmtree.assert_called_with(output, ignore_errors=True)
        mcopytree.assert_called_with(theme, output)

    @mock.patch('holocron.app.shutil.os.path.exists', return_value=True)
    @mock.patch('holocron.app.shutil.rmtree')
    @mock.patch('holocron.app.shutil.copytree')
    def test_copy_user_theme(self, mcopytree, mrmtree, _):
        output = os.path.join(self.app.conf['paths.output'], 'static')
        theme = os.path.join(self.app.conf['paths.theme'], 'static')

        self.app._copy_theme()

        mrmtree.assert_called_with(output, ignore_errors=True)
        mcopytree.assert_called_with(theme, output)


class TestHolocronDefaults(HolocronTestCase):

    def setUp(self):
        """
        Creates a default Holocron instance for each testcase.
        """
        self.app = Holocron()

    def test_registered_converters(self):
        """
        Tests that default converters are registered.
        """
        enabled_converters = set(self.app.conf['converters']['enabled'])

        registered_converters = set()
        for _, converter in self.app._converters.items():
            registered_converters.add(converter)

        self.assertEqual(len(registered_converters), len(enabled_converters))

    def test_registered_generators(self):
        """
        Tests that default generators are registered.
        """
        enabled_generators = set(self.app.conf['generators']['enabled'])

        registered_generators = set()
        for generator, _ in self.app._generators.items():
            registered_generators.add(generator)

        self.assertEqual(len(registered_generators), len(enabled_generators))


class TestCreateApp(HolocronTestCase):

    def _create_app(self, conf_raw=None, side_effect=None):
        """
        Creates an application instance with mocked settings file. All
        arguments will be passed into mock_open.
        """
        mopen = mock.mock_open(read_data=conf_raw)
        mopen.side_effect = side_effect if side_effect else None

        with mock.patch('holocron.app.open', mopen, create=True):
            return create_app('_config.yml')

    def test_default(self):
        """
        The create_app with no arguments has to create a Holocron instance
        with default settings.
        """
        app = create_app()

        self.assertIsNotNone(app)
        self.assertEqual(app.conf, Holocron.default_conf)

    def test_custom_conf(self):
        """
        Tests that custom conf overrides default one.
        """
        conf_raw = [
            'sitename: MySite',
            'author: User',
        ]
        app = self._create_app(conf_raw='\n'.join(conf_raw))

        self.assertIsNotNone(app)
        self.assertEqual(app.conf['sitename'], 'MySite')
        self.assertEqual(app.conf['author'], 'User')

    def test_illformed_conf(self):
        """
        Tests that in case of ill-formed conf we can't create app instance.
        """
        conf_raw = [
            'error',
            'sitename: MySite',
        ]
        app = self._create_app(conf_raw='\n'.join(conf_raw))

        self.assertIsNone(app)

    def test_filenotfounderror(self):
        """
        Tests that we create application with default settings in case user's
        settings wasn't found.
        """
        app = self._create_app(side_effect=FileNotFoundError)

        self.assertIsNotNone(app)
        self.assertEqual(app.conf, Holocron.default_conf)

    def test_permissionerror(self):
        """
        Tests that we create application with default settings in case we
        don't have permissions to read user settings.
        """
        app = self._create_app(side_effect=PermissionError)

        self.assertIsNotNone(app)
        self.assertEqual(app.conf, Holocron.default_conf)

    def test_isadirectoryerror(self):
        """
        Tests that we can't create app instance if we pass a directory as
        settings file.
        """
        app = self._create_app(side_effect=IsADirectoryError)

        self.assertIsNone(app)
