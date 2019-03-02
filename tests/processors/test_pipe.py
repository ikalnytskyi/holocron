"""Pipe processor test suite."""

import pytest

from holocron import core
from holocron.processors import pipe


@pytest.fixture(scope="function")
def testapp():
    def spam(app, items, **options):
        for item in items:
            item["spam"] = options.get("text", 42)
            yield item

    def eggs(app, items, **options):
        for item in items:
            item["content"] += " #friedeggs"
            yield item

    def rice(app, items, **options):
        yield from items
        yield core.Item({"content": "rice"})

    instance = core.Application()
    instance.add_processor("spam", spam)
    instance.add_processor("eggs", eggs)
    instance.add_processor("rice", rice)
    return instance


def test_item(testapp):
    """Pipe processor has to work!"""

    stream = pipe.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force",
                    "author": "skywalker",
                }),
        ],
        pipe=[
            {"name": "spam"},
            {"name": "eggs"},
            {"name": "rice"},
        ])

    assert next(stream) == core.Item(
        {
            "content": "the Force #friedeggs",
            "author": "skywalker",
            "spam": 42,
        })

    assert next(stream) == core.Item(
        {
            "content": "rice",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_processor_with_option(testapp):
    """Pipe processor has to pass down processors options."""

    stream = pipe.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force",
                    "author": "skywalker",
                }),
        ],
        pipe=[
            {"name": "spam", "text": 1},
        ])

    assert next(stream) == core.Item(
        {
            "content": "the Force",
            "author": "skywalker",
            "spam": 1,
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_param_pipeline_empty(testapp):
    """Pipe processor with empty pipeline has to pass by."""

    stream = pipe.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force",
                    "author": "skywalker",
                }),
        ],
        pipe=[])

    assert next(stream) == core.Item(
        {
            "content": "the Force",
            "author": "skywalker",
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Pipe processor has to work with stream."""

    stream = pipe.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force (%d)" % i,
                    "author": "skywalker",
                })
            for i in range(amount)
        ],
        pipe=[
            {"name": "spam"},
            {"name": "eggs"},
        ])

    for i in range(amount):
        assert next(stream) == core.Item(
            {
                "content": "the Force (%d) #friedeggs" % i,
                "author": "skywalker",
                "spam": 42,
            })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("params, error", [
    ({"pipe": 42}, "pipe: 42 should be instance of 'list'"),
])
def test_param_bad_value(testapp, params, error):
    """Pipe processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(pipe.process(testapp, [], **params))
