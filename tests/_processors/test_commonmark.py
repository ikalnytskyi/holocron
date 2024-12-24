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


@pytest.fixture
def testapp():
    return holocron.Application({"url": "https://yoda.ua"})


def test_item(testapp):
    """Commonmark processor has to convert a markuped content."""

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
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<h1>some title</h1>\n<p>text with <strong>bold</strong></p>\n",
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


@pytest.mark.parametrize(
    "content",
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
def test_item_infer_title(testapp, content):
    """Commonmark processor has to cut a title of the content."""

    stream = commonmark.process(
        testapp,
        [holocron.Item({"content": content, "destination": pathlib.Path("1.md")})],
        infer_title=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<p>text with <strong>bold</strong></p>\n",
                "destination": pathlib.Path("1.html"),
                "title": "some title",
            }
        )
    ]


def test_item_infer_title_ignored(testapp):
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
        infer_title=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<h1>some title</h1>\n<p>text with <strong>bold</strong></p>\n",
                "destination": pathlib.Path("1.html"),
                "title": "another title",
            }
        )
    ]


def test_item_infer_title_in_the_middle_of_content(testapp):
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
        infer_title=True,
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


def test_item_infer_title_with_sections(testapp):
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
        infer_title=True,
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
                "content": "<p>the key is <strong>%d</strong></p>\n" % i,
                "destination": pathlib.Path("1.html"),
            }
        )
        for i in range(amount)
    ]


@pytest.mark.parametrize(
    ("rendered", "pygmentize"),
    [
        pytest.param(
            (
                "<p>test codeblock</p>\n"
                '<pre><code class="language-python">'
                "lambda x: pass\n"
                "</code></pre>\n"
            ),
            False,
            id="pygmentize=off",
        ),
        pytest.param(
            (
                "<p>test codeblock</p>\n"
                '<pre><code class="language-python">'
                '<span class="k">lambda</span> '
                '<span class="n">x</span>'
                '<span class="p">:</span> '
                '<span class="k">pass</span>\n'
                "</code></pre>\n"
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
                "content": rendered,
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


@pytest.mark.parametrize("language", [pytest.param("yoda"), pytest.param("vader")])
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
                    f"lambda x: pass\n</code></pre>\n"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_exec(testapp):
    """Commonmark has to pipe code content through an executable if asked to."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """
                        ```text {"exec": ["sed", "s/ a / the /g"]}
                        yoda, a jedi grandmaster
                        ```
                        """
                    ),
                    "source": pathlib.Path("1.md"),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "yoda, the jedi grandmaster\n",
                "source": pathlib.Path("1.md"),
                "destination": pathlib.Path("1.html"),
            },
        ),
    ]


def test_args_strikethrough(testapp):
    """Commonmark has to support strikethrough extension."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "text with ~~strikethrough~~",
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
        strikethrough=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<p>text with <s>strikethrough</s></p>\n",
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_args_table(testapp):
    """Commonmark has to support table extension."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        | name | value |
                        | ---- | ----- |
                        | foo  | bar   |
                        """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
        table=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": (
                    "<table>\n"
                    "<thead>\n<tr>\n<th>name</th>\n<th>value</th>\n</tr>\n</thead>\n"
                    "<tbody>\n<tr>\n<td>foo</td>\n<td>bar</td>\n</tr>\n</tbody>\n"
                    "</table>\n"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_args_footnote(testapp):
    """Commonmark has to support footnote extension."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        text with footnote [^1]

                        [^1]: definition
                        """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
        footnote=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": (
                    "<p>text with footnote "
                    '<sup class="footnote-ref">'
                    '<a href="#fn1" id="fnref1">[1]</a></sup></p>\n'
                    '<hr class="footnotes-sep" />\n'
                    '<section class="footnotes">\n'
                    '<ol class="footnotes-list">\n'
                    '<li id="fn1" class="footnote-item">'
                    "<p>definition "
                    '<a href="#fnref1" class="footnote-backref">↩︎</a>'
                    "</p>\n"
                    "</li>\n"
                    "</ol>\n"
                    "</section>\n"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


@pytest.mark.parametrize("kind", ["warning", "note"])
def test_args_admonition(testapp, kind):
    """Commonmark has to support admonition extension."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        f"""\
                        :::{kind}
                        some text
                        :::
                        """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
        admonition=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": f'<div class="{kind}">\n<p>some text</p>\n</div>\n',
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_args_definition(testapp):
    """Commonmark has to support definition list extension."""

    stream = commonmark.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        term
                        : definition
                        """
                    ),
                    "destination": pathlib.Path("1.md"),
                }
            )
        ],
        definition=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "<dl>\n<dt>term</dt>\n<dd>definition</dd>\n</dl>\n",
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


@pytest.mark.parametrize(
    ("args", "error"),
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
