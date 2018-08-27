"""Atom processor test suite."""

import os
import datetime

import feedparser
import mock
import pytest

from holocron import app, content
from holocron.ext.processors import atom


def _get_document(**kwargs):
    document = content.Document(app.Holocron({}))
    document['author'] = 'Obi-Wan Kenobi'
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})
    return instance


def test_document(testapp):
    """Atom processor has to work!"""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    documents = atom.process(
        testapp,
        [
            _get_document(
                title='Essay',
                content='the way of the Force',
                destination=os.path.join('posts', '1.html'),
                updated=timepoint,
                published=datetime.date(2017, 9, 25)),
        ])

    assert documents[0]['content'] == 'the way of the Force'
    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['updated'] == timepoint
    assert documents[0]['published'] == datetime.date(2017, 9, 25)

    assert documents[1]['source'] == 'virtual://feed'
    assert documents[1]['destination'] == 'atom.xml'
    assert feedparser.parse(documents[1]['content']) == {
        'bozo': 0,
        'encoding': 'utf-8',
        'entries': [
            {
                'author': 'Obi-Wan Kenobi',
                'author_detail': {'name': 'Obi-Wan Kenobi'},
                'authors': [{'name': 'Obi-Wan Kenobi'}],
                'content': [
                    {
                        'base': '',
                        'language': None,
                        'type': 'text/html',
                        'value': 'the way of the Force',
                    }
                ],
                'guidislink': False,
                'id': 'http://obi-wan.jedi/posts/1.html',
                'link': 'http://obi-wan.jedi/posts/1.html',
                'links': [
                    {
                        'href': 'http://obi-wan.jedi/posts/1.html',
                        'rel': 'alternate',
                        'type': 'text/html',
                    },
                ],
                'published': '2017-09-25',
                'published_parsed': mock.ANY,
                'summary': 'the way of the Force',
                'title': 'Essay',
                'title_detail': {
                    'base': '',
                    'language': None,
                    'type': 'text/plain',
                    'value': 'Essay',
                },
                'updated': '1970-01-01T00:00:00+00:00',
                'updated_parsed': mock.ANY,
            },
        ],
        'feed': {
            'generator': 'Holocron',
            'generator_detail': {
                'name': 'Holocron',
                'href': 'https://holocron.readthedocs.io',
                'version': '0.4.0',
            },
            'guidislink': True,
            'id': 'http://obi-wan.jedi',
            'link': 'http://obi-wan.jedi',
            'links': [
                {
                    'href': 'http://obi-wan.jedi/atom.xml',
                    'rel': 'self',
                    'type': 'application/atom+xml',
                },
                {
                    'href': 'http://obi-wan.jedi',
                    'rel': 'alternate',
                    'type': 'text/html',
                },
            ],
            'title': "Kenobi's Thoughts",
            'title_detail': {
                'base': '',
                'language': None,
                'type': 'text/plain',
                'value': "Kenobi's Thoughts",
            },
            'updated': mock.ANY,
            'updated_parsed': mock.ANY,
        },
        'namespaces': {'': 'http://www.w3.org/2005/Atom'},
        'version': 'atom10',
    }


def test_document_options(testapp):
    """Atom processor has to respect custom options."""

    encoding = 'cp1251'
    save_as = 'atom.xml'
    posts_number = 1

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    documents = atom.process(
        testapp,
        [
            _get_document(
                title='Essay #%d' % i,
                content='the way of the Force',
                destination=os.path.join('posts', '%d.html' % i),
                updated=timepoint,
                published=datetime.date(2017, 9, i + 1))
            for i in range(10)
        ],
        encoding=encoding,
        save_as=save_as,
        posts_number=posts_number)

    # Ensure original documents are preserved in the processor's output.
    for i, document in enumerate(documents[:-1]):
        assert document['content'] == 'the way of the Force'
        assert document['destination'] == os.path.join('posts', '%d.html' % i)
        assert document['updated'] == timepoint
        assert document['published'] == datetime.date(2017, 9, i + 1)

    # Ensure a virtual feed document contains proper values.
    assert documents[-1]['source'] == 'virtual://feed'
    assert documents[-1]['destination'] == save_as
    assert feedparser.parse(documents[-1]['content']) == {
        'bozo': 0,
        'encoding': encoding,
        'entries': [
            {
                'author': 'Obi-Wan Kenobi',
                'author_detail': {'name': 'Obi-Wan Kenobi'},
                'authors': [{'name': 'Obi-Wan Kenobi'}],
                'content': [
                    {
                        'base': '',
                        'language': None,
                        'type': 'text/html',
                        'value': 'the way of the Force',
                    }
                ],
                'guidislink': False,
                'id': 'http://obi-wan.jedi/posts/%d.html' % i,
                'link': 'http://obi-wan.jedi/posts/%d.html' % i,
                'links': [
                    {
                        'href': 'http://obi-wan.jedi/posts/%d.html' % i,
                        'rel': 'alternate',
                        'type': 'text/html',
                    },
                ],
                'published': '2017-09-%02d' % (i + 1),
                'published_parsed': mock.ANY,
                'summary': 'the way of the Force',
                'title': 'Essay #%d' % i,
                'title_detail': {
                    'base': '',
                    'language': None,
                    'type': 'text/plain',
                    'value': 'Essay #%d' % i,
                },
                'updated': '1970-01-01T00:00:00+00:00',
                'updated_parsed': mock.ANY,
            }
            for i in range(
                len(documents[:-1]) - 1,
                len(documents[:-1]) - posts_number - 1,
                -1
            )
        ],
        'feed': {
            'generator': 'Holocron',
            'generator_detail': {
                'name': 'Holocron',
                'href': 'https://holocron.readthedocs.io',
                'version': '0.4.0',
            },
            'guidislink': True,
            'id': 'http://obi-wan.jedi',
            'link': 'http://obi-wan.jedi',
            'links': [
                {
                    'href': 'http://obi-wan.jedi/' + save_as,
                    'rel': 'self',
                    'type': 'application/atom+xml',
                },
                {
                    'href': 'http://obi-wan.jedi',
                    'rel': 'alternate',
                    'type': 'text/html',
                },
            ],
            'title': "Kenobi's Thoughts",
            'title_detail': {
                'base': '',
                'language': None,
                'type': 'text/plain',
                'value': "Kenobi's Thoughts",
            },
            'updated': mock.ANY,
            'updated_parsed': mock.ANY,
        },
        'namespaces': {'': 'http://www.w3.org/2005/Atom'},
        'version': 'atom10',
    }


