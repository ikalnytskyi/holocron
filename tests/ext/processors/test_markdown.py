"""Markdown processor test suite."""

import re
import textwrap
import unittest.mock

import pytest

from holocron import app
from holocron.ext.processors import markdown


class _pytest_regex:
    """Assert that a given string meets some expectations."""

    def __init__(self, pattern, flags=0):
        self._regex = re.compile(pattern, flags)

    def __eq__(self, actual):
        return bool(self._regex.match(actual))

    def __repr__(self):
        return self._regex.pattern


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron()


@pytest.fixture(scope='function')
def run_processor():
    streams = []

    def run(*args, **kwargs):
        streams.append(markdown.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


def test_document(testapp, run_processor):
    """Markdown processor has to work."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    # some title

                    text with **bold**
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text with <strong>bold</strong></p>'),
            'destination': '1.html',
            'title': 'some title',
        }


def test_document_with_alt_title_syntax(testapp, run_processor):
    """Markdown processor has to work with alternative title syntax."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    some title
                    ==========

                    text with **bold**
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text with <strong>bold</strong></p>'),
            'destination': '1.html',
            'title': 'some title',
        }


def test_document_with_newlines_at_the_beginning(testapp, run_processor):
    """Markdown processor has to ignore newlines at the beginning."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\


                    # some title

                    text with **bold**
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text with <strong>bold</strong></p>'),
            'destination': '1.html',
            'title': 'some title',
        }


def test_document_without_title(testapp, run_processor):
    """Markdown processor has to work process documents without title."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    text with **bold**
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text with <strong>bold</strong></p>'),
            'destination': '1.html',
        }


def test_document_title_is_not_overwritten(testapp, run_processor):
    """Markdown processor hasn't to set title if it's already set."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    # some title

                    text with **bold**
                '''),
                'destination': '1.md',
                'title': 'another title',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text with <strong>bold</strong></p>'),
            'destination': '1.html',
            'title': 'another title',
        }


def test_document_title_ignored_in_the_middle_of_text(testapp, run_processor):
    """Markdown processor has to ignore title if it's in the middle of text."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    text

                    # some title

                    text with **bold**
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text</p>\s*'
                r'<h1>some title</h1>\s*'
                r'<p>text with <strong>bold</strong></p>'),
            'destination': '1.html',
        }


def test_document_with_sections(testapp, run_processor):
    """Markdown processor has to work even for complex documents."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
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
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>aaa</p>\s*'
                r'<h2>some section 1</h2>\s*<p>bbb</p>\s*'
                r'<h2>some section 2</h2>\s*<p>ccc</p>\s*'
                r'<h1>some title 2</h1>\s*<p>xxx</p>\s*'
                r'<h2>some section 3</h2>\s*<p>yyy</p>\s*'),
            'destination': '1.html',
            'title': 'some title 1',
        }


def test_document_with_code(testapp, run_processor):
    """Markdown processor has to highlight code with codehilite extension."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    test codeblock

                        :::python
                        lambda x: pass
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>test codeblock</p>\s*.*codehilite.*<pre>[\s\S]+</pre>.*'),
            'destination': '1.html',
        }


def test_document_with_fenced_code(testapp, run_processor):
    """Markdown processor has to support GitHub's fence code syntax."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    test codeblock

                    ```python
                    lambda x: pass
                    ```
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>test codeblock</p>\s*.*codehilite.*<pre>[\s\S]+</pre>.*'),
            'destination': '1.html',
        }


def test_document_with_table(testapp, run_processor):
    """Markdown processor has to support table syntax (markup extension)."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    column a | column b
                    ---------|---------
                       foo   |   bar
                '''),
                'destination': '1.md',
            },
        ])

    document = next(stream)
    assert document == \
        {
            'content': unittest.mock.ANY,
            'destination': '1.html',
        }

    assert 'table' in document['content']
    assert '<th>column a</th>' in document['content']
    assert '<th>column b</th>' in document['content']
    assert '<td>foo</td>' in document['content']
    assert '<td>bar</td>' in document['content']


def test_document_with_inline_code(testapp, run_processor):
    """Markdown processor has to use <code> for inline code."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    test `code`
                '''),
                'destination': '1.md',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(r'<p>test <code>code</code></p>'),
            'destination': '1.html',
        }


def test_param_extensions(testapp, run_processor):
    """Markdown processor has to respect extensions parameter."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    ```
                    lambda x: pass
                    ```
                '''),
                'destination': '1.md',
            },
        ],
        extensions=[])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                # no syntax highlighting when no extensions are passed
                r'<p><code>lambda x: pass</code></p>'),
            'destination': '1.html',
        }


def test_param_when(testapp, run_processor):
    """Markdown processor has to ignore non-markdown documents."""

    stream = run_processor(
        testapp,
        [
            {
                'content': '**wookiee**',
                'destination': '0.txt',
                'source': '0.txt',
            },
            {
                'content': '**wookiee**',
                'destination': '1.md',
                'source': '1.md',
            },
            {
                'content': '# wookiee',
                'destination': '2',
                'source': '2',
            },
            {
                'content': '# wookiee',
                'destination': '3.markdown',
                'source': '3.markdown',
            },
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(md|mkd|mdown|markdown)$',
            },
        ])

    assert next(stream) == \
        {
            'content': '**wookiee**',
            'destination': '0.txt',
            'source': '0.txt',
        }

    assert next(stream) == \
        {
            'content': _pytest_regex(r'<p><strong>wookiee</strong></p>'),
            'destination': '1.html',
            'source': '1.md',
        }

    assert next(stream) == \
        {
            'content': '# wookiee',
            'destination': '2',
            'source': '2'
        }

    assert next(stream) == \
        {
            'content': '',
            'destination': '3.html',
            'source': '3.markdown',
            'title': 'wookiee',
        }


@pytest.mark.parametrize('params, error', [
    ({'when': [42]}, 'when: unsupported value'),
    ({'extensions': 42}, "extensions: 42 should be instance of 'list'"),
])
def test_param_bad_value(testapp, params, error):
    """Markdown processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(markdown.process(testapp, [], **params))
