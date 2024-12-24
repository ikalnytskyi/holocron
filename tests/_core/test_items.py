"""Core items test suite."""

import pathlib

import pytest

import holocron


@pytest.fixture(
    params=[
        pytest.param(42, id="int-value"),
        pytest.param("key", id="str-value"),
        pytest.param(42.42, id="float-value"),
        pytest.param(True, id="bool-value"),
        pytest.param(None, id="none-value"),
        pytest.param({"a": 1, "b": 2}, id="dict-value"),
        pytest.param({"a", "b", "c"}, id="set-value"),
        pytest.param([1, 2, "c"], id="list-value"),
        pytest.param((1, None, True), id="tuple-value"),
        pytest.param(object(), id="object-value"),
        pytest.param(lambda: 42, id="lambda-value"),
    ],
)
def supported_value(request):
    return request.param


@pytest.fixture
def item_descriptors_cls():
    class methoddescriptor:
        def __init__(self, wrapped):
            pass

        def __get__(self, instance, owner=None):
            return 42

    class Item(holocron.Item):
        @property
        def x(self):
            return 13

        @methoddescriptor
        def y(self):
            return None

    return Item


def test_item_init_mapping(supported_value):
    """Properties can be initialized."""

    instance = holocron.Item({"x": supported_value, "y": 42})

    assert instance["x"] == supported_value
    assert instance["y"] == 42

    assert instance == holocron.Item({"x": supported_value, "y": 42})


def test_item_init_kwargs(supported_value):
    """Properties can be initialized."""

    instance = holocron.Item(x=supported_value, y=42)

    assert instance["x"] == supported_value
    assert instance["y"] == 42

    assert instance == holocron.Item(x=supported_value, y=42)


def test_item_init_mapping_kwargs():
    """Properties can be initialized."""

    instance = holocron.Item({"x": "skywalker"}, y=42)

    assert instance["x"] == "skywalker"
    assert instance["y"] == 42

    assert instance == holocron.Item({"x": "skywalker", "y": 42})


def test_item_multiple_mappings():
    """Passing 2+ mappings is prohibited."""

    with pytest.raises(TypeError) as excinfo:
        holocron.Item({"a": 1}, {"b": 2})

    assert str(excinfo.value) == "expected at most 1 argument, got 2"


def test_item_setitem(supported_value):
    """Properties can be set."""

    instance = holocron.Item()
    instance["x"] = supported_value
    instance["y"] = 42

    assert instance["x"] == supported_value
    assert instance["y"] == 42

    assert instance == holocron.Item(x=supported_value, y=42)


def test_item_init_setitem(supported_value):
    """Properties can be initialized and set."""

    instance = holocron.Item(x=supported_value)
    instance["y"] = 42

    assert instance["x"] == supported_value
    assert instance["y"] == 42

    assert instance == holocron.Item(x=supported_value, y=42)


def test_item_getitem(supported_value):
    """Properties can be retrieved."""

    instance = holocron.Item(x=supported_value)

    assert instance["x"] == supported_value


def test_item_getitem_descriptor(item_descriptors_cls):
    """Properties can be retrieved."""

    instance = item_descriptors_cls(z="vader")

    assert instance["x"] == 13
    assert instance["y"] == 42
    assert instance["z"] == "vader"


def test_item_getitem_keyerror():
    """KeyError is raised if key is not found."""

    instance = holocron.Item()

    with pytest.raises(KeyError, match="'the-key'"):
        instance["the-key"]


def test_item_getitem_descriptor_dunder():
    """Built-in dunder properties must be ignored."""

    instance = holocron.Item()

    with pytest.raises(KeyError, match="'__weakref__'"):
        instance["__weakref__"]


def test_item_items():
    """.items() iterates over properties."""

    instance = holocron.Item(x=13, y=42)

    assert set(instance.items()) == {("x", 13), ("y", 42)}


def test_item_items_descriptors(item_descriptors_cls):
    """.items() iterates over properties."""

    instance = item_descriptors_cls(z="vader")

    assert set(instance.items()) == {("x", 13), ("y", 42), ("z", "vader")}


def test_item_keys():
    """.keys() iterates over properties."""

    instance = holocron.Item(x=13, y=42)

    assert set(instance.keys()) == {"x", "y"}


def test_item_keys_descriptors(item_descriptors_cls):
    """.keys() iterates over properties."""

    instance = item_descriptors_cls(z="vader")

    assert set(instance.keys()) == {"x", "y", "z"}


def test_item_values():
    """.values() iterates over properties."""

    instance = holocron.Item(x="vader", y=42)

    assert set(instance.values()) == {"vader", 42}


def test_item_values_descriptors(item_descriptors_cls):
    """.values() iterates over properties."""

    instance = item_descriptors_cls(z="vader")

    assert set(instance.values()) == {13, 42, "vader"}


