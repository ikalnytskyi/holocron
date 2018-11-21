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


@pytest.mark.parametrize('filename', [
    's.html',       # test basic case works
    'ы.html',       # test for proper UTF-8 encoding/decoding
    'a&b.html',     # test escaping, otherwise XML is invalid
    'a<b.html',     # test escaping, otherwise XML is invalid
    'a>b.html',     # test escaping, otherwise XML is invalid
    'a"b.html',     # test escaping, otherwise XML is invalid
    "a'b.html",     # test escaping, otherwise XML is invalid
])
def test_document(testapp, filename):
    """Sitemap processor has to work!"""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    documents = sitemap.process(
        testapp,
        [
            _get_document(
                destination=os.path.join('posts', filename),
                updated=timepoint)
        ])

    assert documents[0]['destination'] == os.path.join('posts', filename)
    assert documents[0]['updated'] == timepoint

    assert documents[1]['source'] == 'virtual://sitemap'
    assert documents[1]['destination'] == 'sitemap.xml'
    assert xmltodict.parse(documents[1]['content'], 'UTF-8') == {
        'urlset': {
            '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'url': {
                'loc': 'http://obi-wan.jedi/posts/' + filename,
                'lastmod': '1970-01-01T00:00:00+00:00',
            }
        }
    }


def test_document_options(testapp):
    """Sitemap processor has to respect custom options."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    documents = sitemap.process(
        testapp,
        [
            _get_document(
                destination=os.path.join('posts', '1.html'),
                updated=timepoint)
        ],
        save_as='posts/skywalker.luke',
        gzip=True)

    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['updated'] == timepoint

    assert documents[1]['source'] == 'virtual://sitemap'
    assert documents[1]['destination'] == 'posts/skywalker.luke.gz'

    decompressed = gzip.decompress(documents[1]['content'])
    assert xmltodict.parse(decompressed, 'UTF-8') == {
        'urlset': {
            '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'url': {
                'loc': 'http://obi-wan.jedi/posts/1.html',
                'lastmod': '1970-01-01T00:00:00+00:00',
            }
        }
    }


@pytest.mark.parametrize('document_path, sitemap_path', [
    (os.path.join('1.html'), os.path.join('b', 'sitemap.xml')),
    (os.path.join('a', '1.html'), os.path.join('b', 'sitemap.xml')),
    (os.path.join('a', '1.html'), os.path.join('a', 'c', 'sitemap.xml')),
])
def test_document_sitemap_location(testapp, document_path, sitemap_path):
    """Sitemap process has to check enlisted URLs for compatibility."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)

    with pytest.raises(ValueError) as excinfo:
        sitemap.process(
            testapp,
            [
                _get_document(
                    destination=document_path,
                    updated=timepoint)
            ],
            save_as=sitemap_path)

    excinfo.match(
        "The location of a Sitemap file determines the set of URLs "
        "that can be included in that Sitemap. A Sitemap file located "
        "at .* can include any URLs starting with .* but can not "
        "include .*.")


def test_documents(testapp):
    """Sitemap processor has to ignore non-relevant documents."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    documents = sitemap.process(
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

    # Ensure original documents are preserved in the processor's output.
    for i, document in enumerate(documents[:-1]):
        assert document['source'].endswith('%d.md' % (i + 1))

    # Ensure a virtual sitemap document contains proper values.
    assert documents[-1]['source'] == 'virtual://sitemap'
    assert documents[-1]['destination'] == 'sitemap.xml'
    assert xmltodict.parse(documents[-1]['content'], 'UTF-8') == {
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


def test_parameters_jsonref(testapp):
    testapp.conf.update({
        'extra': {'compression': True},
        'save_sitemap_as': 'foo.xml',
    })

    documents = sitemap.process(
        testapp,
        [],
        gzip={'$ref': ':application:#/extra/compression'},
        save_as={'$ref': ':application:#/save_sitemap_as'})

    assert len(documents) == 1
    assert documents[0]['destination'] == 'foo.xml.gz'


@pytest.mark.parametrize('options, error', [
    ({'when': 42}, 'when: unsupported value'),
    ({'gzip': 'true'}, "gzip: 'true' should be instance of 'bool'"),
    ({'save_as': 42}, "save_as: 42 should be instance of 'str'"),
])
def test_parameters_schema(testapp, options, error):
    with pytest.raises(ValueError, match=error):
        sitemap.process(testapp, [], **options)


@pytest.mark.parametrize('option_name, option_value, error', [
    ('when', 42, 'when: unsupported value'),
    ('gzip', 'true', "gzip: 'true' should be instance of 'bool'"),
    ('save_as', 42, "save_as: 42 should be instance of 'str'"),
])
def test_parameters_jsonref_schema(testapp, option_name, option_value, error):
    testapp.conf.update({'test': {option_name: option_value}})

    with pytest.raises(ValueError, match=error):
        sitemap.process(
            testapp,
            [],
            **{option_name: {'$ref': ':application:#/test/%s' % option_name}})