def test_documents(testapp):
    """Atom processor has to ignore non-relevant documents."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    documents = atom.process(
        testapp,
        [
            _get_document(
                title='Essay #1',
                content='the way of the Force',
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html'),
                updated=timepoint,
                published=datetime.date(2017, 9, 1)),
            _get_document(
                title='Essay #2',
                content='the way of the Force',
                source=os.path.join('pages', '2.md'),
                destination=os.path.join('pages', '2.html'),
                updated=timepoint,
                published=datetime.date(2017, 9, 2)),
            _get_document(
                title='Essay #3',
                content='the way of the Force',
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html'),
                updated=timepoint,
                published=datetime.date(2017, 9, 3)),
            _get_document(
                title='Essay #4',
                content='the way of the Force',
                source=os.path.join('pages', '4.md'),
                destination=os.path.join('pages', '4.html'),
                updated=timepoint,
                published=datetime.date(2017, 9, 4)),
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
        assert document['title'] == 'Essay #%d' % (i + 1)
        assert document['content'] == 'the way of the Force'
        assert document['published'] == datetime.date(2017, 9, i + 1)

    # Ensure a virtual feed document contains proper values.
    assert documents[-1]['source'] == 'virtual://feed'
    assert documents[-1]['destination'] == 'atom.xml'
    assert feedparser.parse(documents[-1]['content']) == {
        'bozo': 0,
        'encoding': 'utf-8',
        'entries': [
            {
                'author': 'Obi-Wan Kenobi',
                'author_detail': {'name': 'Obi-Wan Kenobi'},
                'authors': [{'name': 'Obi-Wan Kenobi'}],
                'content': [
                    {
                        'base': '',
                        'language': None,
                        'type': 'text/html',
                        'value': 'the way of the Force',
                    }
                ],
                'guidislink': False,
                'id': 'http://obi-wan.jedi/posts/%d.html' % i,
                'link': 'http://obi-wan.jedi/posts/%d.html' % i,
                'links': [
                    {
                        'href': 'http://obi-wan.jedi/posts/%d.html' % i,
                        'rel': 'alternate',
                        'type': 'text/html',
                    },
                ],
                'published': '2017-09-%02d' % i,
                'published_parsed': mock.ANY,
                'summary': 'the way of the Force',
                'title': 'Essay #%d' % i,
                'title_detail': {
                    'base': '',
                    'language': None,
                    'type': 'text/plain',
                    'value': 'Essay #%d' % i,
                },
                'updated': '1970-01-01T00:00:00+00:00',
                'updated_parsed': mock.ANY,
            }
            for i in [3, 1]
        ],
        'feed': {
            'generator': 'Holocron',
            'generator_detail': {
                'name': 'Holocron',
                'href': 'https://holocron.readthedocs.io',
                'version': '0.4.0',
            },
            'guidislink': True,
            'id': 'http://obi-wan.jedi',
            'link': 'http://obi-wan.jedi',
            'links': [
                {
                    'href': 'http://obi-wan.jedi/atom.xml',
                    'rel': 'self',
                    'type': 'application/atom+xml',
                },
                {
                    'href': 'http://obi-wan.jedi',
                    'rel': 'alternate',
                    'type': 'text/html',
                },
            ],
            'title': "Kenobi's Thoughts",
            'title_detail': {
                'base': '',
                'language': None,
                'type': 'text/plain',
                'value': "Kenobi's Thoughts",
            },
            'updated': mock.ANY,
            'updated_parsed': mock.ANY,
        },
        'namespaces': {'': 'http://www.w3.org/2005/Atom'},
        'version': 'atom10',
    }
