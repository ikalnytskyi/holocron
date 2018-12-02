"""Commit processor test suite."""

import os

import py
import pytest
import bs4

from holocron import app, content
from holocron.ext.processors import commit


def _get_document(cls=content.Document, **kwargs):
    document = cls(app.Holocron({}))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})
    return instance


def test_document(testapp, monkeypatch, tmpdir):
    """Commit processor has to work!"""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(
                content='the Force',
                destination=os.path.join('posts', '1.html')),
        ])

    assert documents == []

    text = tmpdir.join('_site', 'posts', '1.html').read()
    assert text == 'the Force'


def test_document_template(testapp, monkeypatch, tmpdir):
    """Commit processor has to render a document."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(
                template='page.j2',
                title='History of the Force',
                content='the Force',
                destination=os.path.join('posts', '1.html')),
        ],
        encoding='CP1251')

    assert documents == []

    html = tmpdir.join('_site', 'posts', '1.html').read()
    soup = bs4.BeautifulSoup(html, 'html.parser')

    assert soup.meta['charset'] == 'CP1251'
    assert soup.article.header.h1.string == 'History of the Force'
    assert list(soup.article.stripped_strings)[1] == 'the Force'


def test_document_options(testapp, monkeypatch, tmpdir):
    """Commit processor has to respect custom options."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(
                content='\u0421\u0438\u043b\u0430',
                destination='1.html'),
        ],
        path='_build',
        unload=False,
        encoding='CP1251')

    assert len(documents) == 1

    assert documents[0]['content'] == '\u0421\u0438\u043b\u0430'
    assert documents[0]['destination'] == '1.html'

    assert tmpdir.join('_build', '1.html').read_binary() == b'\xd1\xe8\xeb\xe0'


def test_document_with_custom_encoding(testapp, monkeypatch, tmpdir):
    """Commit processor has to respect suggested encoding."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(
                content='\u0421\u0438\u043b\u0430',
                encoding='CP1251',
                destination='1.html'),
        ],
        encoding='UTF-8')

    assert len(documents) == 0

    assert tmpdir.join('_site', '1.html').read_binary() == b'\xd1\xe8\xeb\xe0'


@pytest.mark.parametrize('data, loader', [
    (u'text', py.path.local.read),
    (b'\xf1', py.path.local.read_binary),
])
def test_document_content_types(testapp, monkeypatch, tmpdir, data, loader):
    """Commit processor has to properly write documents' content."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(
                content=data,
                destination=os.path.join('cv.pdf')),
        ])

    assert documents == []
    assert loader(tmpdir.join('_site', 'cv.pdf')) == data


def test_documents(testapp, monkeypatch, tmpdir):
    """Commit processor has to ignore non-relevant documents."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(
                content='the Force #1',
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html')),
            _get_document(
                content='the Force #2',
                source=os.path.join('pages', '2.md'),
                destination=os.path.join('pages', '2.html')),
            _get_document(
                content='the Force #3',
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html')),
            _get_document(
                content='the Force #4',
                source=os.path.join('pages', '4.md'),
                destination=os.path.join('pages', '4.html')),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    assert len(documents) == 2

    assert documents[0]['content'] == 'the Force #2'
    assert documents[0]['source'] == os.path.join('pages', '2.md')
    assert documents[0]['destination'] == os.path.join('pages', '2.html')

    assert documents[1]['content'] == 'the Force #4'
    assert documents[1]['source'] == os.path.join('pages', '4.md')
    assert documents[1]['destination'] == os.path.join('pages', '4.html')

    assert tmpdir.join('_site', 'posts', '1.html').read() == 'the Force #1'
    assert tmpdir.join('_site', 'posts', '3.html').read() == 'the Force #3'


@pytest.mark.parametrize('options, error', [
    ({'path': 42}, "path: 42 should be instance of 'str'"),
    ({'when': [42]}, 'when: unsupported value'),
    ({'encoding': 'UTF-42'}, 'encoding: unsupported encoding'),
    ({'unload': 42}, "unload: 42 should be instance of 'bool'"),
])
def test_parameters_schema(testapp, options, error):
    with pytest.raises(ValueError, match=error):
        commit.process(testapp, [], **options)
