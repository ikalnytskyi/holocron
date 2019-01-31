"""When processor test suite."""

import os

import pytest

from holocron import app
from holocron.processors import when


@pytest.fixture(scope="function")
def testapp(request):
    def spam(app, items, *, text=42):
        for item in items:
            item["spam"] = text
            yield item

    def rice(app, items):
        yield from items
        yield {"content": "rice"}

    def eggs(app, items):
        while True:
            try:
                item_a = next(items)
                item_b = next(items)
            except StopIteration:
                break
            else:
                yield {"key": item_a["key"] + item_b["key"]}

    instance = app.Holocron()
    instance.add_processor("spam", spam)
    instance.add_processor("rice", rice)
    instance.add_processor("eggs", eggs)
    return instance


@pytest.mark.parametrize("cond, item", [
    ("item.author == 'yoda'", {"content": "eh", "author": "yoda", "spam": 42}),
    ("item.author == 'luke'", {"content": "eh", "author": "yoda"}),
])
def test_item_spam(testapp, cond, item):
    """When processor has to work with a simple processor!"""

    stream = when.process(
        testapp,
        [
            {
                "content": "eh",
                "author": "yoda",
            },
        ],
        processor={"name": "spam"},
        when=[cond])

    assert next(stream) == item

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many_spam(testapp, amount):
    """When processor has to work with a stream."""

    stream = when.process(
        testapp,
        [
            {
                "content": "the great jedi",
                "key": i,
            }
            for i in range(amount)
        ],
        processor={"name": "spam"},
        when=["item.key % 2 == 0"])

    for i, item in zip(range(amount), stream):
        if i % 2 == 0:
            assert item == \
                {
                    "content": "the great jedi",
                    "key": i,
                    "spam": 42,
                }
        else:
            assert item == \
                {
                    "content": "the great jedi",
                    "key": i,
                }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many_rice(testapp, amount):
    """When processor has to work with a processor that populates a stream."""

    stream = when.process(
        testapp,
        [
            {
                "content": "the great jedi",
                "key": i,
            }
            for i in range(amount)
        ],
        processor={"name": "rice"},
        when=["item.key % 2 == 0"])

    for i, item in zip(range(amount), stream):
        assert item == \
            {
                "content": "the great jedi",
                "key": i,
            }

    assert next(stream) == \
        {
            "content": "rice",
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_item_many_eggs(testapp):
    """When processor has to work with complex processor."""

    stream = when.process(
        testapp,
        [
            {
                "content": "the great jedi",
                "key": i,
            }
            for i in range(5)
        ],
        processor={"name": "eggs"},
        when=["item.key % 2 != 0"])

    assert next(stream) == \
        {
            "content": "the great jedi",
            "key": 0,
        }

    assert next(stream) == \
        {
            "content": "the great jedi",
            "key": 2,
        }

    assert next(stream) == \
        {
            "key": 4,
        }

    assert next(stream) == \
        {
            "content": "the great jedi",
            "key": 4,
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("cond", [
    [r"item.author == 'yoda'"],
    [r"item.source.endswith('.md')"],
    [r"item.author == 'yoda'", "item.source.endswith('.md')"],
    [r"item.source | match('.*\.md')"],
    [r"item.source | match('^about.*')"],
])
def test_param_when(testapp, cond):
    """When processor has to respect conditions."""

    stream = when.process(
        testapp,
        [
            {
                "content": "eh",
                "author": "yoda",
                "source": os.path.join("about", "index.md"),
            },
        ],
        processor={"name": "spam"},
        when=cond)

    assert next(stream) == \
        {
            "content": "eh",
            "author": "yoda",
            "source": os.path.join("about", "index.md"),
            "spam": 42,
        }

    with pytest.raises(StopIteration):
        next(stream)
