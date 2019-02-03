"""Commonmark processor test suite."""

import re
import textwrap

import pytest

from holocron import core
from holocron.processors import commonmark


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
    return core.Application()


def test_item(testapp):
    """Commonmark processor has to convert a markuped content."""

    stream = commonmark.process(
        testapp,
        [core.Item({"content": "text with **bold**", "destination": "1.md"})],
    )

    assert next(stream) == core.Item(
        {
            "content": "<p>text with <strong>bold</strong></p>",
            "destination": "1.html",
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


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
        testapp, [core.Item({"content": content, "destination": "1.md"})]
    )

    assert next(stream) == core.Item(
        {
            "content": "<p>text with <strong>bold</strong></p>",
            "destination": "1.html",
            "title": "some title",
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


def test_item_parsed_title_ignored(testapp):
    """Commonmark processor has to ignore a title if it's already set."""

    stream = commonmark.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        # some title

                        text with **bold**
                    """
                    ),
                    "destination": "1.md",
                    "title": "another title",
                }
            )
        ],
    )

    assert next(stream) == core.Item(
        {
            "content": "<p>text with <strong>bold</strong></p>",
            "destination": "1.html",
            "title": "another title",
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


def test_item_parsed_title_in_the_middle_of_content(testapp):
    """Commonmark processor has to ignore a title in the middle of content."""

    stream = commonmark.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        text

                        # some title

                        text with **bold**
                    """
                    ),
                    "destination": "1.md",
                }
            )
        ],
    )

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>text</p>\s*"
                r"<h1>some title</h1>\s*"
                r"<p>text with <strong>bold</strong></p>"
            ),
            "destination": "1.html",
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_sections(testapp):
    """Commonmark processor has to work for multi section content."""

    stream = commonmark.process(
        testapp,
        [
            core.Item(
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
                    "destination": "1.md",
                }
            )
        ],
    )

    assert next(stream) == core.Item(
        {
            "content": _pytest_regex(
                r"<p>aaa</p>\s*"
                r"<h2>some section 1</h2>\s*<p>bbb</p>\s*"
                r"<h2>some section 2</h2>\s*<p>ccc</p>\s*"
                r"<h1>some title 2</h1>\s*<p>xxx</p>\s*"
                r"<h2>some section 3</h2>\s*<p>yyy</p>\s*"
            ),
            "destination": "1.html",
            "title": "some title 1",
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Commonmark processor has to work with stream."""

    stream = commonmark.process(
        testapp,
        [
            core.Item(
                {"content": "the key is **%d**" % i, "destination": "1.md"}
            )
            for i in range(amount)
        ],
    )

    for i in range(amount):
        assert next(stream) == core.Item(
            {
                "content": "<p>the key is <strong>%d</strong></p>" % i,
                "destination": "1.html",
            }
        )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    ["rendered", "pygmentize"],
    [
        pytest.param(
            r"<p>test codeblock</p>\s*<pre><code class=\"language-python\">"
            r"lambda x: pass\s*</code></pre>",
            False,
            id="pygmentize=off",
        ),
        pytest.param(
            r"<p>test codeblock</p>\s*.*highlight.*<pre>[\s\S]+</pre>.*",
            True,
            id="pygmentize=on",
        ),
    ],
)
def test_param_pygmentize(testapp, rendered, pygmentize):
    """Commonmark processor has to pygmentize code with language."""

    stream = commonmark.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent(
                        """
                        test codeblock

                        ```python
                        lambda x: pass
                        ```
                    """
                    ),
                    "destination": "1.md",
                }
            )
        ],
        pygmentize=pygmentize,
    )

    assert next(stream) == core.Item(
        {"content": _pytest_regex(rendered), "destination": "1.html"}
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    ["language"], [pytest.param("yoda"), pytest.param("vader")]
)
def test_param_pygmentize_unknown_language(testapp, language):
    """Commonmark has to assume text/plain for unknown languages."""

    stream = commonmark.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent(
                        """
                        test codeblock

                        ```%s
                        lambda x: pass
                        ```
                    """
                    )
                    % language,
                    "destination": "1.md",
                }
            )
        ],
        pygmentize=True,
    )

    assert next(stream) == core.Item(
        {
            "content": (
                '<p>test codeblock</p>\n<pre><code class="language-%s">'
                "lambda x: pass\n</code></pre>"
            )
            % language,
            "destination": "1.html",
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    ["params", "error"],
    [
        pytest.param(
            {"pygmentize": 42},
            "pygmentize: 42 should be instance of 'bool'",
            id="pygmentize",
        )
    ],
)
def test_param_bad_value(testapp, params, error):
    """Commonmark processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(commonmark.process(testapp, [], **params))
