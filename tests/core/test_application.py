"""Core application test suite."""

import pytest

import holocron.core


def test_metadata():
    """.metadata property works like mapping."""

    testapp = holocron.core.Application()

    with pytest.raises(KeyError, match="'yoda'"):
        testapp.metadata["yoda"]
    assert testapp.metadata.get("yoda", "master") == "master"

    testapp.metadata["yoda"] = "master"
    assert testapp.metadata["yoda"] == "master"


def test_metadata_init():
    """.metadata property is initialized."""

    testapp = holocron.core.Application({"yoda": "master", "vader": "sith"})

    assert testapp.metadata["yoda"] == "master"
    assert testapp.metadata["vader"] == "sith"

    testapp.metadata["vader"] = "darth"
    assert testapp.metadata["vader"] == "darth"
    assert testapp.metadata["yoda"] == "master"


def test_add_processor(caplog):
    """.add_processor() registers a processor."""

    testapp = holocron.core.Application()
    marker = None

    def processor(app, items):
        nonlocal marker
        marker = 42
        yield from items

    testapp.add_processor("processor", processor)

    for _ in testapp.invoke([{"name": "processor"}]):
        pass

    assert marker == 42
    assert len(caplog.records) == 0


def test_add_processor_override(caplog):
    """.add_processor() overrides registered one."""

    testapp = holocron.core.Application()
    marker = None

    def processor_a(app, items):
        nonlocal marker
        marker = 42
        yield from items

    def processor_b(app, items):
        nonlocal marker
        marker = 13
        yield from items

    testapp.add_processor("processor", processor_a)
    testapp.add_processor("processor", processor_b)

    for _ in testapp.invoke([{"name": "processor"}]):
        pass

    assert marker == 13

    assert len(caplog.records) == 1
    assert caplog.records[0].message == "processor override: 'processor'"


def test_add_pipe(caplog):
    """.add_pipe() registers a pipe."""

    testapp = holocron.core.Application()
    marker = None

    def processor(app, items):
        nonlocal marker
        marker = 42
        yield from items

    testapp.add_processor("processor", processor)
    testapp.add_pipe("pipe", [{"name": "processor"}])

    for _ in testapp.invoke("pipe"):
        pass

    assert marker == 42
    assert len(caplog.records) == 0


def test_add_pipe_override(caplog):
    """.add_pipe() overrides registered one."""

    testapp = holocron.core.Application()
    marker = None

    def processor_a(app, items):
        nonlocal marker
        marker = 42
        yield from items

    def processor_b(app, items):
        nonlocal marker
        marker = 13
        yield from items

    testapp.add_processor("processor_a", processor_a)
    testapp.add_processor("processor_b", processor_b)

    testapp.add_pipe("pipe", [{"name": "processor_a"}])
    testapp.add_pipe("pipe", [{"name": "processor_b"}])

    for _ in testapp.invoke("pipe"):
        pass

    assert marker == 13

    assert len(caplog.records) == 1
    assert caplog.records[0].message == "pipe override: 'pipe'"


def test_invoke():
    """.invoke() just works!"""

    def processor_a(app, items):
        items = list(items)
        assert items == [holocron.core.Item({"a": "b"})]
        items[0]["x"] = 42
        yield from items

    def processor_b(app, items):
        items = list(items)
        assert items == [holocron.core.Item({"a": "b", "x": 42})]
        items.append(holocron.core.Item({"z": 13}))
        yield from items

    def processor_c(app, items):
        items = list(items)
        assert items == [
            holocron.core.Item({"a": "b", "x": 42}),
            holocron.core.Item({"z": 13}),
        ]
        yield from items

    testapp = holocron.core.Application()
    testapp.add_processor("processor_a", processor_a)
    testapp.add_processor("processor_b", processor_b)
    testapp.add_processor("processor_c", processor_c)
    testapp.add_pipe(
        "test",
        [
            {"name": "processor_a"},
            {"name": "processor_b"},
            {"name": "processor_c"},
        ],
    )

    stream = testapp.invoke("test", [holocron.core.Item({"a": "b"})])
    assert next(stream) == holocron.core.Item({"a": "b", "x": 42})
    assert next(stream) == holocron.core.Item({"z": 13})

    with pytest.raises(StopIteration):
        next(stream)


def test_invoke_anonymous_pipe():
    """.invoke() works with anonymous pipes."""

    def processor_a(app, items):
        items = list(items)
        assert items == [holocron.core.Item({"a": "b"})]
        items[0]["x"] = 42
        yield from items

    def processor_b(app, items):
        items = list(items)
        assert items == [holocron.core.Item({"a": "b", "x": 42})]
        items.append(holocron.core.Item({"z": 13}))
        yield from items

    def processor_c(app, items):
        items = list(items)
        assert items == [
            holocron.core.Item({"a": "b", "x": 42}),
            holocron.core.Item({"z": 13}),
        ]
        yield from items

    testapp = holocron.core.Application()
    testapp.add_processor("processor_a", processor_a)
    testapp.add_processor("processor_b", processor_b)
    testapp.add_processor("processor_c", processor_c)

    stream = testapp.invoke(
        [
            {"name": "processor_a"},
            {"name": "processor_b"},
            {"name": "processor_c"},
        ],
        [holocron.core.Item({"a": "b"})],
    )

    assert next(stream) == holocron.core.Item({"a": "b", "x": 42})
    assert next(stream) == holocron.core.Item({"z": 13})

    with pytest.raises(StopIteration):
        next(stream)


