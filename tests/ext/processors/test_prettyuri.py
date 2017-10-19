"""Prettyuri processor test suite."""

import os

import mock
import pytest

from holocron import app, content
from holocron.ext.processors import prettyuri


def _get_document(cls=content.Page, **kwargs):
    document = cls(app.Holocron({}))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    return mock.Mock()


def test_document(testapp):
    """Destination has to be changed to produce a pretty URI."""

    documents = prettyuri.process(
        testapp,
        [
            _get_document(destination='about/cv.html'),
        ])

    assert documents[0]['destination'] == 'about/cv/index.html'


@pytest.mark.parametrize('index', [
    'index.html',
    'index.htm',
])
def test_document_index(testapp, index):
    """Prettyuri processor has to ignore index documents."""

    documents = prettyuri.process(
        testapp,
        [
            _get_document(destination=os.path.join('about', 'cv', index)),
        ])

    assert documents[0]['destination'] == os.path.join('about', 'cv', index)


def test_documents(testapp):
    """Prettyuri processor has to ignore non-targeted documents."""

    documents = prettyuri.process(
        testapp,
        [
            _get_document(source='0.txt', destination='0.txt'),
            _get_document(source='1.md', destination='1/index.html'),
            _get_document(source='2', destination='2.html'),
            _get_document(source='3.markdown', destination='3.html'),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(markdown|mdown|mkd|mdwn|md)$',
            },
        ])

    assert documents[0]['destination'] == '0.txt'
    assert documents[1]['destination'] == '1/index.html'
    assert documents[2]['destination'] == '2.html'
    assert documents[3]['destination'] == '3/index.html'