def test_item_as_mapping(supported_value):
    """Properties can be inspected."""

    instance = holocron.Item(x=42, y="test", z=supported_value)

    assert instance.as_mapping() == {
        "x": 42,
        "y": "test",
        "z": supported_value,
    }


def test_item_as_mapping_descriptors(item_descriptors_cls):
    """Properties defined as descriptors can be inspected."""

    assert item_descriptors_cls(z=0).as_mapping() == {"x": 13, "y": 42, "z": 0}


def test_item_contains():
    """Properties can be tested for membership."""

    instance = holocron.Item(x=42, y="test")

    assert "x" in instance
    assert "y" in instance
    assert "z" not in instance


def test_item_contains_descriptors(item_descriptors_cls):
    """Properties can be tested for membership."""

    instance = item_descriptors_cls(z="vader")

    assert "x" in instance
    assert "y" in instance
    assert "z" in instance
    assert "w" not in instance


def test_websiteitem_init_mapping(supported_value):
    """Properties can be initialized."""

    instance = holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    assert instance["x"] == supported_value
    assert instance["destination"] == pathlib.Path("path", "to", "item")
    assert instance["baseurl"] == "https://yoda.ua"
    assert instance["url"] == "/path/to/item"
    assert instance["absurl"] == "https://yoda.ua/path/to/item"

    assert instance == holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )


def test_websiteitem_init_kwargs(supported_value):
    """Properties can be initialized."""

    instance = holocron.WebSiteItem(
        x=supported_value,
        destination=pathlib.Path("path", "to", "item"),
        baseurl="https://yoda.ua",
    )

    assert instance["x"] == supported_value
    assert instance["destination"] == pathlib.Path("path", "to", "item")
    assert instance["baseurl"] == "https://yoda.ua"
    assert instance["url"] == "/path/to/item"
    assert instance["absurl"] == "https://yoda.ua/path/to/item"

    assert instance == holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )


def test_websiteitem_init_mapping_kwargs(supported_value):
    """Properties can be initialized."""

    instance = holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
        },
        baseurl="https://yoda.ua",
    )

    assert instance["x"] == supported_value
    assert instance["destination"] == pathlib.Path("path", "to", "item")
    assert instance["baseurl"] == "https://yoda.ua"
    assert instance["url"] == "/path/to/item"
    assert instance["absurl"] == "https://yoda.ua/path/to/item"

    assert instance == holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )


def test_websiteitem_init_multiple_mappings(supported_value):
    """Passing 2+ mappings is prohibited."""

    with pytest.raises(TypeError) as excinfo:
        holocron.WebSiteItem(
            {"destination": pathlib.Path("path", "to", "item")},
            {"baseurl": "https://yoda.ua"},
        )

    assert str(excinfo.value) == "expected at most 1 argument, got 2"


@pytest.mark.parametrize(
    ("properties", "error"),
    [
        pytest.param(
            {},
            "WebSiteItem is missing some required properties: " "'baseurl', 'destination'",
            id="baseurl",
        ),
        pytest.param(
            {"destination": "test"},
            "WebSiteItem is missing some required properties: 'baseurl'",
            id="baseurl",
        ),
        pytest.param(
            {"baseurl": "test"},
            "WebSiteItem is missing some required properties: 'destination'",
            id="destination",
        ),
    ],
)
def test_websiteitem_init_required_properties(properties, error):
    """Both 'destination' and 'baseurl' are required properties."""

    with pytest.raises(TypeError) as excinfo:
        holocron.WebSiteItem(**properties)
    assert str(excinfo.value) == error


def test_websiteitem_setitem(supported_value):
    """Properties can be set."""

    instance = holocron.WebSiteItem(
        {
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )
    instance["x"] = supported_value

    assert instance["x"] == supported_value
    assert instance["destination"] == pathlib.Path("path", "to", "item")
    assert instance["baseurl"] == "https://yoda.ua"
    assert instance["url"] == "/path/to/item"
    assert instance["absurl"] == "https://yoda.ua/path/to/item"

    assert instance == holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )


