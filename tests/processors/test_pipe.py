"""Pipe processor test suite."""

import collections.abc

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
        [core.Item({"content": "the Force", "author": "skywalker"})],
        pipe=[{"name": "spam"}, {"name": "eggs"}, {"name": "rice"}],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item(
            {
                "content": "the Force #friedeggs",
                "author": "skywalker",
                "spam": 42,
            }
        ),
        core.Item({"content": "rice"}),
    ]


def test_item_processor_with_option(testapp):
    """Pipe processor has to pass down processors options."""

    stream = pipe.process(
        testapp,
        [core.Item({"content": "the Force", "author": "skywalker"})],
        pipe=[{"name": "spam", "text": 1}],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "the Force", "author": "skywalker", "spam": 1})
    ]


def test_param_pipeline_empty(testapp):
    """Pipe processor with empty pipeline has to pass by."""

    stream = pipe.process(
        testapp,
        [core.Item({"content": "the Force", "author": "skywalker"})],
        pipe=[],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "the Force", "author": "skywalker"})
    ]


@pytest.mark.parametrize(
    ["amount"],
    [
        pytest.param(0),
        pytest.param(1),
        pytest.param(2),
        pytest.param(5),
        pytest.param(10),
    ],
)
def test_item_many(testapp, amount):
    """Pipe processor has to work with stream."""

    stream = pipe.process(
        testapp,
        [
            core.Item({"content": "the Force (%d)" % i, "author": "skywalker"})
            for i in range(amount)
        ],
        pipe=[{"name": "spam"}, {"name": "eggs"}],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item(
            {
                "content": "the Force (%d) #friedeggs" % i,
                "author": "skywalker",
                "spam": 42,
            }
        )
        for i in range(amount)
    ]


@pytest.mark.parametrize(
    ["params", "error"],
    [
        pytest.param(
            {"pipe": 42}, "pipe: 42 is not of type 'array'", id="pipe-int"
        )
    ],
)
def test_param_bad_value(testapp, params, error):
    """Pipe processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(pipe.process(testapp, [], **params))
    assert str(excinfo.value) == error
