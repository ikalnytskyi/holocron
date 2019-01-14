"""Commit processor test suite."""

import os

import py
import pytest

from holocron import app
from holocron.processors import commit


@pytest.fixture(scope='function')
def testapp(request):
    return app.Holocron()


def test_item(testapp, monkeypatch, tmpdir):
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

    assert next(stream) == \
        {
            'content': 'Obi-Wan',
            'destination': '1.html',
        }

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', '1.html').read_text('UTF-8') == 'Obi-Wan'


@pytest.mark.parametrize('data, loader', [
    (u'text', py.path.local.read),
    (b'\xf1', py.path.local.read_binary),
])
def test_item_content_types(testapp, monkeypatch, tmpdir, data, loader):
    """Commit processor has to properly write items' content."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': data,
                'destination': '1.dat',
            },
        ])

    assert next(stream) == \
        {
            'content': data,
            'destination': '1.dat',
        }

    with pytest.raises(StopIteration):
        next(stream)

    assert loader(tmpdir.join('_site', '1.dat')) == data


@pytest.mark.parametrize('destination', [
    os.path.join('1.txt'),
    os.path.join('a', '2.txt'),
    os.path.join('a', 'b', '3.txt'),
    os.path.join('a', 'b', 'c', '4.txt'),
])
def test_item_destination(testapp, monkeypatch, tmpdir, destination):
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

    assert next(stream) == \
        {
            'content': 'Obi-Wan',
            'destination': destination,
        }

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', destination).read_text('UTF-8') == 'Obi-Wan'


@pytest.mark.parametrize('amount', [0, 1, 2, 5, 10])
def test_item_many(testapp, monkeypatch, tmpdir, amount):
    """Commit processor has to work with stream."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Obi-Wan',
                'destination': str(i),
            }
            for i in range(amount)
        ])

    for i in range(amount):
        assert next(stream) == \
            {
                'content': 'Obi-Wan',
                'destination': str(i),
            }
        assert tmpdir.join('_site', str(i)).read_text('UTF-8') == 'Obi-Wan'

    with pytest.raises(StopIteration):
        next(stream)


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

    assert next(stream) == \
        {
            'content': 'Оби-Ван',
            'destination': '1.html',
        }

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

    assert next(stream) == \
        {
            'content': 'Оби-Ван',
            'destination': '1.html',
        }

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join('_site', '1.html').read_text(encoding) == 'Оби-Ван'


@pytest.mark.parametrize('save_to', ['_build', '_public'])
def test_param_save_to(testapp, monkeypatch, tmpdir, save_to):
    """Commit processor has to respect save_to parameter."""

    monkeypatch.chdir(tmpdir)

    stream = commit.process(
        testapp,
        [
            {
                'content': 'Obi-Wan',
                'destination': '1.html',
            },
        ],
        save_to=save_to)

    assert next(stream) == \
        {
            'content': 'Obi-Wan',
            'destination': '1.html',
        }

    with pytest.raises(StopIteration):
        next(stream)

    assert tmpdir.join(save_to, '1.html').read_text('UTF-8') == 'Obi-Wan'


@pytest.mark.parametrize('params, error', [
    ({'save_to': 42}, "save_to: 42 should be instance of 'str'"),
    ({'encoding': 'UTF-42'}, 'encoding: unsupported encoding'),
])
def test_param_bad_value(testapp, params, error):
    """Commit processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(commit.process(testapp, [], **params))
