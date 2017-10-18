"""Sitemap processor test suite."""

import os
import datetime

import pytest
import xmltodict

from holocron import app, content
from holocron.ext.processors import sitemap


def _get_document(cls=content.Page, **kwargs):
    document = cls(app.Holocron({}))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})
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
                updated_local=timepoint)
        ])

    assert documents[0]['destination'] == os.path.join('posts', filename)
    assert documents[0]['updated_local'] == timepoint

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
                updated_local=timepoint)
        ],
        save_as='masters/skywalker.luke')

    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['updated_local'] == timepoint

    assert documents[1]['source'] == 'virtual://sitemap'
    assert documents[1]['destination'] == 'masters/skywalker.luke'
    assert xmltodict.parse(documents[1]['content'], 'UTF-8') == {
        'urlset': {
            '@xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'url': {
                'loc': 'http://obi-wan.jedi/posts/1.html',
                'lastmod': '1970-01-01T00:00:00+00:00',
            }
        }
    }


def test_documents(testapp):
    """Sitemap processor has to ignore non-relevant documents."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    documents = sitemap.process(
        testapp,
        [
            _get_document(
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html'),
                updated_local=timepoint),
            _get_document(
                source=os.path.join('pages', '2.md'),
                destination=os.path.join('pages', '2.html'),
                updated_local=timepoint),
            _get_document(
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html'),
                updated_local=timepoint),
            _get_document(
                source=os.path.join('pages', '4.md'),
                destination=os.path.join('pages', '4.html'),
                updated_local=timepoint),
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
