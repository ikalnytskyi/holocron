"""Jinja2 processor test suite."""

import os
import textwrap
import unittest.mock

import pytest
import bs4

from holocron import app
from holocron.ext.processors import jinja2


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron({})


def test_document(testapp):
    """Jinja2 processor has to work!"""

    stream = jinja2.process(
        testapp,
        [
            {
                'title': 'History of the Force',
                'content': 'the Force',
            },
        ])

    document = next(stream)
    assert document == \
        {
            'title': 'History of the Force',
            'content': unittest.mock.ANY,
        }

    soup = bs4.BeautifulSoup(document['content'], 'html.parser')
    assert soup.meta['charset'] == 'UTF-8'
    assert soup.article.header.h1.string == 'History of the Force'
    assert list(soup.article.stripped_strings)[1] == 'the Force'

    # Since we don't know in which order statics are discovered, we sort them
    # so we can avoid possible flakes.
    static = sorted(stream, key=lambda d: d['source'])
    assert static[0]['source'] == os.path.join('static', 'logo.svg')
    assert static[0]['destination'] == static[0]['source']
    assert static[1]['source'] == os.path.join('static', 'pygments.css')
    assert static[1]['destination'] == static[1]['source']
    assert static[2]['source'] == os.path.join('static', 'style.css')
    assert static[2]['destination'] == static[2]['source']
    assert len(static) == 3


