"""Prettyuri processor test suite."""

import os

import mock
import pytest

from holocron import app, content
from holocron.ext.processors import prettyuri


# We are forced to prepare documents this way as long as they smart.
# Fortunately, it's a temporary measure as we are going towards plain
# documents represented as dictionaries.
@mock.patch('holocron.content.os.path.getmtime', return_value=1420121400)
@mock.patch('holocron.content.os.path.getctime', return_value=662739000)
@mock.patch('holocron.content.os.getcwd', return_value='cwd')
def _get_document(_, __, ___, cls=content.Page, path='memory://'):
    return cls(path, app.Holocron({}))


@pytest.fixture(scope='function')
def testapp():
    return mock.Mock()


def test_document(testapp):
    """Destination has to be changed to produce a pretty URI."""

    documents = prettyuri.process(
        testapp,
        [
            _get_document(path='about/cv.mdown'),
        ])

    assert documents[0].destination == 'cwd/_build/about/cv/index.html'


@pytest.mark.parametrize('index', [
    'index.html',
    'index.htm',
])
def test_document_index(testapp, index):
    """Prettyuri processor has to ignore index documents."""

    document = _get_document(path='about/cv.mdown')
    document.destination = os.path.join('about', 'cv', index)

    documents = prettyuri.process(
        testapp,
        [
            document,
        ])

    assert documents[0].destination == os.path.join('about', 'cv', index)


def test_documents(testapp):
    """Prettyuri processor has to ignore non-targeted documents."""

    documents = prettyuri.process(
        testapp,
        [
            _get_document(path='0.txt'),
            _get_document(path='1.md'),
            _get_document(path='2'),
            _get_document(path='3.markdown'),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(markdown|mdown|mkd|mdwn|md)$',
            },
        ])

    assert documents[0].destination == 'cwd/_build/0.txt'
    assert documents[1].destination == 'cwd/_build/1/index.html'
    assert documents[2].destination == 'cwd/_build/2'
    assert documents[3].destination == 'cwd/_build/3/index.html'
