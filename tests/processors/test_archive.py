"""Archive processor test suite."""

import os

import pytest

from holocron import core
from holocron.processors import archive


@pytest.fixture(scope="function")
def testapp():
    return core.Application({"url": "https://yoda.ua"})


def test_item(testapp):
    """Archive processor has to work!"""

    stream = archive.process(
        testapp,
        [
            core.Item(
                {
                    "title": "the way of the Force",
                    "content": "Obi-Wan",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "title": "the way of the Force",
            "content": "Obi-Wan",
        })

    assert next(stream) == core.WebSiteItem(
        {
            "source": "archive://index.html",
            "destination": "index.html",
            "template": "archive.j2",
            "items": [
                core.Item(
                    {
                        "title": "the way of the Force",
                        "content": "Obi-Wan"
                    }),
            ],
            "baseurl": testapp.metadata["url"],
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """archive processor has to work with stream."""

    stream = archive.process(
        testapp,
        [
            core.Item({"title": "the way of the Force #%d" % i})
            for i in range(amount)
        ])

    for i in range(amount):
        assert next(stream) == core.Item(
            {
                "title": "the way of the Force #%d" % i,
            })

    assert next(stream) == core.WebSiteItem(
        {
            "source": "archive://index.html",
            "destination": "index.html",
            "template": "archive.j2",
            "items": [
                core.Item({"title": "the way of the Force #%d" % i})
                for i in range(amount)
            ],
            "baseurl": testapp.metadata["url"],
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_param_template(testapp):
    """archive processor has respect template parameter."""

    stream = archive.process(
        testapp,
        [
            core.Item(
                {
                    "title": "the way of the Force",
                    "content": "Obi-Wan",
                }),
        ],
        template="foobar.txt")

    assert next(stream) == core.Item(
        {
            "title": "the way of the Force",
            "content": "Obi-Wan",
        })

    assert next(stream) == core.WebSiteItem(
        {
            "source": "archive://index.html",
            "destination": "index.html",
            "template": "foobar.txt",
            "items": [
                core.Item(
                    {
                        "title": "the way of the Force",
                        "content": "Obi-Wan",
                    }),
            ],
            "baseurl": testapp.metadata["url"],
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("save_as", [
    os.path.join("posts", "skywalker.luke"),
    os.path.join("yoda.jedi"),
])
def test_param_save_as(testapp, save_as):
    """archive processor has to respect save_as parameter."""

    stream = archive.process(
        testapp,
        [
            core.Item(
                {
                    "title": "the way of the Force",
                    "content": "Obi-Wan",
                }),
        ],
        save_as=save_as)

    assert next(stream) == core.Item(
        {
            "title": "the way of the Force",
            "content": "Obi-Wan",
        })

    assert next(stream) == core.WebSiteItem(
        {
            "source": "archive://%s" % save_as,
            "destination": save_as,
            "template": "archive.j2",
            "items": [
                core.Item(
                    {
                        "title": "the way of the Force",
                        "content": "Obi-Wan",
                    }),
            ],
            "baseurl": testapp.metadata["url"],
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("params, error", [
    ({"save_as": 42}, "save_as: 42 is not of type 'string'"),
    ({"template": 42}, "template: 42 is not of type 'string'"),
    ({"save_as": [42]}, "save_as: [42] is not of type 'string'"),
    ({"template": [42]}, "template: [42] is not of type 'string'"),
    ({"save_as": {"x": 1}}, "save_as: {'x': 1} is not of type 'string'"),
    ({"template": {"y": 2}}, "template: {'y': 2} is not of type 'string'"),
])
def test_param_bad_value(testapp, params, error):
    """archive processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(archive.process(testapp, [], **params))
    assert str(excinfo.value) == error
