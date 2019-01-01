"""Index processor test suite."""

import os
import datetime

import pytest

from holocron import app, content
from holocron.ext.processors import index


def _get_document(**kwargs):
    document = content.Document(app.Holocron({}))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})
    return instance


def test_document(testapp):
    """Index processor has to work!"""

    documents = index.process(
        testapp,
        [
            _get_document(
                title='the way of the Force',
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 4)),
        ])

    assert len(documents) == 2

    assert documents[0]['title'] == 'the way of the Force'
    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['published'] == datetime.date(2017, 10, 4)

    assert documents[-1]['source'] == 'virtual://index'
    assert documents[-1]['destination'] == 'index.html'
    assert documents[-1]['template'] == 'index.j2'
    assert documents[-1]['documents'] == [documents[0]]


def test_param_template(testapp):
    """Index processor has respect template parameter."""

    documents = index.process(
        testapp,
        [
            _get_document(
                title='the way of the Force',
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 4)),
        ],
        template='foobar.txt')

    assert len(documents) == 2

    assert documents[0]['title'] == 'the way of the Force'
    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['published'] == datetime.date(2017, 10, 4)

    assert documents[-1]['source'] == 'virtual://index'
    assert documents[-1]['destination'] == 'index.html'
    assert documents[-1]['template'] == 'foobar.txt'
    assert documents[-1]['documents'] == [documents[0]]


def test_param_when(testapp):
    """Index processor has to ignore non-relevant documents."""

    documents = index.process(
        testapp,
        [
            _get_document(
                title='the way of the Force #1',
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 1)),
            _get_document(
                title='the way of the Force #2',
                source=os.path.join('pages', '2.md'),
                destination=os.path.join('pages', '2.html'),
                published=datetime.date(2017, 10, 2)),
            _get_document(
                title='the way of the Force #3',
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html'),
                published=datetime.date(2017, 10, 3)),
            _get_document(
                title='the way of the Force #4',
                source=os.path.join('pages', '4.md'),
                destination=os.path.join('pages', '4.html'),
                published=datetime.date(2017, 10, 4)),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    assert len(documents) == 5

    for i, document in enumerate(documents[:-1]):
        assert document['source'].endswith('%d.md' % (i + 1))
        assert document['title'] == 'the way of the Force #%d' % (i + 1)
        assert document['published'] == datetime.date(2017, 10, i + 1)

    assert documents[-1]['source'] == 'virtual://index'
    assert documents[-1]['destination'] == 'index.html'
    assert documents[-1]['template'] == 'index.j2'
    assert documents[-1]['documents'] == [
        documents[0],
        documents[2],
    ]


@pytest.mark.parametrize('params, error', [
    ({'when': 42}, 'when: unsupported value'),
    ({'template': 42}, "template: 42 should be instance of 'str'"),
])
def test_param_bad_value(testapp, params, error):
    """Index processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        index.process(testapp, [], **params)
