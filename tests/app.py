# coding: utf-8
"""
    tests.app
    ~~~~~~~~~

    Tests the Holocron instance.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
from holocron.app import Holocron
from holocron.ext import Converter

from tests import HolocronTestCase


class HolocronCase(HolocronTestCase):
    def setUp(self):
        self.app = Holocron()

    def test_register_converter(self):
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
