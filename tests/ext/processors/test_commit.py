"""Commit processor test suite."""

import os

import py
import pytest

from holocron import app
from holocron.ext.processors import commit


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron()


def test_document(testapp, monkeypatch, tmpdir):
    """Commit processor has to work!"""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Obi-Wan',
                'destination': '1.html',
            },
        ])

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', '1.html').read_text('UTF-8') == 'Obi-Wan'


@pytest.mark.parametrize('data, loader', [
    (u'text', py.path.local.read),
    (b'\xf1', py.path.local.read_binary),
])
def test_document_content_types(testapp, monkeypatch, tmpdir, data, loader):
    """Commit processor has to properly write documents' content."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': data,
                'destination': '1.dat',
            },
        ])

    with pytest.raises(StopIteration):
        next(stream)

    assert loader(tmpdir.join('_site', '1.dat')) == data


@pytest.mark.parametrize('destination', [
    os.path.join('1.txt'),
    os.path.join('a', '2.txt'),
    os.path.join('a', 'b', '3.txt'),
    os.path.join('a', 'b', 'c', '4.txt'),
])
def test_document_destination(testapp, monkeypatch, tmpdir, destination):
    """Commit processor has to properly use destination."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Obi-Wan',
                'destination': destination,
            },
        ])

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', destination).read_text('UTF-8') == 'Obi-Wan'


@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding(testapp, monkeypatch, tmpdir, encoding):
    """Commit processor has to respect encoding parameter."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Оби-Ван',
                'destination': '1.html',
            },
        ],
        encoding=encoding)

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', '1.html').read_text(encoding) == 'Оби-Ван'


@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding_fallback(testapp, monkeypatch, tmpdir, encoding):
    """Commit processor has to respect encoding parameter (fallback)."""

    monkeypatch.chdir(tmpdir)
    testapp.metadata.update({'encoding': encoding})

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Оби-Ван',
                'destination': '1.html',
            },
        ])

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', '1.html').read_text(encoding) == 'Оби-Ван'


@pytest.mark.parametrize('unload', [False, True])
def test_param_unload(testapp, monkeypatch, tmpdir, unload):
    """Commit processor has to respect unload parameter."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Obi-Wan',
                'destination': '1.html',
            },
        ],
        unload=unload)

    if not unload:
        assert next(stream) == {
            'content': 'Obi-Wan',
            'destination': '1.html',
        }

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', '1.html').read_text('UTF-8') == 'Obi-Wan'


@pytest.mark.parametrize('path', ['_build', '_public'])
def test_param_path(testapp, monkeypatch, tmpdir, path):
    """Commit processor has to respect path parameter."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Obi-Wan',
                'destination': '1.html',
            },
        ],
        path=path)

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join(path, '1.html').read_text('UTF-8') == 'Obi-Wan'


def test_param_when(testapp, monkeypatch, tmpdir):
    """Commit processor has to ignore non-relevant documents."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Obi-Wan',
                'source': '1.md',
                'destination': '1.html',
            },
            {
                'content': 'Luke',
                'source': '2.rst',
                'destination': '2.html',
            },
            {
                'content': 'Yoda',
                'source': '3.md',
                'destination': '3.html',
            },
            {
                'content': 'Vader',
                'source': '4.rst',
                'destination': '4.html',
            },
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^.*\.md$',
            },
        ])

    assert next(stream) == {
        'content': 'Luke',
        'source': '2.rst',
        'destination': '2.html',
    }

    assert next(stream) == {
        'content': 'Vader',
        'source': '4.rst',
        'destination': '4.html',
    }

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', '1.html').read_text('UTF-8') == 'Obi-Wan'
    assert tmpdir.join('_site', '3.html').read_text('UTF-8') == 'Yoda'


@pytest.mark.parametrize('params, error', [
    ({'path': 42}, "path: 42 should be instance of 'str'"),
    ({'when': [42]}, 'when: unsupported value'),
    ({'encoding': 'UTF-42'}, 'encoding: unsupported encoding'),
    ({'unload': 42}, "unload: 42 should be instance of 'bool'"),
])
def test_param_bad_value(testapp, params, error):
    """Commit processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(commit.process(testapp, [], **params))
