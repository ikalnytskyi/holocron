"""Sitemap processor test suite."""

import os
import datetime
import gzip

import pytest
import xmltodict

from holocron import app, content
from holocron.ext.processors import sitemap


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


@pytest.fixture(scope='function')
def run_processor():
    streams = []

    def run(*args, **kwargs):
        streams.append(sitemap.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


@pytest.mark.parametrize('filename', [
    's.html',       # test basic case works
    'ы.html',       # test for proper UTF-8 encoding/decoding
    'a&b.html',     # test escaping, otherwise XML is invalid
    'a<b.html',     # test escaping, otherwise XML is invalid
    'a>b.html',     # test escaping, otherwise XML is invalid
    'a"b.html',     # test escaping, otherwise XML is invalid
    "a'b.html",     # test escaping, otherwise XML is invalid
])
def test_document(testapp, run_processor, filename):
    """Sitemap processor has to work!"""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = run_processor(
        testapp,
        [
            _get_document(
                destination=os.path.join('posts', filename),
                updated=timepoint)
        ])

    document = next(stream)
    assert document['destination'] == os.path.join('posts', filename)
    assert document['updated'] == timepoint

    document = next(stream)
    assert document['source'] == 'virtual://sitemap'
    assert document['destination'] == 'sitemap.xml'
    assert xmltodict.parse(document['content'], 'UTF-8') == {
        'urlset': {
            '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'url': {
                'loc': 'http://obi-wan.jedi/posts/' + filename,
                'lastmod': '1970-01-01T00:00:00+00:00',
            }
        }
    }


def test_document_gzip(testapp, run_processor):
    """Sitemap processor has to respect gzip parameter."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = run_processor(
        testapp,
        [
            _get_document(
                destination=os.path.join('posts', '1.html'),
                updated=timepoint)
        ],
        gzip=True)

    document = next(stream)
    assert document['destination'] == os.path.join('posts', '1.html')
    assert document['updated'] == timepoint

    document = next(stream)
    assert document['source'] == 'virtual://sitemap'
    assert document['destination'] == 'sitemap.xml.gz'

    decompressed = gzip.decompress(document['content'])
    assert xmltodict.parse(decompressed, 'UTF-8') == {
        'urlset': {
            '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'url': {
                'loc': 'http://obi-wan.jedi/posts/1.html',
                'lastmod': '1970-01-01T00:00:00+00:00',
            }
        }
    }


@pytest.mark.parametrize('save_as', [
    os.path.join('posts', 'skywalker.luke'),
    os.path.join('yoda.jedi'),
])
def test_param_save_as(testapp, run_processor, save_as):
    """Sitemap processor has to respect save_as parameter."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            _get_document(
                destination=os.path.join('posts', '1.html'),
                updated=timepoint)
        ],
        save_as=save_as)

    document = next(stream)
    assert document['destination'] == os.path.join('posts', '1.html')
    assert document['updated'] == timepoint

    document = next(stream)
    assert document['source'] == 'virtual://sitemap'
    assert document['destination'] == save_as


@pytest.mark.parametrize('document_path, sitemap_path', [
    (os.path.join('1.html'), os.path.join('b', 'sitemap.xml')),
    (os.path.join('a', '1.html'), os.path.join('b', 'sitemap.xml')),
    (os.path.join('a', '1.html'), os.path.join('a', 'c', 'sitemap.xml')),
])
def test_param_save_as_unsupported(
        testapp, run_processor, document_path, sitemap_path):
    """Sitemap process has to check enlisted URLs for compatibility."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = run_processor(
        testapp,
        [
            _get_document(
                destination=document_path,
                updated=timepoint)
        ],
        save_as=sitemap_path)

    with pytest.raises(ValueError) as excinfo:
        next(stream)

    excinfo.match(
        "The location of a Sitemap file determines the set of URLs "
        "that can be included in that Sitemap. A Sitemap file located "
        "at .* can include any URLs starting with .* but can not "
        "include .*.")


def test_param_when(testapp, run_processor):
    """Sitemap processor has to ignore non-relevant documents."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = run_processor(
        testapp,
        [
            _get_document(
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html'),
                updated=timepoint),
            _get_document(
                source=os.path.join('pages', '2.md'),
                destination=os.path.join('pages', '2.html'),
                updated=timepoint),
            _get_document(
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html'),
                updated=timepoint),
            _get_document(
                source=os.path.join('pages', '4.md'),
                destination=os.path.join('pages', '4.html'),
                updated=timepoint),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    for i, document in zip(range(4), stream):
        assert document['source'].endswith('%d.md' % (i + 1))
        assert document['destination'].endswith('%d.html' % (i + 1))
        assert document['updated'] == timepoint

    document = next(stream)
    assert document['source'] == 'virtual://sitemap'
    assert document['destination'] == 'sitemap.xml'
    assert xmltodict.parse(document['content'], 'UTF-8') == {
        'urlset': {
            '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'url': [
                {
                    'loc': 'http://obi-wan.jedi/posts/1.html',
                    'lastmod': '1970-01-01T00:00:00+00:00',
                },
                {
                    'loc': 'http://obi-wan.jedi/posts/3.html',
                    'lastmod': '1970-01-01T00:00:00+00:00',
                },
            ]
        }
    }


@pytest.mark.parametrize('params, error', [
    ({'when': 42}, 'when: unsupported value'),
    ({'gzip': 'true'}, "gzip: 'true' should be instance of 'bool'"),
    ({'save_as': 42}, "save_as: 42 should be instance of 'str'"),
])
def test_param_bad_value(testapp, params, error):
    """Sitemap processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(sitemap.process(testapp, [], **params))
