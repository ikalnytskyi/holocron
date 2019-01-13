"""Sitemap processor test suite."""

import os
import datetime
import gzip
import unittest.mock

import pytest
import xmltodict

from holocron import app, content
from holocron.ext.processors import sitemap


class _pytest_xmlasdict:
    """Assert that a given XML has the same semantic meaning."""

    def __init__(self, expected, ungzip=False):
        self._expected = expected
        self._ungzip = ungzip

    def __eq__(self, actual):
        if self._ungzip:
            actual = gzip.decompress(actual)
        actual = xmltodict.parse(actual, 'UTF-8')
        return self._expected == actual

    def __repr__(self):
        return self._expected


def _get_document(**kwargs):
    document = content.Document(app.Holocron({}, metadata={
        'url': 'http://obi-wan.jedi',
    }))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({}, metadata={
        'url': 'http://obi-wan.jedi',
    })
    return instance


@pytest.mark.parametrize('filename', [
    's.html',       # test basic case works
    'ы.html',       # test for proper UTF-8 encoding/decoding
    'a&b.html',     # test escaping, otherwise XML is invalid
    'a<b.html',     # test escaping, otherwise XML is invalid
    'a>b.html',     # test escaping, otherwise XML is invalid
    'a"b.html',     # test escaping, otherwise XML is invalid
    "a'b.html",     # test escaping, otherwise XML is invalid
])
def test_item(testapp, filename):
    """Sitemap processor has to work!"""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            _get_document(destination=filename, updated=timepoint),
        ])

    assert next(stream) == \
        {
            'destination': filename,
            'updated': timepoint,
        }

    assert next(stream) == \
        {
            'source': 'sitemap://sitemap.xml',
            'destination': 'sitemap.xml',
            'content': _pytest_xmlasdict({
                'urlset': {
                    '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                    'url': {
                        'loc': 'http://obi-wan.jedi/' + filename,
                        'lastmod': '1970-01-01T00:00:00+00:00',
                    },
                },
            }),
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('amount', [2, 5, 10])
def test_item_many(testapp, amount):
    """Sitemap processor has to work with stream."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            _get_document(destination=str(i), updated=timepoint)
            for i in range(amount)
        ])

    for i in range(amount):
        assert next(stream) == \
            {
                'destination': str(i),
                'updated': timepoint,
            }

    assert next(stream) == \
        {
            'source': 'sitemap://sitemap.xml',
            'destination': 'sitemap.xml',
            'content': _pytest_xmlasdict({
                'urlset': {
                    '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                    'url': [
                        {
                            'loc': 'http://obi-wan.jedi/%d' % i,
                            'lastmod': '1970-01-01T00:00:00+00:00',
                        }
                        for i in range(amount)
                    ],
                },
            }),
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_gzip(testapp):
    """Sitemap processor has to respect gzip parameter."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            _get_document(destination='1.html', updated=timepoint),
        ],
        gzip=True)

    assert next(stream) == \
        {
            'destination': '1.html',
            'updated': timepoint,
        }

    assert next(stream) == \
        {
            'source': 'sitemap://sitemap.xml.gz',
            'destination': 'sitemap.xml.gz',
            'content': _pytest_xmlasdict({
                'urlset': {
                    '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                    'url': {
                        'loc': 'http://obi-wan.jedi/1.html',
                        'lastmod': '1970-01-01T00:00:00+00:00',
                    },
                },
            }, ungzip=True),
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('save_as', [
    os.path.join('posts', 'skywalker.luke'),
    os.path.join('yoda.jedi'),
])
def test_param_save_as(testapp, save_as):
    """Sitemap processor has to respect save_as parameter."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            _get_document(
                destination=os.path.join('posts', '1.html'),
                updated=timepoint),
        ],
        save_as=save_as)

    assert next(stream) == \
        {
            'destination': os.path.join('posts', '1.html'),
            'updated': timepoint,
        }

    assert next(stream) == \
        {
            'source': 'sitemap://%s' % save_as,
            'destination': save_as,
            'content': unittest.mock.ANY,
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('document_path, sitemap_path', [
    (os.path.join('1.html'), os.path.join('b', 'sitemap.xml')),
    (os.path.join('a', '1.html'), os.path.join('b', 'sitemap.xml')),
    (os.path.join('a', '1.html'), os.path.join('a', 'c', 'sitemap.xml')),
    (os.path.join('ab', '1.html'), os.path.join('a', 'sitemap.xml')),
])
def test_param_save_as_unsupported(testapp, document_path, sitemap_path):
    """Sitemap process has to check enlisted URLs for compatibility."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            _get_document(destination=document_path, updated=timepoint),
        ],
        save_as=sitemap_path)

    with pytest.raises(ValueError) as excinfo:
        next(stream)

    excinfo.match(
        "The location of a Sitemap file determines the set of URLs "
        "that can be included in that Sitemap. A Sitemap file located "
        "at .* can include any URLs starting with .* but can not "
        "include .*.")

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('pretty, lines', (
    (False, 1),
    (True, 7),
))
def test_param_pretty(testapp, pretty, lines):
    """Sitemap processor has to respect pretty parameter."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            _get_document(destination='1.html', updated=timepoint),
        ],
        pretty=pretty)

    assert next(stream) == \
        {
            'destination': '1.html',
            'updated': timepoint,
        }

    item = next(stream)
    assert item == \
        {
            'source': 'sitemap://sitemap.xml',
            'destination': 'sitemap.xml',
            'content': unittest.mock.ANY,
        }
    assert len(item['content'].splitlines()) == lines

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('params, error', [
    ({'gzip': 'true'}, "gzip: 'true' should be instance of 'bool'"),
    ({'save_as': 42}, "save_as: 42 should be instance of 'str'"),
])
def test_param_bad_value(testapp, params, error):
    """Sitemap processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(sitemap.process(testapp, [], **params))
