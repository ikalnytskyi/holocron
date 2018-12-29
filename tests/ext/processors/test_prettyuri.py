"""Prettyuri processor test suite."""

import os

import pytest

from holocron import app
from holocron.ext.processors import prettyuri


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron()


@pytest.fixture(scope='function')
def run_processor():
    streams = []

    def run(*args, **kwargs):
        streams.append(prettyuri.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


def test_document(testapp, run_processor):
    """Prettyuri processor has to work!"""

    stream = run_processor(
        testapp,
        [
            {
                'destination': os.path.join('about', 'cv.html'),
            },
        ])

    assert next(stream) == \
        {
            'destination': os.path.join('about', 'cv', 'index.html'),
        }


@pytest.mark.parametrize('index', [
    'index.html',
    'index.htm',
])
def test_document_index(testapp, run_processor, index):
    """Prettyuri processor has to ignore index documents."""

    stream = run_processor(
        testapp,
        [
            {
                'destination': os.path.join('about', 'cv', index),
            },
        ])

    assert next(stream) == \
        {
            'destination': os.path.join('about', 'cv', index),
        }


def test_param_when(testapp, run_processor):
    """Prettyuri processor has to ignore non-targeted documents."""

    stream = run_processor(
        testapp,
        [
            {
                'source': '0.txt',
                'destination': '0.txt',
            },
            {
                'source': '1.md',
                'destination': os.path.join('1', 'index.html'),
            },
            {
                'source': '2',
                'destination': '2.html',
            },
            {
                'source': '3.markdown',
                'destination': '3.html',
            },
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(markdown|mdown|mkd|mdwn|md)$',
            },
        ])

    assert next(stream) == \
        {
            'source': '0.txt',
            'destination': '0.txt',
        }

    assert next(stream) == \
        {
            'source': '1.md',
            'destination': os.path.join('1', 'index.html'),
        }

    assert next(stream) == \
        {
            'source': '2',
            'destination': '2.html',
        }

    assert next(stream) == \
        {
            'source': '3.markdown',
            'destination': os.path.join('3', 'index.html'),
        }


@pytest.mark.parametrize('params, error', [
    ({'when': [42]}, 'when: unsupported value'),
])
def test_param_bad_value(testapp, params, error):
    """Prettyuri processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(prettyuri.process(testapp, [], **params))