def test_websiteitem_init_setitem(supported_value):
    """Properties can be initialized and set."""

    instance = holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )
    instance["y"] = 42

    assert instance["x"] == supported_value
    assert instance["y"] == 42
    assert instance["destination"] == pathlib.Path("path", "to", "item")
    assert instance["baseurl"] == "https://yoda.ua"
    assert instance["url"] == "/path/to/item"
    assert instance["absurl"] == "https://yoda.ua/path/to/item"

    assert instance == holocron.WebSiteItem(
        {
            "x": supported_value,
            "y": 42,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )


def test_websiteitem_getitem():
    """Properties can be retrieved."""

    instance = holocron.WebSiteItem(
        {
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    assert instance["destination"] == pathlib.Path("path", "to", "item")
    assert instance["baseurl"] == "https://yoda.ua"
    assert instance["url"] == "/path/to/item"
    assert instance["absurl"] == "https://yoda.ua/path/to/item"


def test_websiteitem_getitem_keyerror():
    """KeyError is raised if key is not found."""

    instance = holocron.WebSiteItem(
        {
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    with pytest.raises(KeyError, match="'the-key'"):
        instance["the-key"]


def test_websiteitem_items():
    """.items() iterates over properties."""

    instance = holocron.WebSiteItem(
        {
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    assert set(instance.items()) == {
        ("destination", pathlib.Path("path", "to", "item")),
        ("baseurl", "https://yoda.ua"),
        ("url", "/path/to/item"),
        ("absurl", "https://yoda.ua/path/to/item"),
    }


def test_websiteitem_keys():
    """.keys() iterates over properties."""

    instance = holocron.WebSiteItem(
        {
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    assert set(instance.keys()) == {"destination", "baseurl", "url", "absurl"}


def test_websiteitem_values():
    """.values() iterates over properties."""

    instance = holocron.WebSiteItem(
        {
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    assert set(instance.values()) == {
        pathlib.Path("path", "to", "item"),
        "https://yoda.ua",
        "/path/to/item",
        "https://yoda.ua/path/to/item",
    }


def test_websiteitem_as_mapping(supported_value):
    """Properties can be inspected."""

    instance = holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    assert instance.as_mapping() == {
        "x": supported_value,
        "destination": pathlib.Path("path", "to", "item"),
        "baseurl": "https://yoda.ua",
        "url": "/path/to/item",
        "absurl": "https://yoda.ua/path/to/item",
    }


def test_websiteitem_contains():
    """Properties can be tested for membership."""

    instance = holocron.WebSiteItem(
        {
            "x": supported_value,
            "destination": pathlib.Path("path", "to", "item"),
            "baseurl": "https://yoda.ua",
        }
    )

    assert "x" in instance
    assert "destination" in instance
    assert "baseurl" in instance
    assert "url" in instance
    assert "absurl" in instance
    assert "z" not in instance


@pytest.mark.parametrize(
    ("destination", "url"),
    [
        pytest.param(pathlib.Path("path-to-item"), "/path-to-item", id="flat"),
        pytest.param(pathlib.Path("path", "to", "item"), "/path/to/item", id="nested"),
        pytest.param(pathlib.Path("path to item"), "/path%20to%20item", id="quoted"),
        pytest.param(pathlib.Path("index.html"), "/", id="pretty-root-url"),
        pytest.param(pathlib.Path("jedi", "index.html"), "/jedi/", id="pretty-url"),
    ],
)
def test_websiteitem_url(destination, url):
    """'url' property is based on 'destination'."""

    instance = holocron.WebSiteItem({"destination": destination, "baseurl": "https://yoda.ua"})

    assert instance["url"] == url


@pytest.mark.parametrize(
    ("properties", "absurl"),
    [
        pytest.param(
            {
                "destination": pathlib.Path("path-to-item"),
                "baseurl": "https://yoda.ua",
            },
            "https://yoda.ua/path-to-item",
            id="flat",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("path", "to", "item"),
                "baseurl": "https://yoda.ua",
            },
            "https://yoda.ua/path/to/item",
            id="nested",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("path to item"),
                "baseurl": "https://yoda.ua",
            },
            "https://yoda.ua/path%20to%20item",
            id="quoted",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("path", "to", "item"),
                "baseurl": "https://skywalker.org",
            },
            "https://skywalker.org/path/to/item",
            id="baseurl",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("path", "to", "item"),
                "baseurl": "https://skywalker.org/",
            },
            "https://skywalker.org/path/to/item",
            id="trailing-/",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("path", "to", "item"),
                "baseurl": "https://skywalker.org/blog",
            },
            "https://skywalker.org/blog/path/to/item",
            id="subdir",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("path", "to", "item"),
                "baseurl": "https://skywalker.org/blog/",
            },
            "https://skywalker.org/blog/path/to/item",
            id="subdir-trailing-/",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("index.html"),
                "baseurl": "https://skywalker.org",
            },
            "https://skywalker.org/",
            id="pretty-root-url",
        ),
        pytest.param(
            {
                "destination": pathlib.Path("jedi", "index.html"),
                "baseurl": "https://skywalker.org",
            },
            "https://skywalker.org/jedi/",
            id="pretty-url",
        ),
    ],
)
def test_websiteitem_absurl(properties, absurl):
    """'absurl' property is based on 'destination' and 'baseurl'."""

    instance = holocron.WebSiteItem(properties)

    assert instance["absurl"] == absurl
