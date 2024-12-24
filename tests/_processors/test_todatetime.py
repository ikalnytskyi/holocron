"""Todatetime processor test suite."""

import collections.abc
import datetime
import pathlib

import dateutil.tz
import pytest

import holocron
from holocron._processors import todatetime

_TZ_UTC = dateutil.tz.gettz("UTC")
_TZ_EET = dateutil.tz.gettz("EET")


@pytest.fixture
def testapp():
    return holocron.Application()


@pytest.mark.parametrize(
    ("timestamp", "parsed"),
    [
        pytest.param(
            "2019-01-15T21:07:07+00:00",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07:07+00",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07:07Z",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07:07",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07+00:00",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07+00",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07Z",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21+00:00",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21+00",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21Z",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15",
            datetime.datetime(2019, 1, 15, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "20190115T210707Z",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "2019-01-15T21:07:07+02:00",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_EET),
        ),
        pytest.param(
            "2019/01/11",
            datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "01/11/2019",
            datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "01-11-2019",
            datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        pytest.param(
            "01.11.2019",
            datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
    ],
)
def test_item(testapp, timestamp, parsed):
    """Todatetime processor has to work."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": timestamp,
                }
            )
        ],
        todatetime="timestamp",
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": parsed,
            }
        )
    ]


@pytest.mark.parametrize(
    "amount",
    [
        pytest.param(0),
        pytest.param(1),
        pytest.param(2),
        pytest.param(5),
        pytest.param(10),
    ],
)
def test_item_many(testapp, amount):
    """Todatetime processor has to work with stream."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "2019-01-%d" % (i + 1),
                }
            )
            for i in range(amount)
        ],
        todatetime="timestamp",
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": datetime.datetime(2019, 1, i + 1, tzinfo=_TZ_UTC),
            }
        )
        for i in range(amount)
    ]


def test_item_timestamp_missing(testapp):
    """Todatetime processor has to ignore items with missing timestamp."""

    stream = todatetime.process(
        testapp,
        [holocron.Item({"content": "the Force is strong with this one"})],
        todatetime="timestamp",
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [holocron.Item({"content": "the Force is strong with this one"})]


def test_item_timestamp_bad_value(testapp):
    """Todatetime processor has to error if a timestamp cannot be parsed."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "yoda",
                }
            )
        ],
        todatetime="timestamp",
    )

    assert isinstance(stream, collections.abc.Iterable)

    with pytest.raises(Exception) as excinfo:
        next(stream)
        assert str(excinfo.value) == "('Unknown string format:', 'yoda')"


@pytest.mark.parametrize(
    "timestamp",
    [
        pytest.param("2019-01-11", id="str"),
        pytest.param(pathlib.Path("2019-01-11"), id="path"),
    ],
)
def test_args_todatetime(testapp, timestamp):
    """Todatetime processor has to respect "writeto" argument."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": timestamp,
                }
            )
        ],
        todatetime=["timestamp", "published"],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": timestamp,
                "published": datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
            }
        )
    ]


@pytest.mark.parametrize(
    ("timestamp", "parsearea"),
    [
        pytest.param("2019/01/11/luke-skywalker-part-1.txt", r"\d{4}/\d{2}/\d{2}"),
        pytest.param("2019-01-11-luke-skywalker-part-1.txt", r"\d{4}-\d{2}-\d{2}"),
        pytest.param("2019/01/11/luke-skywalker-part-1.txt", r"\d{4}.\d{2}.\d{2}"),
        pytest.param("2019-01-11-luke-skywalker-part-1.txt", r"\d{4}.\d{2}.\d{2}"),
    ],
)
def test_args_parsearea(testapp, timestamp, parsearea):
    """Todatetime processor has to respect "parsearea" argument."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": timestamp,
                }
            )
        ],
        todatetime="timestamp",
        parsearea=parsearea,
        fuzzy=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": datetime.datetime(2019, 1, 11, tzinfo=_TZ_UTC),
            }
        )
    ]


def test_args_parsearea_not_found(testapp):
    """Todatetime processor has to respect "parsearea" argument."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "luke-skywalker-part-1.txt",
                }
            )
        ],
        todatetime="timestamp",
        parsearea=r"\d{4}-\d{2}-\d{2}",
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": "luke-skywalker-part-1.txt",
            }
        )
    ]


