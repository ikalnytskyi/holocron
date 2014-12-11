# coding: utf-8
"""
    tests.test_app
    ~~~~~~~~~~~~~~

    Tests the Holocron instance.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""
import copy
from unittest import mock

from holocron.app import Holocron
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
        self.assertIsInstance(self.app._generators[TestGenerator], TestGenerator)

        # test double registering protection
        generator_id = id(self.app._generators[TestGenerator])
        self.app.register_generator(TestGenerator)
        self.assertEqual(generator_id, id(self.app._generators[TestGenerator]))

        # test force re-registering
        generator_id = id(self.app._generators[TestGenerator])
        self.app.register_generator(TestGenerator, _force=True)
        self.assertNotEqual(generator_id, id(self.app._generators[TestGenerator]))

    @mock.patch('holocron.app.iterfiles')
    def test_run(self, iterfiles):
        """
        Tests build process.
        """
        iterfiles.return_value = ['doc_a', 'doc_b', 'doc_c']
        self.app.document_class = mock.Mock()
        self.app._copy_theme = mock.Mock()
        self.app._generators = {
            mock.Mock(): mock.Mock(),
            mock.Mock(): mock.Mock(),
        }

        self.app.run()

        # check iterfiles call signature
        iterfiles.assert_called_with(
            self.app.conf['paths']['content'], '[!_.]*', True)

        self.app.document_class.assert_has_calls([
            # check that document class was used to generate class instances
            mock.call('doc_a', self.app),
            # check that document instances were built
            mock.call().build(),
            mock.call('doc_b', self.app),
            mock.call().build(),
            mock.call('doc_c', self.app),
            mock.call().build(),
        ])
        self.assertEqual(self.app.document_class.call_count, 3)

        # check that generators was used
        for _, generator in self.app._generators.items():
            self.assertEqual(generator.generate.call_count, 1)

        # check that _copy_theme was called
        self.app._copy_theme.assert_called_once_with()


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
