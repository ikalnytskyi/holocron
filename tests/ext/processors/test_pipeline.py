"""Pipeline processor test suite."""


import os

import pytest

from holocron import app
from holocron.ext.processors import pipeline


@pytest.fixture(scope='function')
def testapp():
    def spam(app, documents, **options):
        for document in documents:
            document['spam'] = options.get('text', 42)
            yield document

    def eggs(app, documents, **options):
        for document in documents:
            document['content'] += ' #friedeggs'
            yield document

    def rice(app, documents, **options):
        yield from documents
        yield {'content': 'rice'}

    instance = app.Holocron({})
    instance.add_processor('spam', spam)
    instance.add_processor('eggs', eggs)
    instance.add_processor('rice', rice)

    return instance


@pytest.fixture(scope='function')
def run_processor():
    streams = []

    def run(*args, **kwargs):
        streams.append(pipeline.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


def test_document(testapp, run_processor):
    """Pipeline processor has to work!"""

    stream = run_processor(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ],
        processors=[
            {'name': 'spam'},
            {'name': 'eggs'},
            {'name': 'rice'},
        ])

    assert next(stream) == \
        {
            'content': 'the Force #friedeggs',
            'author': 'skywalker',
            'spam': 42,
        }

    assert next(stream) == \
        {
            'content': 'rice',
        }


def test_document_processor_with_option(testapp, run_processor):
    """Pipeline processor has to pass down processors options."""

    stream = run_processor(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ],
        processors=[
            {'name': 'spam', 'text': 1},
        ])

    assert next(stream) == \
        {
            'content': 'the Force',
            'author': 'skywalker',
            'spam': 1,
        }


def test_document_no_processors(testapp, run_processor):
    """Pipeline processor with no processors has to passed by."""

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


def test_param_when(testapp, run_processor):
    """Pipeline processor has to ignore non-targeted documents."""

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
        processors=[
            {'name': 'spam'},
            {'name': 'eggs'},
            {'name': 'rice'},
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    assert next(stream) == \
        {
            'content': 'the way of the Force #2',
            'source': os.path.join('pages', '2.md'),
        }

    assert next(stream) == \
        {
            'content': 'the way of the Force #4',
            'source': os.path.join('pages', '4.md'),
        }

    assert next(stream) == \
        {
            'content': 'the way of the Force #1 #friedeggs',
            'source': os.path.join('posts', '1.md'),
            'spam': 42,
        }

    assert next(stream) == \
        {
            'content': 'the way of the Force #3 #friedeggs',
            'source': os.path.join('posts', '3.md'),
            'spam': 42,
        }

    assert next(stream) == \
        {
            'content': 'rice',
        }


@pytest.mark.parametrize('params, error', [
    ({'when': [42]}, 'when: unsupported value'),
    ({'processors': 42}, "processors: 42 should be instance of 'list'"),
])
def test_param_bad_value(testapp, params, error):
    """Pipeline processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(pipeline.process(testapp, [], **params))
