"""When processor test suite."""

import collections.abc
import itertools
import os

import pytest

from holocron import core
from holocron.processors import when


@pytest.fixture(scope="function")
def testapp(request):
    def spam(app, items, *, text=42):
        for item in items:
            item["spam"] = text
            yield item

    def rice(app, items):
        yield from items
        yield core.Item({"content": "rice"})

    def eggs(app, items):
        while True:
            try:
                item_a = next(items)
                item_b = next(items)
            except StopIteration:
                break
            else:
                yield core.Item({"key": item_a["key"] + item_b["key"]})

    instance = core.Application()
    instance.add_processor("spam", spam)
    instance.add_processor("rice", rice)
    instance.add_processor("eggs", eggs)
    return instance


@pytest.mark.parametrize(
    ["cond", "item"],
    [
        pytest.param(
            "item.author == 'yoda'",
            {"content": "eh", "author": "yoda", "spam": 42},
            id="matched",
        ),
        pytest.param(
            "item.author == 'luke'",
            {"content": "eh", "author": "yoda"},
            id="skipped",
        ),
    ],
)
def test_item_spam(testapp, cond, item):
    """When processor has to work with a simple processor!"""

    stream = when.process(
        testapp,
        [core.Item({"content": "eh", "author": "yoda"})],
        processor={"name": "spam"},
        when=[cond],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [core.Item(item)]


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
def test_item_many_spam(testapp, amount):
    """When processor has to work with a stream."""

    stream = when.process(
        testapp,
        [
            core.Item({"content": "the great jedi", "key": i})
            for i in range(amount)
        ],
        processor={"name": "spam"},
        when=["item.key % 2 == 0"],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "the great jedi", "key": i})
        if i % 2
        else core.Item({"content": "the great jedi", "key": i, "spam": 42})
        for i in range(amount)
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
def test_item_many_rice(testapp, amount):
    """When processor has to work with a processor that populates a stream."""

    stream = when.process(
        testapp,
        [
            core.Item({"content": "the great jedi", "key": i})
            for i in range(amount)
        ],
        processor={"name": "rice"},
        when=["item.key % 2 == 0"],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == list(
        itertools.chain(
            [
                core.Item({"content": "the great jedi", "key": i})
                for i in range(amount)
            ],
            [core.Item({"content": "rice"})],
        )
    )


def test_item_many_eggs(testapp):
    """When processor has to work with complex processor."""

    stream = when.process(
        testapp,
        [core.Item({"content": "the great jedi", "key": i}) for i in range(5)],
        processor={"name": "eggs"},
        when=["item.key % 2 != 0"],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "the great jedi", "key": 0}),
        core.Item({"content": "the great jedi", "key": 2}),
        core.Item({"key": 4}),
        core.Item({"content": "the great jedi", "key": 4}),
    ]


@pytest.mark.parametrize(
    ["cond"],
    [
        pytest.param([r"item.author == 'yoda'"], id="=="),
        pytest.param([r"item.source.endswith('.md')"], id="endswith"),
        pytest.param(
            [r"item.author == 'yoda'", "item.source.endswith('.md')"],
            id="two-conditions",
        ),
        pytest.param([r"item.source | match('.*\.md')"], id="match-md"),
        pytest.param([r"item.source | match('^about.*')"], id="match-about"),
    ],
)
def test_param_when(testapp, cond):
    """When processor has to respect conditions."""

    stream = when.process(
        testapp,
        [
            core.Item(
                {
                    "content": "eh",
                    "author": "yoda",
                    "source": os.path.join("about", "index.md"),
                }
            )
        ],
        processor={"name": "spam"},
        when=cond,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item(
            {
                "content": "eh",
                "author": "yoda",
                "source": os.path.join("about", "index.md"),
                "spam": 42,
            }
        )
    ]
