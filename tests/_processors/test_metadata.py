"""Metadata processor test suite."""

import collections.abc

import pytest

import holocron
from holocron._processors import metadata


@pytest.fixture(scope="function")
def testapp():
    return holocron.Application()


def test_item(testapp):
    """Metadata processor has to work!"""

    stream = metadata.process(
        testapp,
        [holocron.Item({"content": "the Force", "author": "skywalker"})],
        metadata={"author": "yoda", "type": "memoire"},
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"content": "the Force", "author": "yoda", "type": "memoire"})
    ]


def test_item_untouched(testapp):
    """Metadata processor has to ignore items if no metadata are passed."""

    stream = metadata.process(
        testapp,
        [holocron.Item({"content": "the Force", "author": "skywalker"})],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"content": "the Force", "author": "skywalker"})
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
    """Metadata processor has to work with stream."""

    stream = metadata.process(
        testapp,
        [
            holocron.Item({"content": "the key is #%d" % i, "author": "luke"})
            for i in range(amount)
        ],
        metadata={"author": "yoda", "type": "memoire"},
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the key is #%d" % i,
                "author": "yoda",
                "type": "memoire",
            }
        )
        for i in range(amount)
    ]


@pytest.mark.parametrize(
    ["overwrite", "author"],
    [
        pytest.param(True, "yoda", id="overwrite"),
        pytest.param(False, "skywalker", id="not-overwrite"),
    ],
)
def test_args_overwrite(testapp, overwrite, author):
    """Metadata processor has to respect 'overwrite' argument."""

    stream = metadata.process(
        testapp,
        [holocron.Item({"content": "the Force", "author": "skywalker"})],
        metadata={"author": "yoda", "type": "memoire"},
        overwrite=overwrite,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"content": "the Force", "author": author, "type": "memoire"})
    ]


@pytest.mark.parametrize(
    ["args", "error"],
    [
        pytest.param(
            {"metadata": 42},
            "metadata: 42 is not of type 'object'",
            id="metadata",
        ),
        pytest.param(
            {"overwrite": "true"},
            "overwrite: 'true' is not of type 'boolean'",
            id="overwrite",
        ),
    ],
)
def test_args_bad_value(testapp, args, error):
    """Metadata processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(metadata.process(testapp, [], **args))
    assert str(excinfo.value) == error
