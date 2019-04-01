"""Source processor test suite."""

import collections.abc
import os
import unittest.mock

import pytest

from holocron import core
from holocron.processors import source


class _pytest_timestamp:
    """Assert that a given timestamp is equal to a datetime object."""

    def __init__(self, timestamp, abs_=0.001):
        self._timestamp = timestamp
        self._abs = abs_

    def __eq__(self, actual):
        return actual.timestamp() == pytest.approx(
            self._timestamp, abs=self._abs
        )

    def __repr__(self):
        return self._timestamp


@pytest.fixture(scope="function")
def testapp():
    return core.Application({"url": "https://yoda.ua"})


@pytest.mark.parametrize(
    ["path"],
    [
        pytest.param(["about", "luke", "cv.pdf"], id="deep-subdir"),
        pytest.param(["about", "cv.pdf"], id="subdir"),
        pytest.param(["cv.pdf"], id="flat"),
        pytest.param([".post"], id="hidden"),
    ],
)
def test_item(testapp, monkeypatch, tmpdir, path):
    """Source processor has to work."""

    monkeypatch.chdir(tmpdir)
    tmpdir.ensure(*path).write_text("Obi-Wan", encoding="UTF-8")

    stream = source.process(testapp, [])

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.WebSiteItem(
            {
                "source": os.path.join(*path),
                "destination": os.path.join(*path),
                "content": "Obi-Wan",
                "created": _pytest_timestamp(tmpdir.join(*path).stat().ctime),
                "updated": _pytest_timestamp(tmpdir.join(*path).stat().mtime),
                "baseurl": testapp.metadata["url"],
            }
        )
    ]


@pytest.mark.parametrize(
    ["data"], [pytest.param("text"), pytest.param(b"\xf1")]
)
def test_item_content_types(testapp, monkeypatch, tmpdir, data):
    """Source processor has to properly read items" content."""

    monkeypatch.chdir(tmpdir)
    localpath = tmpdir.ensure("cv.md")

    if isinstance(data, bytes):
        localpath.write_binary(data)
    else:
        localpath.write_text(data, encoding="UTF-8")

    stream = source.process(testapp, [])

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.WebSiteItem(
            {
                "source": "cv.md",
                "destination": "cv.md",
                "content": data,
                "created": _pytest_timestamp(
                    tmpdir.join("cv.md").stat().ctime
                ),
                "updated": _pytest_timestamp(
                    tmpdir.join("cv.md").stat().mtime
                ),
                "baseurl": testapp.metadata["url"],
            }
        )
    ]


def test_item_empty(testapp, monkeypatch, tmpdir):
    """Source processor has to properly read empty items."""

    monkeypatch.chdir(tmpdir)
    tmpdir.ensure("cv.md").write_binary(b"")

    stream = source.process(testapp, [])

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.WebSiteItem(
            {
                "source": "cv.md",
                "destination": "cv.md",
                "content": "",
                "created": _pytest_timestamp(
                    tmpdir.join("cv.md").stat().ctime
                ),
                "updated": _pytest_timestamp(
                    tmpdir.join("cv.md").stat().mtime
                ),
                "baseurl": testapp.metadata["url"],
            }
        )
    ]


@pytest.mark.parametrize(
    ["discovered"],
    [
        pytest.param(0),
        pytest.param(1),
        pytest.param(2),
        pytest.param(5),
        pytest.param(10),
    ],
)
@pytest.mark.parametrize(
    ["passed"],
    [
        pytest.param(0),
        pytest.param(1),
        pytest.param(2),
        pytest.param(5),
        pytest.param(10),
    ],
)
def test_item_many(testapp, monkeypatch, tmpdir, discovered, passed):
    """Source processor has to preserve documents and produce many new."""

    monkeypatch.chdir(tmpdir)

    for i in range(discovered):
        tmpdir.join(str(i)).write_text("key=%d" % i, encoding="UTF-8")

    stream = source.process(
        testapp,
        [core.Item({"marker": "the key is %d" % i}) for i in range(passed)],
    )

    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items[:passed] == [
        core.Item({"marker": "the key is %d" % i}) for i in range(passed)
    ]

    # Since we don"t know in which order items are discovered, we sort them so
    # we can avoid possible flakes of the test.
    assert sorted(items[passed:], key=lambda item: item["source"]) == [
        core.WebSiteItem(
            {
                "source": str(i),
                "destination": str(i),
                "content": "key=%d" % i,
                "created": _pytest_timestamp(tmpdir.join(str(i)).stat().ctime),
                "updated": _pytest_timestamp(tmpdir.join(str(i)).stat().mtime),
                "baseurl": testapp.metadata["url"],
            }
        )
        for i in range(discovered)
    ]