def test_invoke_pipe_not_found():
    """.invoke() raises proper exception."""

    testapp = holocron.core.Application()

    with pytest.raises(ValueError) as excinfo:
        next(testapp.invoke("test"))

    assert str(excinfo.value) == "no such pipe: 'test'"


def test_invoke_empty_pipe():
    """.invoke() returns nothing."""

    testapp = holocron.core.Application()
    testapp.add_pipe("test", [])

    with pytest.raises(StopIteration):
        next(testapp.invoke("test"))


def test_invoke_passthrough_items_empty_pipe():
    """.invoke() passes through items on empty pipe."""

    testapp = holocron.core.Application()
    testapp.add_pipe("test", [])

    stream = testapp.invoke(
        "test",
        [
            holocron.core.Item(name="yoda", rank="master"),
            holocron.core.Item(name="skywalker"),
        ],
    )

    assert next(stream) == holocron.core.Item(name="yoda", rank="master")
    assert next(stream) == holocron.core.Item(name="skywalker")

    with pytest.raises(StopIteration):
        next(testapp.invoke("test"))


def test_invoke_passthrough_items():
    """.invoke() passes through items on non empty pipe."""

    def processor(app, items):
        yield from items

    testapp = holocron.core.Application()
    testapp.add_processor("processor", processor)
    testapp.add_pipe("test", [{"name": "processor"}])

    stream = testapp.invoke(
        "test",
        [
            holocron.core.Item(name="yoda", rank="master"),
            holocron.core.Item(name="skywalker"),
        ],
    )

    assert next(stream) == holocron.core.Item(name="yoda", rank="master")
    assert next(stream) == holocron.core.Item(name="skywalker")

    with pytest.raises(StopIteration):
        next(testapp.invoke("test"))


@pytest.mark.parametrize(
    "processor_options",
    [
        {"a": 1},
        {"b": 1.13},
        {"a": 1, "b": 1.13},
        {"a": {"x": [1, 2]}, "b": ["1", 2]},
    ],
)
def test_invoke_propagates_processor_options(processor_options):
    """.invoke() propagates processor's options."""

    def processor(app, items, **options):
        assert options == processor_options
        yield from items

    testapp = holocron.core.Application()
    testapp.add_processor("processor", processor)
    testapp.add_pipe("test", [dict(processor_options, name="processor")])

    with pytest.raises(StopIteration):
        next(testapp.invoke("test"))


@pytest.mark.parametrize(
    "options, resolved",
    [
        ({"a": {"$ref": "metadata://#/is_yoda_master"}}, {"a": True}),
        ({"a": {"$ref": "metadata://#/extra/0/luke"}}, {"a": "skywalker"}),
        (
            {
                "a": {"$ref": "metadata://#/is_yoda_master"},
                "b": {"$ref": "metadata://#/extra/0/luke"},
            },
            {"a": True, "b": "skywalker"},
        ),
        (
            {"a": {"$ref": "item://#/content"}},
            {"a": {"$ref": "item://#/content"}},
        ),
    ],
)
def test_invoke_resolves_jsonref(options, resolved):
    """.invoke() resolves JSON references in processor's options."""

    testapp = holocron.core.Application(
        {"extra": [{"luke": "skywalker"}], "is_yoda_master": True}
    )

    def processor(app, items, **options):
        assert options == resolved
        yield from items

    testapp.add_processor("processor", processor)
    testapp.add_pipe("test", [dict(options, name="processor")])

    with pytest.raises(StopIteration):
        next(testapp.invoke("test"))


def test_invoke_processor_errors():
    """.invoke() raises proper exception."""

    def processor(app, documents):
        raise ValueError("something bad happened")
        yield

    testapp = holocron.core.Application()
    testapp.add_processor("processor", processor)
    testapp.add_pipe("test", [{"name": "processor"}])

    stream = testapp.invoke("test")

    with pytest.raises(ValueError, match=r"^something bad happened$"):
        next(stream)

    with pytest.raises(StopIteration):
        next(stream)


def test_invoke_processor_not_found():
    """.invoke() raises proper exception."""

    testapp = holocron.core.Application()
    testapp.add_pipe("test", [{"name": "processor"}])

    with pytest.raises(ValueError) as excinfo:
        next(testapp.invoke("test"))

    assert str(excinfo.value) == "no such processor: 'processor'"
