"""Pipeline processor test suite."""

import pytest

from holocron import app
from holocron.ext.processors import pipeline


@pytest.fixture(scope='function')
def testapp():
    def spam(app, items, **options):
        for item in items:
            item['spam'] = options.get('text', 42)
            yield item

    def eggs(app, items, **options):
        for item in items:
            item['content'] += ' #friedeggs'
            yield item

    def rice(app, items, **options):
        yield from items
        yield {'content': 'rice'}

    instance = app.Holocron()
    instance.add_processor('spam', spam)
    instance.add_processor('eggs', eggs)
    instance.add_processor('rice', rice)

    return instance


def test_item(testapp):
    """Pipeline processor has to work!"""

    stream = pipeline.process(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ],
        pipeline=[
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

    with pytest.raises(StopIteration):
        next(stream)


def test_item_processor_with_option(testapp):
    """Pipeline processor has to pass down processors options."""

    stream = pipeline.process(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ],
        pipeline=[
            {'name': 'spam', 'text': 1},
        ])

    assert next(stream) == \
        {
            'content': 'the Force',
            'author': 'skywalker',
            'spam': 1,
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_pipeline_empty(testapp):
    """Pipeline processor with empty pipeline has to pass by."""

    stream = pipeline.process(
        testapp,
        [
            {
                'content': 'the Force',
                'author': 'skywalker',
            },
        ],
        pipeline=[])

    assert next(stream) == \
        {
            'content': 'the Force',
            'author': 'skywalker',
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('amount', [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Pipeline processor has to work with stream."""

    stream = pipeline.process(
        testapp,
        [
            {
                'content': 'the Force (%d)' % i,
                'author': 'skywalker',
            }
            for i in range(amount)
        ],
        pipeline=[
            {'name': 'spam'},
            {'name': 'eggs'},
        ])

    for i in range(amount):
        assert next(stream) == \
            {
                'content': 'the Force (%d) #friedeggs' % i,
                'author': 'skywalker',
                'spam': 42,
            }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('params, error', [
    ({'pipeline': 42}, "pipeline: 42 should be instance of 'list'"),
])
def test_param_bad_value(testapp, params, error):
    """Pipeline processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(pipeline.process(testapp, [], **params))
