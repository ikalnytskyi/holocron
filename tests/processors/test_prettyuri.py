"""Prettyuri processor test suite."""

import os

import pytest

from holocron import app, core
from holocron.processors import prettyuri


@pytest.fixture(scope="function")
def testapp():
    return app.Holocron()


def test_item(testapp):
    """Prettyuri processor has to work!"""

    stream = prettyuri.process(
        testapp,
        [
            core.Item({"destination": os.path.join("about", "cv.html")}),
        ])

    assert next(stream) == core.Item(
        {
            "destination": os.path.join("about", "cv", "index.html"),
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("index", [
    "index.html",
    "index.htm",
])
def test_item_index(testapp, index):
    """Prettyuri processor has to ignore index items."""

    stream = prettyuri.process(
        testapp,
        [
            core.Item({"destination": os.path.join("about", "cv", index)}),
        ])

    assert next(stream) == core.Item(
        {
            "destination": os.path.join("about", "cv", index),
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Prettyuri processor has to work with stream."""

    stream = prettyuri.process(
        testapp,
        [
            core.Item({"destination": os.path.join("about", "%d.html" % i)})
            for i in range(amount)
        ])

    for i in range(amount):
        assert next(stream) == core.Item(
            {
                "destination": os.path.join("about", str(i), "index.html"),
            })

    with pytest.raises(StopIteration):
        next(stream)
