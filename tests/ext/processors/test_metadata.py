"""Metadata processor test suite."""

import os

import pytest

from holocron import app
from holocron.ext.processors import metadata


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron({})


@pytest.fixture(scope='function')
def run_processor():
    streams = []

    def run(*args, **kwargs):
        streams.append(metadata.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


def test_document(testapp, run_processor):
    """Metadata processor has to work!"""

    stream = run_processor(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ],
        metadata={
            'author': 'yoda',
            'type': 'memoire',
        })

    assert next(stream) == \
        {
            'content': 'the Force',
            'author': 'yoda',
            'type': 'memoire',
        }


def test_document_untouched(testapp, run_processor):
    """Metadata processor has to ignore documents if metadata isn't passed."""

    stream = run_processor(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ])

    assert next(stream) == \
        {
            'content': 'the Force',
            'author': 'skywalker',
        }


@pytest.mark.parametrize('overwrite, author', [
    (True, 'yoda'),
    (False, 'skywalker'),
])
def test_param_overwrite(testapp, run_processor, overwrite, author):
    """Metadata processor has to respect overwrite option."""

    stream = run_processor(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ],
        metadata={
            'author': 'yoda',
            'type': 'memoire',
        },
        overwrite=overwrite)

    assert next(stream) == \
        {
            'content': 'the Force',
            'author': author,
            'type': 'memoire',
        }


def test_param_when(testapp, run_processor):
    """Metadata processor has to ignore non-targeted documents."""

    stream = run_processor(
        testapp,
        [
            {
                'content': 'the way of the Force #1',
                'source': os.path.join('posts', '1.md'),
            },
            {
                'content': 'the way of the Force #2',
                'source': os.path.join('pages', '2.md'),
            },
            {
                'content': 'the way of the Force #3',
                'source': os.path.join('posts', '3.md'),
            },
            {
                'content': 'the way of the Force #4',
                'source': os.path.join('pages', '4.md'),
            },
        ],
        metadata={
            'author': 'kenobi',
        },
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    assert next(stream) == \
        {
            'content': 'the way of the Force #1',
            'source': os.path.join('posts', '1.md'),
            'author': 'kenobi',
        }

    assert next(stream) == \
        {
            'content': 'the way of the Force #2',
            'source': os.path.join('pages', '2.md'),
        }

    assert next(stream) == \
        {
            'content': 'the way of the Force #3',
            'source': os.path.join('posts', '3.md'),
            'author': 'kenobi',
        }

    assert next(stream) == \
        {
            'content': 'the way of the Force #4',
            'source': os.path.join('pages', '4.md'),
        }


@pytest.mark.parametrize('params, error', [
    ({'when': [42]}, 'when: unsupported value'),
    ({'metadata': 42}, "metadata: 42 should be instance of 'dict'"),
    ({'overwrite': 'true'}, "overwrite: 'true' should be instance of 'bool'"),
])
def test_param_bad_value(testapp, params, error):
    """Metadata processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(metadata.process(testapp, [], **params))
