"""Archive processor test suite."""

import collections.abc
import itertools
import os

import pytest

import holocron
from holocron._processors import archive


@pytest.fixture(scope="function")
def testapp():
    return holocron.Application({"url": "https://yoda.ua"})


def test_item(testapp):
    """Archive processor has to work!"""

    stream = archive.process(
        testapp, [holocron.Item({"title": "The Force", "content": "Obi-Wan"})]
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"title": "The Force", "content": "Obi-Wan"}),
        holocron.WebSiteItem(
            {
                "source": "archive://index.html",
                "destination": "index.html",
                "template": "archive.j2",
                "items": [
                    holocron.Item({"title": "The Force", "content": "Obi-Wan"})
                ],
                "baseurl": testapp.metadata["url"],
            }
        ),
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
    """archive processor has to work with stream."""

    stream = archive.process(
        testapp,
        [
            holocron.Item({"title": "The Force (part #%d)" % i})
            for i in range(amount)
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == list(
        itertools.chain(
            [
                holocron.Item({"title": "The Force (part #%d)" % i})
                for i in range(amount)
            ],
            [
                holocron.WebSiteItem(
                    {
                        "source": "archive://index.html",
                        "destination": "index.html",
                        "template": "archive.j2",
                        "items": [
                            holocron.Item(
                                {"title": "The Force (part #%d)" % i}
                            )
                            for i in range(amount)
                        ],
                        "baseurl": testapp.metadata["url"],
                    }
                )
            ],
        )
    )


def test_param_template(testapp):
    """archive processor has respect template parameter."""

    stream = archive.process(
        testapp,
        [holocron.Item({"title": "The Force", "content": "Obi-Wan"})],
        template="foobar.txt",
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"title": "The Force", "content": "Obi-Wan"}),
        holocron.WebSiteItem(
            {
                "source": "archive://index.html",
                "destination": "index.html",
                "template": "foobar.txt",
                "items": [
                    holocron.Item({"title": "The Force", "content": "Obi-Wan"})
                ],
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["save_as"],
    [
        pytest.param(os.path.join("posts", "skywalker.luke"), id="deep"),
        pytest.param(os.path.join("yoda.jedi"), id="flat"),
    ],
)
def test_param_save_as(testapp, save_as):
    """archive processor has to respect save_as parameter."""

    stream = archive.process(
        testapp,
        [holocron.Item({"title": "The Force", "content": "Obi-Wan"})],
        save_as=save_as,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"title": "The Force", "content": "Obi-Wan"}),
        holocron.WebSiteItem(
            {
                "source": "archive://%s" % save_as,
                "destination": save_as,
                "template": "archive.j2",
                "items": [
                    holocron.Item({"title": "The Force", "content": "Obi-Wan"})
                ],
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["params", "error"],
    [
        pytest.param(
            {"save_as": 42},
            "save_as: 42 is not of type 'string'",
            id="save_as-int",
        ),
        pytest.param(
            {"template": 42},
            "template: 42 is not of type 'string'",
            id="template-int",
        ),
        pytest.param(
            {"save_as": [42]},
            "save_as: [42] is not of type 'string'",
            id="save_as-list",
        ),
        pytest.param(
            {"template": [42]},
            "template: [42] is not of type 'string'",
            id="template-list",
        ),
        pytest.param(
            {"save_as": {"x": 1}},
            "save_as: {'x': 1} is not of type 'string'",
            id="save_as-dict",
        ),
        pytest.param(
            {"template": {"y": 2}},
            "template: {'y': 2} is not of type 'string'",
            id="template-dict",
        ),
    ],
)
def test_param_bad_value(testapp, params, error):
    """archive processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(archive.process(testapp, [], **params))
    assert str(excinfo.value) == error
