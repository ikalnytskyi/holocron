"""Metadata processor test suite."""

import pytest

from holocron import core
from holocron.processors import metadata


@pytest.fixture(scope="function")
def testapp():
    return core.Application()


def test_item(testapp):
    """Metadata processor has to work!"""

    stream = metadata.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force",
                    "author": "skywalker",
                }),
        ],
        metadata={
            "author": "yoda",
            "type": "memoire",
        })

    assert next(stream) == core.Item(
        {
            "content": "the Force",
            "author": "yoda",
            "type": "memoire",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_untouched(testapp):
    """Metadata processor has to ignore items if no metadata are passed."""

    stream = metadata.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force",
                    "author": "skywalker",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": "the Force",
            "author": "skywalker",
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Metadata processor has to work with stream."""

    stream = metadata.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the key is #%d" % i,
                    "author": "luke",
                })
            for i in range(amount)
        ],
        metadata={
            "author": "yoda",
            "type": "memoire",
        })

    for i in range(amount):
        assert next(stream) == core.Item(
            {
                "content": "the key is #%d" % i,
                "author": "yoda",
                "type": "memoire",
            })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("overwrite, author", [
    (True, "yoda"),
    (False, "skywalker"),
])
def test_param_overwrite(testapp, overwrite, author):
    """Metadata processor has to respect overwrite option."""

    stream = metadata.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force",
                    "author": "skywalker",
                }),
        ],
        metadata={
            "author": "yoda",
            "type": "memoire",
        },
        overwrite=overwrite)

    assert next(stream) == core.Item(
        {
            "content": "the Force",
            "author": author,
            "type": "memoire",
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("params, error", [
    ({"metadata": 42}, "metadata: 42 is not of type 'object'"),
    ({"overwrite": "true"}, "overwrite: 'true' is not of type 'boolean'"),
])
def test_param_bad_value(testapp, params, error):
    """Metadata processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(metadata.process(testapp, [], **params))
    assert str(excinfo.value) == error