@pytest.mark.parametrize(
    "timestamp",
    [
        pytest.param("2019/01/11/luke-skywalker.txt"),
        pytest.param("2019/01/11/luke-skywalker/index.txt"),
        pytest.param("/2019/01/11/luke-skywalker.txt"),
        pytest.param("/2019/01/11/luke-skywalker/index.txt"),
        pytest.param("http://example.com/2019/01/11/luke-skywalker.txt"),
        pytest.param("http://example.com/2019/01/11/luke-skywalker/index.txt"),
        pytest.param("2019-01-11-luke-skywalker.txt"),
        pytest.param("posts/2019-01-11-luke-skywalker.txt"),
        pytest.param("/posts/2019-01-11-luke-skywalker.txt"),
        pytest.param("http://example.com/posts/2019-01-11-luke-skywalker.txt"),
    ],
)
def test_args_fuzzy(testapp, timestamp):
    """Todatetime processor has to respect "fuzzy" argument."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": timestamp,
                }
            )
        ],
        todatetime="timestamp",
        fuzzy=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": datetime.datetime(2019, 1, 11, tzinfo=_TZ_UTC),
            }
        )
    ]


@pytest.mark.parametrize("tz", [pytest.param("EET"), pytest.param("UTC")])
def test_args_timezone(testapp, tz):
    """Todatetime processor has to respect "timezone" argument."""

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "2019-01-15T21:07+00:00",
                }
            ),
            holocron.Item(
                {
                    "content": "may the Force be with you",
                    "timestamp": "2019-01-15T21:07",
                }
            ),
        ],
        todatetime="timestamp",
        # Custom timezone has to be attached only to timestamps without
        # explicit timezone information. So this argument is nothing more
        # but a fallback.
        timezone=tz,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": datetime.datetime(2019, 1, 15, 21, 7, tzinfo=_TZ_UTC),
            }
        ),
        holocron.Item(
            {
                "content": "may the Force be with you",
                "timestamp": datetime.datetime(2019, 1, 15, 21, 7, tzinfo=dateutil.tz.gettz(tz)),
            }
        ),
    ]


@pytest.mark.parametrize("tz", [pytest.param("EET"), pytest.param("UTC")])
def test_args_timezone_fallback(testapp, tz):
    """Todatetime processor has to respect "timezone" argument (fallback)."""

    # Custom timezone has to be attached only to timestamps without
    # explicit timezone information. So this option is nothing more
    # but a fallback.
    testapp.metadata.update({"timezone": tz})

    stream = todatetime.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "2019-01-15T21:07+00:00",
                }
            ),
            holocron.Item(
                {
                    "content": "may the Force be with you",
                    "timestamp": "2019-01-15T21:07",
                }
            ),
        ],
        todatetime="timestamp",
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": datetime.datetime(2019, 1, 15, 21, 7, tzinfo=_TZ_UTC),
            }
        ),
        holocron.Item(
            {
                "content": "may the Force be with you",
                "timestamp": datetime.datetime(2019, 1, 15, 21, 7, tzinfo=dateutil.tz.gettz(tz)),
            }
        ),
    ]


@pytest.mark.parametrize(
    ("args", "error"),
    [
        pytest.param(
            {"todatetime": 42},
            "todatetime: 42 is not valid under any of the given schemas",
            id="todatetime-int",
        ),
        pytest.param(
            {"parsearea": 42},
            "parsearea: 42 is not of type 'string'",
            id="parsearea-int",
        ),
        pytest.param(
            {"timezone": "Europe/Kharkiv"},
            "timezone: 'Europe/Kharkiv' is not a 'timezone'",
            id="timezone-wrong",
        ),
        pytest.param({"fuzzy": 42}, "fuzzy: 42 is not of type 'boolean'", id="fuzzy-int"),
    ],
)
def test_args_bad_value(testapp, args, error):
    """Todatetime processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(todatetime.process(testapp, [], **args))
    assert str(excinfo.value) == error
