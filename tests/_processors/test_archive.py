"""Archive processor test suite."""

import collections.abc
import itertools
import pathlib

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
                "source": pathlib.Path("archive://index.html"),
                "destination": pathlib.Path("index.html"),
                "template": "archive.j2",
                "items": [holocron.Item({"title": "The Force", "content": "Obi-Wan"})],
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
    """Archive processor has to work with stream."""

    stream = archive.process(
        testapp,
        [holocron.Item({"title": "The Force (part #%d)" % i}) for i in range(amount)],
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
                        "source": pathlib.Path("archive://index.html"),
                        "destination": pathlib.Path("index.html"),
                        "template": "archive.j2",
                        "items": [
                            holocron.Item({"title": "The Force (part #%d)" % i})
                            for i in range(amount)
                        ],
                        "baseurl": testapp.metadata["url"],
                    }
                )
            ],
        )
    )


def test_args_template(testapp):
    """Archive processor has respect 'template' argument."""

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
                "source": pathlib.Path("archive://index.html"),
                "destination": pathlib.Path("index.html"),
                "template": "foobar.txt",
                "items": [holocron.Item({"title": "The Force", "content": "Obi-Wan"})],
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["save_as"],
    [
        pytest.param(pathlib.Path("posts", "skywalker.luke"), id="deep"),
        pytest.param(pathlib.Path("yoda.jedi"), id="flat"),
    ],
)
def test_args_save_as(testapp, save_as):
    """Archive processor has to respect 'save_as' argument."""

    stream = archive.process(
        testapp,
        [holocron.Item({"title": "The Force", "content": "Obi-Wan"})],
        save_as=str(save_as),
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"title": "The Force", "content": "Obi-Wan"}),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("archive://", save_as),
                "destination": save_as,
                "template": "archive.j2",
                "items": [holocron.Item({"title": "The Force", "content": "Obi-Wan"})],
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["args", "error"],
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
def test_args_bad_value(testapp, args, error):
    """Archive processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(archive.process(testapp, [], **args))
    assert str(excinfo.value) == error
