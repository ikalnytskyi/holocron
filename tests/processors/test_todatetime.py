"""Todatetime processor test suite."""

import datetime

import pytest
import dateutil.tz

from holocron import core
from holocron.processors import todatetime


_TZ_UTC = dateutil.tz.gettz("UTC")
_TZ_EET = dateutil.tz.gettz("EET")


@pytest.fixture(scope="function")
def testapp():
    return core.Application()


@pytest.mark.parametrize(
    "timestamp, parsed",
    [
        (
            "2019-01-15T21:07:07+00:00",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07:07+00",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07:07Z",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07:07",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07+00:00",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07+00",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07Z",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07",
            datetime.datetime(2019, 1, 15, 21, 7, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21+00:00",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21+00",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21Z",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21",
            datetime.datetime(2019, 1, 15, 21, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15",
            datetime.datetime(2019, 1, 15, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
            "20190115T210707Z",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_UTC),
        ),
        (
            "2019-01-15T21:07:07+02:00",
            datetime.datetime(2019, 1, 15, 21, 7, 7, tzinfo=_TZ_EET),
        ),
        (
            "2019/01/11",
            datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
            "01/11/2019",
            datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
            "01-11-2019",
            datetime.datetime(2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC),
        ),
        (
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
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": timestamp,
                }
            )
        ],
        todatetime="timestamp",
    )

    assert next(stream) == core.Item(
        {"content": "the Force is strong with this one", "timestamp": parsed}
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Todatetime processor has to work with stream."""

    stream = todatetime.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "2019-01-%d" % (i + 1),
                }
            )
            for i in range(amount)
        ],
        todatetime="timestamp",
    )

    for i, item in zip(range(amount), stream):
        assert item == core.Item(
            {
                "content": "the Force is strong with this one",
                "timestamp": datetime.datetime(2019, 1, i + 1, tzinfo=_TZ_UTC),
            }
        )

    with pytest.raises(StopIteration):
        next(stream)


def test_item_timestamp_missing(testapp):
    """Todatetime processor has to ignore items with missing timestamp."""

    stream = todatetime.process(
        testapp,
        [core.Item({"content": "the Force is strong with this one"})],
        todatetime="timestamp",
    )

    assert next(stream) == core.Item(
        {"content": "the Force is strong with this one"}
    )

    with pytest.raises(StopIteration):
        next(stream)


def test_item_timestamp_bad_value(testapp):
    """Todatetime processor has to error if a timestamp cannot be parsed."""

    stream = todatetime.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "yoda",
                }
            )
        ],
        todatetime="timestamp",
    )

    with pytest.raises(Exception) as excinfo:
        next(stream)
        assert str(excinfo.value) == "('Unknown string format:', 'yoda')"

    with pytest.raises(StopIteration):
        next(stream)


def test_param_todatetime(testapp):
    """Todatetime processor has to respect "writeto" parameter."""

    stream = todatetime.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "2019-01-11",
                }
            )
        ],
        todatetime=["timestamp", "published"],
    )

    assert next(stream) == core.Item(
        {
            "content": "the Force is strong with this one",
            "timestamp": "2019-01-11",
            "published": datetime.datetime(
                2019, 1, 11, 0, 0, 0, tzinfo=_TZ_UTC
            ),
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    "timestamp, parsearea",
    [
        ("2019/01/11/luke-skywalker-part-1.txt", r"\d{4}/\d{2}/\d{2}"),
        ("2019-01-11-luke-skywalker-part-1.txt", r"\d{4}-\d{2}-\d{2}"),
        ("2019/01/11/luke-skywalker-part-1.txt", r"\d{4}.\d{2}.\d{2}"),
        ("2019-01-11-luke-skywalker-part-1.txt", r"\d{4}.\d{2}.\d{2}"),
    ],
)
def test_param_parsearea(testapp, timestamp, parsearea):
    """Todatetime processor has to respect "parsearea" parameter."""

    stream = todatetime.process(
        testapp,
        [
            core.Item(
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

    assert next(stream) == core.Item(
        {
            "content": "the Force is strong with this one",
            "timestamp": datetime.datetime(2019, 1, 11, tzinfo=_TZ_UTC),
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


def test_param_parsearea_not_found(testapp):
    """Todatetime processor has to respect "parsearea" parameter."""

    stream = todatetime.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "luke-skywalker-part-1.txt",
                }
            )
        ],
        todatetime="timestamp",
        parsearea=r"\d{4}-\d{2}-\d{2}",
    )

    assert next(stream) == core.Item(
        {
            "content": "the Force is strong with this one",
            "timestamp": "luke-skywalker-part-1.txt",
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    "timestamp",
    [
        "2019/01/11/luke-skywalker.txt",
        "2019/01/11/luke-skywalker/index.txt",
        "/2019/01/11/luke-skywalker.txt",
        "/2019/01/11/luke-skywalker/index.txt",
        "http://example.com/2019/01/11/luke-skywalker.txt",
        "http://example.com/2019/01/11/luke-skywalker/index.txt",
        "2019-01-11-luke-skywalker.txt",
        "posts/2019-01-11-luke-skywalker.txt",
        "/posts/2019-01-11-luke-skywalker.txt",
        "http://example.com/posts/2019-01-11-luke-skywalker.txt",
    ],
)
def test_param_fuzzy(testapp, timestamp):
    """Todatetime processor has to respect "fuzzy" parameter."""

    stream = todatetime.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": timestamp,
                }
            )
        ],
        todatetime="timestamp",
        fuzzy=True,
    )

    assert next(stream) == core.Item(
        {
            "content": "the Force is strong with this one",
            "timestamp": datetime.datetime(2019, 1, 11, tzinfo=_TZ_UTC),
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("tz", ["EET", "UTC"])
def test_param_timezone(testapp, tz):
    """Todatetime processor has to respect "timezone" parameter."""

    stream = todatetime.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "2019-01-15T21:07+00:00",
                }
            ),
            core.Item(
                {
                    "content": "may the Force be with you",
                    "timestamp": "2019-01-15T21:07",
                }
            ),
        ],
        todatetime="timestamp",
        # Custom timezone has to be attached only to timestamps without
        # explicit timezone information. So this option is nothing more
        # but a fallback.
        timezone=tz,
    )

    assert next(stream) == core.Item(
        {
            "content": "the Force is strong with this one",
            "timestamp": datetime.datetime(2019, 1, 15, 21, 7, tzinfo=_TZ_UTC),
        }
    )

    assert next(stream) == core.Item(
        {
            "content": "may the Force be with you",
            "timestamp": datetime.datetime(
                2019, 1, 15, 21, 7, tzinfo=dateutil.tz.gettz(tz)
            ),
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("tz", ["EET", "UTC"])
def test_param_timezone_fallback(testapp, tz):
    """Todatetime processor has to respect "timezone" parameter (fallback)."""

    # Custom timezone has to be attached only to timestamps without
    # explicit timezone information. So this option is nothing more
    # but a fallback.
    testapp.metadata.update({"timezone": tz})

    stream = todatetime.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the Force is strong with this one",
                    "timestamp": "2019-01-15T21:07+00:00",
                }
            ),
            core.Item(
                {
                    "content": "may the Force be with you",
                    "timestamp": "2019-01-15T21:07",
                }
            ),
        ],
        todatetime="timestamp",
    )

    assert next(stream) == core.Item(
        {
            "content": "the Force is strong with this one",
            "timestamp": datetime.datetime(2019, 1, 15, 21, 7, tzinfo=_TZ_UTC),
        }
    )

    assert next(stream) == core.Item(
        {
            "content": "may the Force be with you",
            "timestamp": datetime.datetime(
                2019, 1, 15, 21, 7, tzinfo=dateutil.tz.gettz(tz)
            ),
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    "params, error",
    [
        ({"todatetime": 42}, "todatetime: unsupported todatetime"),
        ({"parsearea": 42}, "parsearea: unsupported regexp"),
        ({"timezone": "Europe/Kharkiv"}, "timezone: unsupported timezone"),
        ({"fuzzy": 42}, "fuzzy: 42 should be instance of 'bool'"),
    ],
)
def test_param_bad_value(testapp, params, error):
    """Todatetime processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(todatetime.process(testapp, [], **params))