@pytest.mark.parametrize(
    ["path"],
    [
        pytest.param(["a"]),
        pytest.param(["a", "b"]),
        pytest.param(["a", "b", "c"]),
    ],
)
def test_param_path(testapp, monkeypatch, tmpdir, path):
    """Source processor has to respect path parameter."""

    monkeypatch.chdir(tmpdir)
    tmpdir.join(*path).ensure("test").write_text("Obi-Wan", encoding="UTF-8")

    stream = source.process(testapp, [], path=tmpdir.join(*path).strpath)

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.WebSiteItem(
            {
                "source": "test",
                "destination": "test",
                "content": "Obi-Wan",
                "created": _pytest_timestamp(
                    tmpdir.join(*path).join("test").stat().ctime
                ),
                "updated": _pytest_timestamp(
                    tmpdir.join(*path).join("test").stat().mtime
                ),
                "baseurl": testapp.metadata["url"],
            }
        )
    ]


def test_param_pattern(testapp, monkeypatch, tmpdir):
    """Source processor has to respect pattern parameter."""

    monkeypatch.chdir(tmpdir)

    tmpdir.join("1.md").write_text("Skywalker", encoding="UTF-8")
    tmpdir.join("2.txt").write_text("Obi-Wan", encoding="UTF-8")
    tmpdir.join("3.rst").write_text("Vader", encoding="UTF-8")
    tmpdir.join("4.markdown").write_text("Yoda", encoding="UTF-8")

    stream = source.process(testapp, [], pattern=r".*\.(md|markdown)")
    assert isinstance(stream, collections.abc.Iterable)

    # Since we don"t know in which order items are discovered, we sort them so
    # we can avoid possible flakes of the test.
    assert sorted(stream, key=lambda item: item["source"]) == [
        core.WebSiteItem(
            {
                "source": "1.md",
                "destination": "1.md",
                "content": "Skywalker",
                "created": _pytest_timestamp(tmpdir.join("1.md").stat().ctime),
                "updated": _pytest_timestamp(tmpdir.join("1.md").stat().mtime),
                "baseurl": testapp.metadata["url"],
            }
        ),
        core.WebSiteItem(
            {
                "source": "4.markdown",
                "destination": "4.markdown",
                "content": "Yoda",
                "created": _pytest_timestamp(
                    tmpdir.join("4.markdown").stat().ctime
                ),
                "updated": _pytest_timestamp(
                    tmpdir.join("4.markdown").stat().mtime
                ),
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["encoding"], [pytest.param("CP1251"), pytest.param("UTF-16")]
)
def test_param_encoding(testapp, monkeypatch, tmpdir, encoding):
    """Source processor has to respect encoding parameter."""

    monkeypatch.chdir(tmpdir)
    tmpdir.ensure("cv.md").write_text("Оби-Ван", encoding=encoding)

    stream = source.process(testapp, [], encoding=encoding)

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.WebSiteItem(
            {
                "source": "cv.md",
                "destination": "cv.md",
                "content": "Оби-Ван",
                "created": unittest.mock.ANY,
                "updated": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        )
    ]


@pytest.mark.parametrize(
    ["encoding"], [pytest.param("CP1251"), pytest.param("UTF-16")]
)
def test_param_encoding_fallback(testapp, monkeypatch, tmpdir, encoding):
    """Source processor has to respect encoding parameter (fallback)."""

    monkeypatch.chdir(tmpdir)
    tmpdir.ensure("cv.md").write_text("Оби-Ван", encoding=encoding)
    testapp.metadata.update({"encoding": encoding})

    stream = source.process(testapp, [])

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.WebSiteItem(
            {
                "source": "cv.md",
                "destination": "cv.md",
                "content": "Оби-Ван",
                "created": unittest.mock.ANY,
                "updated": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        )
    ]


@pytest.mark.parametrize(
    ["timezone", "tznames"],
    [
        pytest.param("UTC", ["UTC"]),
        pytest.param("Europe/Kiev", ["EET", "EEST"]),
    ],
)
def test_param_timezone(testapp, monkeypatch, tmpdir, timezone, tznames):
    """Source processor has to respect timezone parameter."""

    monkeypatch.chdir(tmpdir)
    tmpdir.ensure("cv.md").write_text("Obi-Wan", encoding="UTF-8")

    stream = source.process(testapp, [], timezone=timezone)
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert len(items) == 1

    created = items[0]["created"]
    updated = items[0]["updated"]

    assert created.tzinfo.tzname(created) in tznames
    assert updated.tzinfo.tzname(updated) in tznames


@pytest.mark.parametrize(
    ["tz", "tznames"],
    [
        pytest.param("UTC", ["UTC"]),
        pytest.param("Europe/Kiev", ["EET", "EEST"]),
    ],
)
def test_param_timezone_fallback(testapp, monkeypatch, tmpdir, tz, tznames):
    """Source processor has to respect timezone parameter (fallback)."""

    monkeypatch.chdir(tmpdir)
    tmpdir.ensure("cv.md").write_text("Obi-Wan", encoding="UTF-8")
    testapp.metadata.update({"timezone": tz})

    stream = source.process(testapp, [])
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert len(items) == 1

    created = items[0]["created"]
    updated = items[0]["updated"]

    assert created.tzinfo.tzname(created) in tznames
    assert updated.tzinfo.tzname(updated) in tznames


def test_param_timezone_in_action(testapp, monkeypatch, tmpdir):
    """Source processor has to respect timezone parameter."""

    monkeypatch.chdir(tmpdir)
    tmpdir.ensure("cv.md").write_text("Obi-Wan", encoding="UTF-8")

    stream_utc = source.process(testapp, [], timezone="UTC")
    stream_kie = source.process(testapp, [], timezone="Europe/Kiev")

    assert isinstance(stream_utc, collections.abc.Iterable)
    assert isinstance(stream_kie, collections.abc.Iterable)

    items_utc = list(stream_utc)
    items_kie = list(stream_kie)

    assert len(items_utc) == 1
    assert len(items_kie) == 1

    created_utc = items_utc[0]["created"]
    created_kie = items_kie[0]["created"]

    assert created_kie.tzinfo.utcoffset(
        created_kie
    ) >= created_utc.tzinfo.utcoffset(created_utc)
    assert created_kie.isoformat() > created_utc.isoformat()
    assert created_kie.isoformat().split("+")[-1] in ("02:00", "03:00")


@pytest.mark.parametrize(
    ["params", "error"],
    [
        pytest.param(
            {"path": 42}, "path: 42 is not of type 'string'", id="path-int"
        ),
        pytest.param(
            {"pattern": 42},
            "pattern: 42 is not of type 'string'",
            id="pattern-int",
        ),
        pytest.param(
            {"encoding": "UTF-42"},
            "encoding: 'UTF-42' is not a 'encoding'",
            id="encoding-wrong",
        ),
        pytest.param(
            {"timezone": "Europe/Kharkiv"},
            "timezone: 'Europe/Kharkiv' is not a 'timezone'",
            id="timezone-wrong",
        ),
    ],
)
def test_param_bad_value(testapp, params, error):
    """Source processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(source.process(testapp, [], **params))
    assert str(excinfo.value) == error
