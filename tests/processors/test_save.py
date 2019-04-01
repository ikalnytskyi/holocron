"""Save processor test suite."""

import collections.abc
import os

import py
import pytest

from holocron import core
from holocron.processors import save


@pytest.fixture(scope="function")
def testapp(request):
    return core.Application()


def test_item(testapp, monkeypatch, tmpdir):
    """Save processor has to work!"""

    monkeypatch.chdir(tmpdir)

    stream = save.process(
        testapp, [core.Item({"content": "Obi-Wan", "destination": "1.html"})]
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "Obi-Wan", "destination": "1.html"})
    ]
    assert tmpdir.join("_site", "1.html").read_text("UTF-8") == "Obi-Wan"


@pytest.mark.parametrize(
    ["data", "loader"],
    [
        pytest.param("text", py.path.local.read, id="text"),
        pytest.param(b"\xf1", py.path.local.read_binary, id="binary"),
    ],
)
def test_item_content_types(testapp, monkeypatch, tmpdir, data, loader):
    """Save processor has to save content of bytes and string types."""

    monkeypatch.chdir(tmpdir)

    stream = save.process(
        testapp, [core.Item({"content": data, "destination": "1.dat"})]
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": data, "destination": "1.dat"})
    ]
    assert loader(tmpdir.join("_site", "1.dat")) == data


@pytest.mark.parametrize(
    ["destination"],
    [
        pytest.param(os.path.join("1.txt"), id="deep-0"),
        pytest.param(os.path.join("a", "2.txt"), id="deep-1"),
        pytest.param(os.path.join("a", "b", "3.txt"), id="deep-2"),
        pytest.param(os.path.join("a", "b", "c", "4.txt"), id="deep-3"),
    ],
)
def test_item_destination(testapp, monkeypatch, tmpdir, destination):
    """Save processor has to respect any destination value."""

    monkeypatch.chdir(tmpdir)

    stream = save.process(
        testapp,
        [core.Item({"content": "Obi-Wan", "destination": destination})],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "Obi-Wan", "destination": destination})
    ]
    assert tmpdir.join("_site", destination).read_text("UTF-8") == "Obi-Wan"


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
def test_item_many(testapp, monkeypatch, tmpdir, amount):
    """Save processor has to work with a stream of items."""

    monkeypatch.chdir(tmpdir)

    stream = save.process(
        testapp,
        [
            core.Item({"content": "Obi-Wan", "destination": str(i)})
            for i in range(amount)
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "Obi-Wan", "destination": str(i)})
        for i in range(amount)
    ]

    for i in range(amount):
        assert tmpdir.join("_site", str(i)).read_text("UTF-8") == "Obi-Wan"


@pytest.mark.parametrize(
    ["encoding"], [pytest.param("CP1251"), pytest.param("UTF-16")]
)
def test_param_encoding(testapp, monkeypatch, tmpdir, encoding):
    """Save processor has to respect 'encoding' parameter."""

    monkeypatch.chdir(tmpdir)

    stream = save.process(
        testapp,
        [core.Item({"content": "Обі-Ван", "destination": "1.html"})],
        encoding=encoding,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "Обі-Ван", "destination": "1.html"})
    ]
    assert tmpdir.join("_site", "1.html").read_text(encoding) == "Обі-Ван"


@pytest.mark.parametrize(
    ["encoding"], [pytest.param("CP1251"), pytest.param("UTF-16")]
)
def test_param_encoding_fallback(testapp, monkeypatch, tmpdir, encoding):
    """Save processor has to respect 'encoding' parameter (fallback)."""

    monkeypatch.chdir(tmpdir)
    testapp.metadata.update({"encoding": encoding})

    stream = save.process(
        testapp, [core.Item({"content": "Обі-Ван", "destination": "1.html"})]
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "Обі-Ван", "destination": "1.html"})
    ]
    assert tmpdir.join("_site", "1.html").read_text(encoding) == "Обі-Ван"


@pytest.mark.parametrize(
    ["to"], [pytest.param("_build"), pytest.param("_public")]
)
def test_param_to(testapp, monkeypatch, tmpdir, to):
    """Save processor has to respect 'to' parameter."""

    monkeypatch.chdir(tmpdir)

    stream = save.process(
        testapp,
        [core.Item({"content": "Obi-Wan", "destination": "1.html"})],
        to=to,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        core.Item({"content": "Obi-Wan", "destination": "1.html"})
    ]
    assert tmpdir.join(to, "1.html").read_text("UTF-8") == "Obi-Wan"


@pytest.mark.parametrize(
    ["params", "error"],
    [
        pytest.param(
            {"to": 42}, "to: 42 is not of type 'string'", id="to-int"
        ),
        pytest.param(
            {"to": [42]}, "to: [42] is not of type 'string'", id="to-list"
        ),
        pytest.param(
            {"to": {"x": 1}},
            "to: {'x': 1} is not of type 'string'",
            id="to-dict",
        ),
        pytest.param(
            {"encoding": "UTF-42"},
            "encoding: 'UTF-42' is not a 'encoding'",
            id="encoding-wrong",
        ),
        pytest.param(
            {"encoding": [42]},
            "encoding: [42] is not of type 'string'",
            id="encoding-list",
        ),
        pytest.param(
            {"encoding": {"y": 2}},
            "encoding: {'y': 2} is not of type 'string'",
            id="encoding-dict",
        ),
    ],
)
def test_param_bad_value(testapp, params, error):
    """Save processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(save.process(testapp, [], **params))
    assert str(excinfo.value) == error
