"""Markdown processor test suite."""

import re
import textwrap
import unittest.mock

import pytest

from holocron import app, core
from holocron.processors import markdown


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
    return app.Holocron()


def test_item(testapp):
    """Markdown processor has to work."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        # some title

                        text with **bold**
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>text with <strong>bold</strong></p>"),
            "destination": "1.html",
            "title": "some title",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_alt_title_syntax(testapp):
    """Markdown processor has to work with alternative title syntax."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        some title
                        ==========

                        text with **bold**
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>text with <strong>bold</strong></p>"),
            "destination": "1.html",
            "title": "some title",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_newlines_at_the_beginning(testapp):
    """Markdown processor has to ignore newlines at the beginning."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\


                        # some title

                        text with **bold**
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>text with <strong>bold</strong></p>"),
            "destination": "1.html",
            "title": "some title",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_without_title(testapp):
    """Markdown processor has to work process items without title."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        text with **bold**
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>text with <strong>bold</strong></p>"),
            "destination": "1.html",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_title_is_not_overwritten(testapp):
    """Markdown processor hasn"t to set title if it"s already set."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        # some title

                        text with **bold**
                    """),
                    "destination": "1.md",
                    "title": "another title",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>text with <strong>bold</strong></p>"),
            "destination": "1.html",
            "title": "another title",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_title_ignored_in_the_middle_of_text(testapp):
    """Markdown processor has to ignore title if it"s in the middle of text."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        text

                        # some title

                        text with **bold**
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>text</p>\s*"
                r"<h1>some title</h1>\s*"
                r"<p>text with <strong>bold</strong></p>"),
            "destination": "1.html",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_sections(testapp):
    """Markdown processor has to work even for complex items."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
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
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>aaa</p>\s*"
                r"<h2>some section 1</h2>\s*<p>bbb</p>\s*"
                r"<h2>some section 2</h2>\s*<p>ccc</p>\s*"
                r"<h1>some title 2</h1>\s*<p>xxx</p>\s*"
                r"<h2>some section 3</h2>\s*<p>yyy</p>\s*"),
            "destination": "1.html",
            "title": "some title 1",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_code(testapp):
    """Markdown processor has to highlight code with codehilite extension."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        test codeblock

                            :::python
                            lambda x: pass
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>test codeblock</p>\s*.*codehilite.*<pre>[\s\S]+</pre>.*"),
            "destination": "1.html",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_fenced_code(testapp):
    """Markdown processor has to support GitHub"s fence code syntax."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        test codeblock

                        ```python
                        lambda x: pass
                        ```
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>test codeblock</p>\s*.*codehilite.*<pre>[\s\S]+</pre>.*"),
            "destination": "1.html",
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_table(testapp):
    """Markdown processor has to support table syntax (markup extension)."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        column a | column b
                        ---------|---------
                           foo   |   bar
                    """),
                    "destination": "1.md",
                }),
        ])

    item = next(stream)
    assert item == core.Item(
        {
            "content": unittest.mock.ANY,
            "destination": "1.html",
        })

    assert "table" in item["content"]
    assert "<th>column a</th>" in item["content"]
    assert "<th>column b</th>" in item["content"]
    assert "<td>foo</td>" in item["content"]
    assert "<td>bar</td>" in item["content"]

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_inline_code(testapp):
    """Markdown processor has to use <code> for inline code."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        test `code`
                    """),
                    "destination": "1.md",
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(r"<p>test <code>code</code></p>"),
            "destination": "1.html",
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Markdown processor has to work with stream."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": "the key is **%d**" % i,
                    "destination": "1.md",
                })
            for i in range(amount)
        ])

    for i in range(amount):
        assert next(stream) == core.Item(
            {
                "content": "<p>the key is <strong>%d</strong></p>" % i,
                "destination": "1.html",
            })

    with pytest.raises(StopIteration):
        next(stream)


def test_param_extensions(testapp):
    """Markdown processor has to respect extensions parameter."""

    stream = markdown.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        ```
                        lambda x: pass
                        ```
                    """),
                    "destination": "1.md",
                }),
        ],
        extensions=[])

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                # no syntax highlighting when no extensions are passed
                r"<p><code>lambda x: pass</code></p>"),
            "destination": "1.html",
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("params, error", [
    ({"extensions": 42}, "extensions: 42 should be instance of 'list'"),
])
def test_param_bad_value(testapp, params, error):
    """Markdown processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(markdown.process(testapp, [], **params))
