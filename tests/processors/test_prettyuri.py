"""Prettyuri processor test suite."""

import os
import collections.abc

import pytest

from holocron import core
from holocron.processors import prettyuri


@pytest.fixture(scope="function")
def testapp():
    return core.Application()


def test_item(testapp):
    """Prettyuri processor has to work!"""

    stream = prettyuri.process(
        testapp, [core.Item({"destination": os.path.join("about", "cv.html")})]
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"destination": os.path.join("about", "cv", "index.html")})
    ]


@pytest.mark.parametrize(
    ["index"], [pytest.param("index.html"), pytest.param("index.htm")]
)
def test_item_index(testapp, index):
    """Prettyuri processor has to ignore index items."""

    stream = prettyuri.process(
        testapp,
        [core.Item({"destination": os.path.join("about", "cv", index)})],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"destination": os.path.join("about", "cv", index)})
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
    """Prettyuri processor has to work with stream."""

    stream = prettyuri.process(
        testapp,
        [
            core.Item({"destination": os.path.join("about", "%d.html" % i)})
            for i in range(amount)
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"destination": os.path.join("about", str(i), "index.html")})
        for i in range(amount)
    ]
