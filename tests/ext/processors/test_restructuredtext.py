"""ReStructuredText processors test suite."""

import re
import textwrap

import pytest

from holocron import app
from holocron.ext.processors import restructuredtext


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
        streams.append(restructuredtext.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


def test_document(testapp, run_processor):
    """reStructuredText processor has to work in simple case."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    some title
                    ==========

                    text with **bold**
                '''),
                'destination': '1.rst',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text with <strong>bold</strong></p>\s*'),
            'destination': '1.html',
            'title': 'some title',
        }


def test_document_with_subsection(testapp, run_processor):
    """reStructuredText processor has to start subsections with <h2>."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    some title
                    ==========

                    abstract

                    some section
                    ------------

                    text with **bold**
                '''),
                'destination': '1.rst',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>abstract</p>\s*'
                r'<h2>some section</h2>\s*'
                r'<p>text with <strong>bold</strong></p>\s*'),
            'destination': '1.html',
            'title': 'some title',
        }


def test_document_without_title(testapp, run_processor):
    """reStructuredText processor has to work even without a title."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    text with **bold**
                '''),
                'destination': '1.rst',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>text with <strong>bold</strong></p>\s*'),
            'destination': '1.html',
        }


def test_document_with_sections(testapp, run_processor):
    """reStructuredText processor has to work with a lot of sections."""

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

                    some title 2
                    ============

                    xxx

                    some section 3
                    --------------

                    yyy
                '''),
                'destination': '1.rst',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<h2>some title 1</h2>\s*'
                r'<p>aaa</p>\s*'
                r'<h3>some section 1</h3>\s*'
                r'<p>bbb</p>\s*'
                r'<h3>some section 2</h3>\s*'
                r'<p>ccc</p>\s*'
                r'<h2>some title 2</h2>\s*'
                r'<p>xxx</p>\s*'
                r'<h3>some section 3</h3>\s*'
                r'<p>yyy</p>\s*'),
            'destination': '1.html',
        }


def test_document_with_code(testapp, run_processor):
    """reStructuredText processor has to highlight code with Pygments."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    test codeblock

                    .. code:: python

                        lambda x: pass
                '''),
                'destination': '1.rst',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(
                r'<p>test codeblock</p>\s*<pre.*python[^>]*>[\s\S]+</pre>'),
            'destination': '1.html',
        }


def test_document_with_inline_code(testapp, run_processor):
    """reStructuredText processor has to use <code> tag for inline code."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    test ``code``
                '''),
                'destination': '1.rst',
            },
        ])

    assert next(stream) == \
        {
            'content': _pytest_regex(r'<p>test <code>code</code></p>'),
            'destination': '1.html',
        }


def test_param_docutils(testapp, run_processor):
    """reStructuredText processor has to respect custom settings."""

    stream = run_processor(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    section 1
                    =========

                    aaa

                    section 2
                    =========

                    bbb
                '''),
                'destination': '1.rst',
            },
        ],
        docutils={
            'initial_header_level': 3,
        })

    assert next(stream) == \
        {
            'content': _pytest_regex(
                # by default, initial header level is 2 and so the sections
                # would start with <h2>
                r'<h3>section 1</h3>\s*'
                r'<p>aaa</p>\s*'
                r'<h3>section 2</h3>\s*'
                r'<p>bbb</p>\s*'),
            'destination': '1.html',
        }


def test_param_when(testapp, run_processor):
    """reStructuredText processor has to ignore non-targeted documents."""

    stream = run_processor(
        testapp,
        [
            {
                'content': '**wookiee**',
                'source': '0.txt',
                'destination': '0.txt',
            },
            {
                'content': '**wookiee**',
                'source': '1.rst',
                'destination': '1.rst',
            },
            {
                'content': 'wookiee\n=======',
                'source': '2',
                'destination': '2',
            },
            {
                'content': 'wookiee\n=======',
                'source': '3.rest',
                'destination': '3.rest',
            },
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(rst|rest)$',
            },
        ])

    assert next(stream) == \
        {
            'source': '0.txt',
            'content': '**wookiee**',
            'destination': '0.txt',
        }

    assert next(stream) == \
        {
            'source': '1.rst',
            'content': '<p><strong>wookiee</strong></p>',
            'destination': '1.html',
        }

    assert next(stream) == \
        {
            'source': '2',
            'content': 'wookiee\n=======',
            'destination': '2',
        }

    assert next(stream) == \
        {
            'source': '3.rest',
            'content': '',
            'destination': '3.html',
            'title': 'wookiee',
        }


@pytest.mark.parametrize('params, error', [
    ({'when': [42]}, 'when: unsupported value'),
    ({'docutils': 42}, "docutils: 42 should be instance of 'dict'"),
])
def test_param_bad_value(testapp, params, error):
    """reStructuredText processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(restructuredtext.process(testapp, [], **params))