def test_document_template(testapp, tmpdir):
    """Jinja2 processor has to respect document suggested template."""

    tmpdir.ensure('theme_a', 'templates', 'holiday.j2').write_text(
        textwrap.dedent('''\
            template: my super template
            rendered: {{ document.title }}
        '''),
        encoding='UTF-8')

    stream = jinja2.process(
        testapp,
        [
            {
                'title': 'History of the Force',
                'content': 'the Force',
                'template': 'holiday.j2',
            },
        ],
        themes=[tmpdir.join('theme_a').strpath])

    assert next(stream) == \
        {
            'title': 'History of the Force',
            'template': 'holiday.j2',
            'content': textwrap.dedent('''\
                template: my super template
                rendered: History of the Force''')
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_themes(testapp, tmpdir):
    """Jinja2 processor has to respect themes parameter."""

    tmpdir.ensure('theme_a', 'templates', 'page.j2').write_text(
        textwrap.dedent('''\
            template: my super template
            rendered: {{ document.title }}
        '''),
        encoding='UTF-8')

    tmpdir.ensure('theme_a', 'static', 'style.css').write_text(
        'article { margin: 0 }',
        encoding='UTF-8')

    stream = jinja2.process(
        testapp,
        [
            {
                'title': 'History of the Force',
                'content': 'the Force',
            },
        ],
        themes=[tmpdir.join('theme_a').strpath])

    assert next(stream) == \
        {
            'title': 'History of the Force',
            'content': textwrap.dedent('''\
                template: my super template
                rendered: History of the Force''')
        }

    assert next(stream) == \
        {
            'content': 'article { margin: 0 }',
            'source': os.path.join('static', 'style.css'),
            'destination': os.path.join('static', 'style.css'),
            'created': unittest.mock.ANY,
            'updated': unittest.mock.ANY,
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_themes_two_themes(testapp, tmpdir):
    """Jinja2 processor has to respect themes parameter."""

    tmpdir.ensure('theme_a', 'templates', 'page.j2').write_text(
        textwrap.dedent('''\
            template: my super template from theme_a
            rendered: {{ document.title }}
        '''),
        encoding='UTF-8')

    tmpdir.ensure('theme_b', 'templates', 'page.j2').write_text(
        textwrap.dedent('''\
            template: my super template from theme_b
            rendered: {{ document.title }}
        '''),
        encoding='UTF-8')

    tmpdir.ensure('theme_b', 'templates', 'holiday.j2').write_text(
        textwrap.dedent('''\
            template: my holiday template from theme_b
            rendered: {{ document.title }}
        '''),
        encoding='UTF-8')

    stream = jinja2.process(
        testapp,
        [
            {
                'title': 'History of the Force',
                'content': 'the Force',
                'template': 'page.j2',
            },
            {
                'title': 'History of the Force',
                'content': 'the Force',
                'template': 'holiday.j2',
            },
        ],
        themes=[
            tmpdir.join('theme_a').strpath,
            tmpdir.join('theme_b').strpath,
        ])

    assert next(stream) == \
        {
            'title': 'History of the Force',
            'template': 'page.j2',
            'content': textwrap.dedent('''\
                template: my super template from theme_a
                rendered: History of the Force''')
        }

    assert next(stream) == \
        {
            'title': 'History of the Force',
            'template': 'holiday.j2',
            'content': textwrap.dedent('''\
                template: my holiday template from theme_b
                rendered: History of the Force''')
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_when(testapp):
    """Jinja2 processor has to ignore non-relevant documents."""

    stream = jinja2.process(
        testapp,
        [
            {
                'title': 'History of the Force #1',
                'content': 'the Force #1',
                'source': os.path.join('posts', '1.md'),
            },
            {
                'title': 'History of the Force #2',
                'content': 'the Force #2',
                'source': os.path.join('pages', '2.md'),
            },
            {
                'title': 'History of the Force #3',
                'content': 'the Force #3',
                'source': os.path.join('posts', '3.md'),
            },
            {
                'title': 'History of the Force #4',
                'content': 'the Force #4',
                'source': os.path.join('pages', '4.md'),
            },
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    document = next(stream)
    assert document == \
        {
            'title': 'History of the Force #1',
            'source': os.path.join('posts', '1.md'),
            'content': unittest.mock.ANY,
        }
    assert document['title'] == 'History of the Force #1'
    soup = bs4.BeautifulSoup(document['content'], 'html.parser')
    assert soup.meta['charset'] == 'UTF-8'
    assert soup.article.header.h1.string == 'History of the Force #1'
    assert list(soup.article.stripped_strings)[1] == 'the Force #1'

    assert next(stream) == \
        {
            'title': 'History of the Force #2',
            'source': os.path.join('pages', '2.md'),
            'content': 'the Force #2',
        }

    document = next(stream)
    assert document == \
        {
            'title': 'History of the Force #3',
            'source': os.path.join('posts', '3.md'),
            'content': unittest.mock.ANY,
        }
    assert document['title'] == 'History of the Force #3'
    soup = bs4.BeautifulSoup(document['content'], 'html.parser')
    assert soup.meta['charset'] == 'UTF-8'
    assert soup.article.header.h1.string == 'History of the Force #3'
    assert list(soup.article.stripped_strings)[1] == 'the Force #3'

    assert next(stream) == \
        {
            'title': 'History of the Force #4',
            'source': os.path.join('pages', '4.md'),
            'content': 'the Force #4',
        }

    # Since we don't know in which order statics are discovered, we sort them
    # so we can avoid possible flakes.
    static = sorted(stream, key=lambda d: d['source'])
    assert static[-3]['source'] == os.path.join('static', 'logo.svg')
    assert static[-3]['destination'] == static[0]['source']
    assert static[-2]['source'] == os.path.join('static', 'pygments.css')
    assert static[-2]['destination'] == static[1]['source']
    assert static[-1]['source'] == os.path.join('static', 'style.css')
    assert static[-1]['destination'] == static[2]['source']
    assert len(static) == 3


@pytest.mark.parametrize('params, error', [
    ({'when': [42]}, 'when: unsupported value'),
    ({'template': 42}, "template: 42 should be instance of 'str'"),
    ({'themes': {'foo': 1}}, 'themes: unsupported value'),
    ({'context': 42}, 'context: must be a dict'),
])
def test_param_bad_value(testapp, params, error):
    """Commit processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(jinja2.process(testapp, [], **params))
