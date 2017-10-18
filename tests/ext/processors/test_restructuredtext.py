"""ReStructuredText processors test suite."""

import re
import textwrap

import mock
import pytest

from holocron import app, content
from holocron.ext.processors import restructuredtext


def _get_document(cls=content.Page, **kwargs):
    document = cls(app.Holocron({}))
    document['destination'] = 'about/cv.rst'
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    return mock.Mock()


def test_document(testapp):
    """reStructuredText processor has to work in simple case."""

    documents = restructuredtext.process(
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
            '<p>text with <strong>bold</strong></p>\s*'
        ),
        documents[0].content)

    assert documents[0].destination.endswith('.html')
    assert documents[0].title == 'some title'


def test_document_with_subsection(testapp):
    """reStructuredText processor has to start subsections with <h2>."""

    documents = restructuredtext.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    some title
                    ==========

                    abstract

                    some section
                    ------------

                    text with **bold**
                '''))
        ])

    assert re.match(
        (
            '<p>abstract</p>\s*'
            '<h2>some section</h2>\s*'
            '<p>text with <strong>bold</strong></p>\s*'
        ),
        documents[0].content)

    assert documents[0].destination.endswith('.html')
    assert documents[0].title == 'some title'


def test_document_without_title(testapp):
    """reStructuredText processor has to work even without a title."""

    documents = restructuredtext.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    text with **bold**
                '''))
        ])

    assert re.match(
        (
            '<p>text with <strong>bold</strong></p>\s*'
        ),
        documents[0].content)

    assert documents[0].destination.endswith('.html')
    assert not hasattr(documents[0], 'title')


def test_document_with_sections(testapp):
    """reStructuredText processor has to work with a lot of sections."""

    documents = restructuredtext.process(
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

                    some title 2
                    ============

                    xxx

                    some section 3
                    --------------

                    yyy
                '''))
        ])

    assert re.match(
        (
            '<h2>some title 1</h2>\s*'
            '<p>aaa</p>\s*'
            '<h3>some section 1</h3>\s*'
            '<p>bbb</p>\s*'
            '<h3>some section 2</h3>\s*'
            '<p>ccc</p>\s*'
            '<h2>some title 2</h2>\s*'
            '<p>xxx</p>\s*'
            '<h3>some section 3</h3>\s*'
            '<p>yyy</p>\s*'
        ),
        documents[0].content)

    assert documents[0].destination.endswith('.html')
    assert not hasattr(documents[0], 'title')


def test_document_with_code(testapp):
    """reStructuredText processor has to highlight code with Pygments."""

    documents = restructuredtext.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    test codeblock

                    .. code:: python

                        lambda x: pass
                '''))
        ])

    assert re.match(
        (
            r'<p>test codeblock</p>\s*<pre.*python[^>]*>[\s\S]+</pre>'
        ),
        documents[0].content)

    assert documents[0].destination.endswith('.html')
    assert not hasattr(documents[0], 'title')


def test_document_with_inline_code(testapp):
    """reStructuredText processor has to use <code> tag for inline code."""

    documents = restructuredtext.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    test ``code``
                '''))
        ])

    assert re.match(
        (
            '<p>test <code>code</code></p>'
        ),
        documents[0].content)

    assert documents[0].destination.endswith('.html')
    assert not hasattr(documents[0], 'title')


def test_document_with_setting(testapp):
    """reStructuredText processor has to respect custom settings."""

    documents = restructuredtext.process(
        testapp,
        [
            _get_document(
                content=textwrap.dedent('''\
                    section 1
                    =========

                    aaa

                    section 2
                    =========

                    bbb
                '''))
        ],
        docutils={
            'initial_header_level': 3,
        })

    # by default, initial header level is 2 and so the sections would
    # start with <h2>
    assert re.match(
        (
            '<h3>section 1</h3>\s*'
            '<p>aaa</p>\s*'
            '<h3>section 2</h3>\s*'
            '<p>bbb</p>\s*'
        ),
        documents[0].content)
    assert documents[0].destination.endswith('.html')
    assert not hasattr(documents[0], 'title')


def test_documents(testapp):
    """reStructuredText processor has to ignore non-targeted documents."""

    documents = restructuredtext.process(
        testapp,
        [
            _get_document(
                content='**wookiee**',
                source='0.txt',
                destination='0.txt'),
            _get_document(
                content='**wookiee**',
                source='1.rst',
                destination='1.rst'),
            _get_document(
                content='wookiee\n=======',
                source='2',
                destination='2'),
            _get_document(
                content='wookiee\n=======',
                source='3.rest',
                destination='3.rest'),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(rst|rest)$',
            },
        ])

    assert documents[0].source == '0.txt'
    assert documents[0].content == '**wookiee**'
    assert documents[0].destination.endswith('0.txt')
    assert not hasattr(documents[0], 'title')

    assert documents[1].source == '1.rst'
    assert documents[1].content == '<p><strong>wookiee</strong></p>'
    assert documents[1].destination.endswith('1.html')
    assert not hasattr(documents[1], 'title')

    assert documents[2].source == '2'
    assert documents[2].content == 'wookiee\n======='
    assert documents[2].destination.endswith('2')
    assert not hasattr(documents[2], 'title')

    assert documents[3].source == '3.rest'
    assert documents[3].content == ''
    assert documents[3].destination.endswith('3.html')
    assert documents[3].title == 'wookiee'
