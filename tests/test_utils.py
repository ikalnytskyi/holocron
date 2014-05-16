# coding: utf-8
"""
    tests.test_utils
    ~~~~~~~~~~~~~~~~

    Tests Holocron's utils.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
import copy
from holocron.utils import merge_dict

from tests import HolocronTestCase


class TestMergeDict(HolocronTestCase):
    def test_merge(self):
        a = {
            'root': {
                'map': {
                    'ukraine': 'heroes',
                    'russia': 'fascist',
                },

                'countries': ['ukraine', 'russia'],
            },
            'extra': False,
        }

        b = {
            'root': {
                'map': {
                    'ukraine': 'cossacks',
                    'france': 'musketeers',
                },

                'countries': ['ukraine', 'france'],
            },

            'extended': True,
        }

        self.assertDictEqual({
            'root': {
                'map': {
                    'ukraine': 'cossacks',
                    'russia': 'fascist',
                    'france': 'musketeers',
                },

                'countries': ['ukraine', 'france'],
            },

            'extra': False,
            'extended': True,
        }, merge_dict(a, b))

    def test_merge_few_dicts(self):
        dictionaries = [
            {
                'x': '42',
            },
            {
                'y': '13',
                'z': '00',
            },
            {
                'x': '04',
            },
        ]

        self.assertDictEqual({
            'x': '04',
            'y': '13',
            'z': '00',
        }, merge_dict(*dictionaries))

    def test_for_copies(self):
        dictionaries = [
            {
                'complex': {
                    'x': 42,
                },
                'x': '42',
            },
            {
                'y': '13',
                'z': '00',
            },
            {
                'x': '04',
            },
        ]
        copy_dictionaries = copy.deepcopy(dictionaries)

        result = merge_dict(*dictionaries)

        # check for no changes
        for x, y in zip(copy_dictionaries, dictionaries):
            self.assertDictEqual(x, y)

        # check for copies
        self.assertNotIn(id(result), [id(d) for d in dictionaries])
        self.assertNotEqual(id(result['complex']), id(dictionaries[0]['complex']))
