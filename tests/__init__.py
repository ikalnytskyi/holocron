"""
    tests
    ~~~~~

    Tests Holocron itself.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import unittest
from holocron.ext import abc


class FakeConverter(abc.Converter):
    """
    Fake converter class that converts *.fake files into HTML. It's used by
    some tests where we need to check rendered HTML code.
    """
    extensions = ['.fake']

    def to_html(self, text):
        return {}, 'html_text'


class HolocronTestCase(unittest.TestCase):
    """
    Base class for all the tests that Holocron uses.
    """
