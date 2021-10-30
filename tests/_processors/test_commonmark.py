"""Commonmark processor test suite."""

import collections.abc
import pathlib
import re
import textwrap

import pytest

import holocron
from holocron._processors import commonmark


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
    """Commonmark processor has to convert a markuped content."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "text with **bold**",
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<p>text with <strong>bold</strong></p>",
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


@pytest.mark.parametrize(
    ["content"],
    [
        pytest.param(
            textwrap.dedent(
                """\
            # some title

            text with **bold**
        """
            ),
            id="heading",
        ),
        pytest.param(
            textwrap.dedent(
                """\


            # some title

            text with **bold**
        """
            ),
            id="heading-leading-nl",
        ),
        pytest.param(
            textwrap.dedent(
                """\
            some title
            ==========

            text with **bold**
        """
            ),
            id="setext-heading",
        ),
        pytest.param(
            textwrap.dedent(
                """\


            some title
            ==========

            text with **bold**
        """
            ),
            id="setext-heading-leading-nl",
        ),
    ],
)
def test_item_parsed_title(testapp, content):
    """Commonmark processor has to cut a title of the content."""

    stream = commonmark.process(
        testapp,
        [holocron.Item({"content": content, "destination": pathlib.Path("1.md")})],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<p>text with <strong>bold</strong></p>",
                "destination": pathlib.Path("1.html"),
                "title": "some title",
            }
        )
    ]


def test_item_parsed_title_ignored(testapp):
    """Commonmark processor has to ignore a title if it's already set."""

    stream = commonmark.process(
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
                "content": "<p>text with <strong>bold</strong></p>",
                "destination": pathlib.Path("1.html"),
                "title": "another title",
            }
        )
    ]


def test_item_parsed_title_in_the_middle_of_content(testapp):
    """Commonmark processor has to ignore a title in the middle of content."""

    stream = commonmark.process(
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
    """Commonmark processor has to work for multi section content."""

    stream = commonmark.process(
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
    """Commonmark processor has to work with stream."""

    stream = commonmark.process(
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
    ["rendered", "pygmentize"],
    [
        pytest.param(
            (
                r"<p>test codeblock</p>\s*"
                r"<pre><code class=\"language-python\">"
                r"lambda x: pass\s*</code></pre>"
            ),
            False,
            id="pygmentize=off",
        ),
        pytest.param(
            (
                r"<p>test codeblock</p>\s*"
                r".*highlight.*"
                r"<pre>\s*<span>\s*</span>\s*"
                r"<code>[\s\S]+</code>\s*"
                r"</pre>.*"
            ),
            True,
            id="pygmentize=on",
        ),
    ],
)
def test_args_pygmentize(testapp, rendered, pygmentize):
    """Commonmark processor has to pygmentize code with language."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """
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
        pygmentize=pygmentize,
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


@pytest.mark.parametrize(["language"], [pytest.param("yoda"), pytest.param("vader")])
def test_args_pygmentize_unknown_language(testapp, language):
    """Commonmark has to assume text/plain for unknown languages."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        f"""
                        test codeblock

                        ```{language}
                        lambda x: pass
                        ```
                        """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
        pygmentize=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": (
                    f"<p>test codeblock</p>\n"
                    f'<pre><code class="language-{language}">'
                    f"lambda x: pass\n</code></pre>"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


@pytest.mark.parametrize(
    ["args", "error"],
    [
        pytest.param(
            {"pygmentize": 42},
            "pygmentize: 42 is not of type 'boolean'",
            id="pygmentize",
        )
    ],
)
def test_args_bad_value(testapp, args, error):
    """Commonmark processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(commonmark.process(testapp, [], **args))
    assert str(excinfo.value) == error
