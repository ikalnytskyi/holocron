"""Chain processor test suite."""

import collections.abc

import pytest

import holocron
from holocron._processors import chain


@pytest.fixture(scope="function")
def testapp():
    return holocron.Application()


def test_one_item(testapp):
    """Chain processor has to work with one item!"""

    stream = chain.process(
        testapp, [holocron.Item({"title": "The Force", "content": "Obi-Wan"})]
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item({"title": "The Force", "content": "Obi-Wan"})
    ]


def test_two_items(testapp):
    """Chain processor has to work with two items!"""

    stream = chain.process(
        testapp,
        [
            holocron.Item({"title": "The Force", "content": "Obi-Wan"}),
            holocron.Item({"title": "Force, The", "content": "Yoda"}),
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    items = list(stream)

    assert items == [
        holocron.Item(
            {"title": "The Force", "content": "Obi-Wan", "next": items[1]}
        ),
        holocron.Item(
            {"title": "Force, The", "content": "Yoda", "prev": items[0]}
        ),
    ]


def test_three_items(testapp):
    """Chain processor has to work with three items!"""

    stream = chain.process(
        testapp,
        [
            holocron.Item({"title": "The Force", "content": "Obi-Wan"}),
            holocron.Item({"title": "Force, The", "content": "Yoda"}),
            holocron.Item({"title": "The Dark Side", "content": "Vader"}),
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    items = list(stream)

    assert items == [
        holocron.Item(
            {"title": "The Force", "content": "Obi-Wan", "next": items[1]}
        ),
        holocron.Item(
            {
                "title": "Force, The",
                "content": "Yoda",
                "prev": items[0],
                "next": items[2],
            }
        ),
        holocron.Item(
            {"title": "The Dark Side", "content": "Vader", "prev": items[1]}
        ),
    ]


def test_param_order_by(testapp):
    """Chain processor has to respect 'order_by' parameter."""

    stream = chain.process(
        testapp,
        [
            holocron.Item(
                {"title": "The Dark Side", "content": "Vader", "id": 3}
            ),
            holocron.Item(
                {"title": "The Force", "content": "Obi-Wan", "id": 1}
            ),
            holocron.Item({"title": "Force, The", "content": "Yoda", "id": 2}),
        ],
        order_by="id",
    )

    assert isinstance(stream, collections.abc.Iterable)
    items = list(stream)

    assert items == [
        holocron.Item(
            {
                "title": "The Force",
                "content": "Obi-Wan",
                "next": items[1],
                "id": 1,
            }
        ),
        holocron.Item(
            {
                "title": "Force, The",
                "content": "Yoda",
                "prev": items[0],
                "next": items[2],
                "id": 2,
            }
        ),
        holocron.Item(
            {
                "title": "The Dark Side",
                "content": "Vader",
                "prev": items[1],
                "id": 3,
            }
        ),
    ]


def test_param_direction(testapp):
    """Chain processor has to respect 'direction' parameter."""

    stream = chain.process(
        testapp,
        [
            holocron.Item(
                {"title": "The Dark Side", "content": "Vader", "id": 3}
            ),
            holocron.Item(
                {"title": "The Force", "content": "Obi-Wan", "id": 1}
            ),
            holocron.Item({"title": "Force, The", "content": "Yoda", "id": 2}),
        ],
        order_by="id",
        direction="desc",
    )

    assert isinstance(stream, collections.abc.Iterable)
    items = list(stream)

    assert items == [
        holocron.Item(
            {
                "title": "The Dark Side",
                "content": "Vader",
                "next": items[1],
                "id": 3,
            }
        ),
        holocron.Item(
            {
                "title": "Force, The",
                "content": "Yoda",
                "prev": items[0],
                "next": items[2],
                "id": 2,
            }
        ),
        holocron.Item(
            {
                "title": "The Force",
                "content": "Obi-Wan",
                "prev": items[1],
                "id": 1,
            }
        ),
    ]


@pytest.mark.parametrize(
    ["params", "error"],
    [
        pytest.param(
            {"order_by": 42},
            "order_by: 42 is not of type 'string'",
            id="save_as-int",
        ),
        pytest.param(
            {"order_by": "yoda", "direction": 42},
            "direction: 42 is not of type 'string'",
            id="template-int",
        ),
        pytest.param(
            {"order_by": "yoda", "direction": "luke"},
            "direction: 'luke' is not one of ['asc', 'desc']",
            id="template-int",
        ),
    ],
)
def test_param_bad_value(testapp, params, error):
    """Chain processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(chain.process(testapp, [], **params))
    assert str(excinfo.value) == error
