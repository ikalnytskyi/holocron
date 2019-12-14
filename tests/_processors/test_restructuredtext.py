"""ReStructuredText processors test suite."""

import collections.abc
import re
import textwrap
import pathlib

import pytest

import holocron
from holocron._processors import restructuredtext


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
    """reStructuredText processor has to work in simple case."""

    stream = restructuredtext.process(
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
                    "destination": pathlib.Path("1.rst"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>text with <strong>bold</strong></p>\s*"
                ),
                "destination": pathlib.Path("1.html"),
                "title": "some title",
            }
        )
    ]


def test_item_with_subsection(testapp):
    """reStructuredText processor has to start subsections with <h2>."""

    stream = restructuredtext.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        some title
                        ==========

                        abstract

                        some section
                        ------------

                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.rst"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>abstract</p>\s*"
                    r"<h2>some section</h2>\s*"
                    r"<p>text with <strong>bold</strong></p>\s*"
                ),
                "destination": pathlib.Path("1.html"),
                "title": "some title",
            }
        )
    ]


def test_item_without_title(testapp):
    """reStructuredText processor has to work even without a title."""

    stream = restructuredtext.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        text with **bold**
                    """
                    ),
                    "destination": pathlib.Path("1.rst"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>text with <strong>bold</strong></p>\s*"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_with_sections(testapp):
    """reStructuredText processor has to work with a lot of sections."""

    stream = restructuredtext.process(
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

                        some title 2
                        ============

                        xxx

                        some section 3
                        --------------

                        yyy
                    """
                    ),
                    "destination": pathlib.Path("1.rst"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<h2>some title 1</h2>\s*"
                    r"<p>aaa</p>\s*"
                    r"<h3>some section 1</h3>\s*"
                    r"<p>bbb</p>\s*"
                    r"<h3>some section 2</h3>\s*"
                    r"<p>ccc</p>\s*"
                    r"<h2>some title 2</h2>\s*"
                    r"<p>xxx</p>\s*"
                    r"<h3>some section 3</h3>\s*"
                    r"<p>yyy</p>\s*"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_with_code(testapp):
    """reStructuredText processor has to highlight code with Pygments."""

    stream = restructuredtext.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        test codeblock

                        .. code:: python

                            lambda x: pass
                    """
                    ),
                    "destination": pathlib.Path("1.rst"),
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    r"<p>test codeblock</p>\s*<pre.*python[^>]*>[\s\S]+</pre>"
                ),
                "destination": pathlib.Path("1.html"),
            }
        )
    ]


def test_item_with_inline_code(testapp):
    """reStructuredText processor has to use <code> tag for inline code."""

    stream = restructuredtext.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        test ``code``
                    """
                    ),
                    "destination": pathlib.Path("1.rst"),
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


def test_args_settings(testapp):
    """reStructuredText processor has to respect custom settings."""

    stream = restructuredtext.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        section 1
                        =========

                        aaa

                        section 2
                        =========

                        bbb
                    """
                    ),
                    "destination": pathlib.Path("1.rst"),
                }
            )
        ],
        settings={"initial_header_level": 3},
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": _pytest_regex(
                    # by default, initial header level is 2 and so the sections
                    # would start with <h2>
                    r"<h3>section 1</h3>\s*"
                    r"<p>aaa</p>\s*"
                    r"<h3>section 2</h3>\s*"
                    r"<p>bbb</p>\s*"
                ),
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
    """reStructuredText processor has to work with stream."""

    stream = restructuredtext.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the key is **%d**" % i,
                    "destination": pathlib.Path("1.rst"),
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
    ["args", "error"],
    [
        pytest.param(
            {"settings": 42},
            "settings: 42 is not of type 'object'",
            id="settings-int",
        )
    ],
)
def test_args_bad_value(testapp, args, error):
    """reStructuredText processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(restructuredtext.process(testapp, [], **args))
    assert str(excinfo.value) == error
