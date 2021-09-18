"""Markdown processor test suite."""

import collections.abc
import pathlib
import re
import textwrap
import unittest.mock

import pytest

import holocron
from holocron._processors import markdown


class _pytest_regex:
    """Assert that a given string meets some expectations."""

    def __init__(self, pattern, flags=0):
        self._regex = re.compile(pattern, flags)

    def __eq__(self, actual):
        return bool(self._regex.match(actual))

    def __repr__(self):
        return self._regex.pattern


@pytest.fixture(scope="function")
def testapp():
    return holocron.Application()


def test_item(testapp):
    """Markdown processor has to work."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        # some title

                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(r"<p>text with <strong>bold</strong></p>"),
                "destination": pathlib.Path("1.html"),
                "title": "some title",
            }
        )
    ]


def test_item_with_alt_title_syntax(testapp):
    """Markdown processor has to work with alternative title syntax."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        some title
                        ==========

                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(r"<p>text with <strong>bold</strong></p>"),
                "destination": pathlib.Path("1.html"),
                "title": "some title",
            }
        )
    ]


def test_item_with_newlines_at_the_beginning(testapp):
    """Markdown processor has to ignore newlines at the beginning."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\


                        # some title

                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(r"<p>text with <strong>bold</strong></p>"),
                "destination": pathlib.Path("1.html"),
                "title": "some title",
            }
        )
    ]


def test_item_without_title(testapp):
    """Markdown processor has to work process items without title."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(r"<p>text with <strong>bold</strong></p>"),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_title_is_not_overwritten(testapp):
    """Markdown processor hasn"t to set title if it"s already set."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        # some title

                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                    "title": "another title",
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(r"<p>text with <strong>bold</strong></p>"),
                "destination": pathlib.Path("1.html"),
                "title": "another title",
            }
        )
    ]


def test_item_title_ignored_in_the_middle_of_text(testapp):
    """Markdown processor has to ignore title if it"s in the middle of text."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        text

                        # some title

                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>text</p>\s*"
                    r"<h1>some title</h1>\s*"
                    r"<p>text with <strong>bold</strong></p>"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_with_sections(testapp):
    """Markdown processor has to work even for complex items."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        some title 1
                        ============

                        aaa

                        some section 1
                        --------------

                        bbb

                        some section 2
                        --------------

                        ccc

                        # some title 2

                        xxx

                        ## some section 3

                        yyy
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>aaa</p>\s*"
                    r"<h2>some section 1</h2>\s*<p>bbb</p>\s*"
                    r"<h2>some section 2</h2>\s*<p>ccc</p>\s*"
                    r"<h1>some title 2</h1>\s*<p>xxx</p>\s*"
                    r"<h2>some section 3</h2>\s*<p>yyy</p>\s*"
                ),
                "destination": pathlib.Path("1.html"),
                "title": "some title 1",
            }
        )
    ]


def test_item_with_code(testapp):
    """Markdown processor has to highlight code with codehilite extension."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        test codeblock

                            :::python
                            lambda x: pass
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>test codeblock</p>\s*.*highlight.*<pre>[\s\S]+</pre>.*"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_with_fenced_code(testapp):
    """Markdown processor has to support GitHub"s fence code syntax."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        test codeblock

                        ```python
                        lambda x: pass
                        ```
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>test codeblock</p>\s*.*highlight.*<pre>[\s\S]+</pre>.*"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_with_table(testapp):
    """Markdown processor has to support table syntax (markup extension)."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        column a | column b
                        ---------|---------
                           foo   |   bar
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)

    stream = list(stream)
    assert stream == [
        holocron.Item(
            {
                "content": unittest.mock.ANY,
                "destination": pathlib.Path("1.html"),
            }
        )
    ]

    item = stream[0]
    assert "table" in item["content"]
    assert "<th>column a</th>" in item["content"]
    assert "<th>column b</th>" in item["content"]
    assert "<td>foo</td>" in item["content"]
    assert "<td>bar</td>" in item["content"]


def test_item_with_inline_code(testapp):
    """Markdown processor has to use <code> for inline code."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        test `code`
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(r"<p>test <code>code</code></p>"),
                "destination": pathlib.Path("1.html"),
            }
        )
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
    """Markdown processor has to work with stream."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the key is **%d**" % i,
                    "destination": pathlib.Path("1.md"),
                }
            )
            for i in range(amount)
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<p>the key is <strong>%d</strong></p>" % i,
                "destination": pathlib.Path("1.html"),
            }
        )
        for i in range(amount)
    ]


@pytest.mark.parametrize(
    ["extensions", "rendered"],
    [
        pytest.param(
            {},
            r"<p>test codeblock</p>\s*"
            r"<pre><code>:::\s*lambda x: pass\s*</code></pre>",
            id="no",
        ),
        pytest.param(
            {"markdown.extensions.codehilite": {"css_class": "vader"}},
            r"<p>test codeblock</p>\s*.*vader.*<pre>[\s\S]+</pre>.*",
            id="codehilite",
        ),
    ],
)
def test_args_extensions(testapp, extensions, rendered):
    """Markdown processor has to respect extensions argument."""

    stream = markdown.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        test codeblock

                            :::
                            lambda x: pass
                    """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
        extensions=extensions,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(rendered),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


@pytest.mark.parametrize(
    ["args", "error"],
    [
        pytest.param(
            {"extensions": 42},
            "extensions: 42 is not of type 'object'",
            id="extensions-int",
        ),
        pytest.param(
            {"extensions": {"a": 42}},
            r"extensions: 'a' does not match '^markdown\\.extensions\\..*'",
            id="extensions-dict",
        ),
    ],
)
def test_args_bad_value(testapp, args, error):
    """Markdown processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(markdown.process(testapp, [], **args))
    assert str(excinfo.value) == error
