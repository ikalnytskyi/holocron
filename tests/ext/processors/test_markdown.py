"""Markdown processor test suite."""

import re
import textwrap

import mock
import pytest

from holocron import app, content
from holocron.ext.processors import markdown


def _get_document(**kwargs):
    document = content.Document(app.Holocron({}))
    document['destination'] = 'about/cv.md'
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    return mock.Mock()


def test_document(testapp):
    """Markdown processor has to work."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    # some title

                    text with **bold**
                '''))
        ])

    assert re.match(
        (
            r'<p>text with <strong>bold</strong></p>'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert documents[0]['title'] == 'some title'


def test_document_with_alt_title_syntax(testapp):
    """Markdown processor has to work with alternative title syntax."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    some title
                    ==========

                    text with **bold**
                '''))
        ])

    assert re.match(
        (
            r'<p>text with <strong>bold</strong></p>'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert documents[0]['title'] == 'some title'


def test_document_with_newlines_at_the_beginning(testapp):
    """Markdown processor has to ignore newlines at the beginning."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\


                    # some title

                    text with **bold**
                '''))
        ])

    assert re.match(
        (
            r'<p>text with <strong>bold</strong></p>'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert documents[0]['title'] == 'some title'


def test_document_without_title(testapp):
    """Markdown processor has to work process documents without title."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    text with **bold**
                '''))
        ])

    assert re.match(
        (
            r'<p>text with <strong>bold</strong></p>'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert 'title' not in documents[0]


def test_document_title_is_not_overwritten(testapp):
    """Markdown processor hasn't to set title if it's already set."""

    document = _get_document(
        content=textwrap.dedent('''\
            # some title

            text with **bold**
        '''))
    document['title'] = 'another title'
    documents = markdown.process(testapp, [document])

    assert re.match(
        (
            r'<p>text with <strong>bold</strong></p>'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert documents[0]['title'] == 'another title'


def test_document_title_ignored_in_the_middle_of_text(testapp):
    """Markdown processor has to ignore title if it's in the middle of text."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    text

                    # some title

                    text with **bold**
                '''))
        ])

    assert re.match(
        (
            r'<p>text</p>\s*'
            r'<h1>some title</h1>\s*'
            r'<p>text with <strong>bold</strong></p>'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert 'title' not in documents[0]


def test_document_with_sections(testapp):
    """Markdown processor has to work even for complex documents."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
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
                '''))
        ])

    assert re.match(
        (
            r'<p>aaa</p>\s*'
            r'<h2>some section 1</h2>\s*<p>bbb</p>\s*'
            r'<h2>some section 2</h2>\s*<p>ccc</p>\s*'
            r'<h1>some title 2</h1>\s*<p>xxx</p>\s*'
            r'<h2>some section 3</h2>\s*<p>yyy</p>\s*'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert documents[0]['title'] == 'some title 1'


def test_document_with_code(testapp):
    """Markdown processor has to highlight code with codehilite extension."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    test codeblock

                        :::python
                        lambda x: pass
                '''))
        ])

    assert re.match(
        (
            r'<p>test codeblock</p>\s*.*codehilite.*<pre>[\s\S]+</pre>.*'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert 'title' not in documents[0]


def test_document_with_fenced_code(testapp):
    """Markdown processor has to support GitHub's fence code syntax."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    ```python
                    lambda x: pass
                    ```
                '''))
        ])

    assert re.match(
        (
            r'.*codehilite.*<pre>[\s\S]+</pre>.*'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert 'title' not in documents[0]


def test_document_with_table(testapp):
    """Markdown processor has to support table syntax (markup extension)."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    column a | column b
                    ---------|---------
                       foo   |   bar
                '''))
        ])

    assert 'table' in documents[0]['content']

    assert '<th>column a</th>' in documents[0]['content']
    assert '<th>column b</th>' in documents[0]['content']

    assert '<td>foo</td>' in documents[0]['content']
    assert '<td>bar</td>' in documents[0]['content']

    assert documents[0]['destination'].endswith('.html')
    assert 'title' not in documents[0]


def test_document_with_inline_code(testapp):
    """Markdown processor has to use <code> for inline code."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    test `code`
                '''))
        ])

    assert documents[0]['content'] == '<p>test <code>code</code></p>'
    assert documents[0]['destination'].endswith('.html')
    assert 'title' not in documents[0]


def test_document_with_custom_extensions(testapp):
    """Markdown processor has to respect custom extensions."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    ```
                    lambda x: pass
                    ```
                '''))
        ],
        extensions=[])

    # when no extensions are passed, syntax highlighting is turned off
    assert re.match(
        (
            r'<p><code>lambda x: pass</code></p>'
        ),
        documents[0]['content'])

    assert documents[0]['destination'].endswith('.html')
    assert 'title' not in documents[0]


def test_documents(testapp):
    """Markdown processor has to ignore non-markdown documents."""

    documents = markdown.process(
        testapp,
        [
            _get_document(
                content='**wookiee**',
                source='0.txt',
                destination='0.txt'),
            _get_document(
                content='**wookiee**',
                source='1.md',
                destination='1.md'),
            _get_document(
                content='# wookiee',
                source='2',
                destination='2'),
            _get_document(
                content='# wookiee',
                source='3.markdown',
                destination='3.markdown'),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(md|mkd|mdown|markdown)$',
            },
        ])

    assert documents[0]['source'] == '0.txt'
    assert documents[0]['content'] == '**wookiee**'
    assert documents[0]['destination'].endswith('0.txt')
    assert 'title' not in documents[0]

    assert documents[1]['source'] == '1.md'
    assert documents[1]['content'] == '<p><strong>wookiee</strong></p>'
    assert documents[1]['destination'].endswith('1.html')
    assert 'title' not in documents[1]

    assert documents[2]['source'] == '2'
    assert documents[2]['content'] == '# wookiee'
    assert documents[2]['destination'].endswith('2')
    assert 'title' not in documents[2]

    assert documents[3]['source'] == '3.markdown'
    assert documents[3]['content'] == ''
    assert documents[3]['destination'].endswith('3.html')
    assert documents[3]['title'] == 'wookiee'
