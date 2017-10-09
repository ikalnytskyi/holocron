"""Commit processor test suite."""

import os

import py
import pytest

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

    assert len(documents) == 0

    text = tmpdir.join('_site', 'posts', '1.html').read()
    assert text == 'the Force'


@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding(testapp, monkeypatch, tmpdir, encoding):
    """Commit processor has to respect encoding parameter."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(content='оби-ван', destination='1.html'),
        ],
        encoding=encoding)

    assert len(documents) == 0
    assert tmpdir.join('_site', '1.html').read_text(encoding) == 'оби-ван'


@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding_fallback(testapp, monkeypatch, tmpdir, encoding):
    """Commit processor has to respect encoding parameter (fallback)."""

    monkeypatch.chdir(tmpdir)
    testapp.metadata.update({'encoding': encoding})

    documents = commit.process(
        testapp,
        [
            _get_document(content='оби-ван', destination='1.html'),
        ])

    assert len(documents) == 0
    assert tmpdir.join('_site', '1.html').read_text(encoding) == 'оби-ван'


@pytest.mark.parametrize('unload', [False, True])
def test_param_unload(testapp, monkeypatch, tmpdir, unload):
    """Commit processor has to respect unload parameter."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(content='obi-wan', destination='1.html'),
        ],
        unload=unload)

    assert len(documents) == int(not unload)

    if not unload:
        assert documents[0]['content'] == 'obi-wan'
        assert documents[0]['destination'] == '1.html'


@pytest.mark.parametrize('path', ['_build', '_public'])
def test_param_path(testapp, monkeypatch, tmpdir, path):
    """Commit processor has to respect path parameter."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(content='obi-wan', destination='1.html'),
        ],
        path=path)

    assert len(documents) == 0
    assert tmpdir.join(path, '1.html').read() == 'obi-wan'


def test_document_custom_encoding(testapp, monkeypatch, tmpdir):
    """Commit processor has to respect suggested encoding."""

    monkeypatch.chdir(tmpdir)

    documents = commit.process(
        testapp,
        [
            _get_document(
                content='оби-ван',
                encoding='CP1251',
                destination='1.html'),
            _get_document(
                content='оби-ван',
                destination='2.html'),
        ],
        encoding='UTF-8')

    assert len(documents) == 0
    assert tmpdir.join('_site', '1.html').read_text('CP1251') == 'оби-ван'
    assert tmpdir.join('_site', '2.html').read_text('UTF-8') == 'оби-ван'


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

    assert len(documents) == 0
    assert loader(tmpdir.join('_site', 'cv.pdf')) == data


def test_param_when(testapp, monkeypatch, tmpdir):
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


@pytest.mark.parametrize('params, error', [
    ({'path': 42}, "path: 42 should be instance of 'str'"),
    ({'when': [42]}, 'when: unsupported value'),
    ({'encoding': 'UTF-42'}, 'encoding: unsupported encoding'),
    ({'unload': 42}, "unload: 42 should be instance of 'bool'"),
])
def test_param_bad_value(testapp, params, error):
    """Commit processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        commit.process(testapp, [], **params)
