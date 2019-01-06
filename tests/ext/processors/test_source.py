"""Source processor test suite."""

import os
import datetime
import unittest.mock

import pytest

from holocron import app
from holocron.ext.processors import source


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron()


@pytest.fixture(scope='function')
def run_processor():
    streams = []

    def run(*args, **kwargs):
        streams.append(source.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


@pytest.mark.parametrize('path', [
    ['about', 'cv.pdf'],
    ['2017', '09', '17', 'cv.pdf'],
])
def test_document(testapp, run_processor, tmpdir, path):
    """run_processoror has to work."""

    tmpdir.ensure(*path).write_text('Obi-Wan', encoding='UTF-8')

    stream = run_processor(
        testapp,
        [
            {
                'source': os.path.join('images', 'me.png'),
            },
        ],
        path=tmpdir.strpath)

    assert next(stream) == \
        {
            'source': os.path.join('images', 'me.png'),
        }

    document = next(stream)

    assert document['source'] == os.path.join(*path)
    assert document['destination'] == os.path.join(*path)
    assert document['created'].timestamp() \
        == pytest.approx(tmpdir.join(*path).stat().ctime, 0.00001)
    assert document['updated'].timestamp() \
        == pytest.approx(tmpdir.join(*path).stat().mtime, 0.00001)
    assert document['content'] == 'Obi-Wan'

    if path[0] == '2017':
        assert document['published'] == datetime.date(2017, 9, 17)


@pytest.mark.parametrize('data', [
    u'text',
    b'\xf1',
])
def test_document_content_types(testapp, run_processor, tmpdir, data):
    """run_processoror has to properly read documents' content."""

    localpath = tmpdir.ensure('cv.md')

    if isinstance(data, bytes):
        localpath.write_binary(data)
    else:
        localpath.write_text(data, encoding='UTF-8')

    stream = run_processor(testapp, [], path=tmpdir.strpath)
    assert next(stream) == \
        {
            'source': 'cv.md',
            'destination': 'cv.md',
            'content': data,
            'created': unittest.mock.ANY,
            'updated': unittest.mock.ANY,
        }


def test_document_empty(testapp, run_processor, tmpdir):
    """run_processoror has to properly read empty documents."""

    tmpdir.ensure('cv.md').write_binary(b'')

    stream = run_processor(testapp, [], path=tmpdir.strpath)
    assert next(stream) == \
        {
            'source': 'cv.md',
            'destination': 'cv.md',
            'content': '',
            'created': unittest.mock.ANY,
            'updated': unittest.mock.ANY,
        }


@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding(testapp, run_processor, tmpdir, encoding):
    """run_processoror has to respect encoding parameter."""

    tmpdir.ensure('cv.md').write_text('Оби-Ван', encoding=encoding)

    stream = run_processor(
        testapp,
        [],
        path=tmpdir.strpath,
        encoding=encoding)

    assert next(stream) == \
        {
            'source': 'cv.md',
            'destination': 'cv.md',
            'content': 'Оби-Ван',
            'created': unittest.mock.ANY,
            'updated': unittest.mock.ANY,
        }


@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding_fallback(testapp, run_processor, tmpdir, encoding):
    """run_processoror has to respect encoding parameter (fallback)."""

    tmpdir.ensure('cv.md').write_text('Оби-Ван', encoding=encoding)
    testapp.metadata.update({'encoding': encoding})

    stream = run_processor(
        testapp,
        [],
        path=tmpdir.strpath)

    assert next(stream) == \
        {
            'source': 'cv.md',
            'destination': 'cv.md',
            'content': 'Оби-Ван',
            'created': unittest.mock.ANY,
            'updated': unittest.mock.ANY,
        }


@pytest.mark.parametrize('timezone, tznames', [
    ('UTC', ['UTC']),
    ('Europe/Kiev', ['EET', 'EEST']),
])
def test_param_timezone(testapp, run_processor, tmpdir, timezone, tznames):
    """run_processoror has to respect timezone parameter."""

    tmpdir.ensure('cv.md').write_text('Obi-Wan', encoding='UTF-8')

    stream = run_processor(
        testapp,
        [],
        path=tmpdir.strpath,
        timezone=timezone)

    document = next(stream)

    created = document['created']
    updated = document['updated']

    assert created.tzinfo.tzname(created) in tznames
    assert updated.tzinfo.tzname(updated) in tznames


@pytest.mark.parametrize('tz, tznames', [
    ('UTC', ['UTC']),
    ('Europe/Kiev', ['EET', 'EEST']),
])
def test_param_timezone_fallback(testapp, run_processor, tmpdir, tz, tznames):
    """run_processoror has to respect timezone parameter (fallback)."""

    tmpdir.ensure('cv.md').write_text('Obi-Wan', encoding='UTF-8')
    testapp.metadata.update({'timezone': tz})

    stream = run_processor(
        testapp,
        [],
        path=tmpdir.strpath)

    document = next(stream)

    created = document['created']
    updated = document['updated']

    assert created.tzinfo.tzname(created) in tznames
    assert updated.tzinfo.tzname(updated) in tznames


def test_param_timezone_in_action(testapp, run_processor, tmpdir):
    """run_processoror has to respect timezone parameter."""

    tmpdir.ensure('cv.md').write_text('Obi-Wan', encoding='UTF-8')

    stream_utc = run_processor(
        testapp, [], path=tmpdir.strpath, timezone='UTC')
    stream_kie = run_processor(
        testapp, [], path=tmpdir.strpath, timezone='Europe/Kiev')

    created_utc = next(stream_utc)['created']
    created_kie = next(stream_kie)['created']

    assert created_kie.tzinfo.utcoffset(created_kie) \
        >= created_utc.tzinfo.utcoffset(created_utc)
    assert created_kie.isoformat() > created_utc.isoformat()
    assert created_kie.isoformat().split('+')[-1] in ('02:00', '03:00')


def test_param_when(testapp, run_processor, tmpdir):
    """run_processoror has to ignore non-matched stream."""

    structure = sorted([
        ['about', 'index.md'],
        ['about', 'me.png'],
        ['cv.pdf'],
    ])

    for path in structure:
        tmpdir.ensure(*path)
    tmpdir.ensure('_config.yml')

    stream = run_processor(
        testapp,
        [],
        path=tmpdir.strpath,
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^(?!_).*$',
            },
        ])

    documents = sorted(stream, key=lambda document: document['source'])

    for document, path in zip(documents, structure):
        assert document == \
            {
                'source': os.path.join(*path),
                'destination': os.path.join(*path),
                'content': '',
                'created': unittest.mock.ANY,
                'updated': unittest.mock.ANY,
            }

        assert document['created'].timestamp() \
            == pytest.approx(tmpdir.join(*path).stat().ctime, 0.00001)
        assert document['updated'].timestamp() \
            == pytest.approx(tmpdir.join(*path).stat().mtime, 0.00001)


@pytest.mark.parametrize('params, error', [
    ({'path': 42}, "path: 42 should be instance of 'str'"),
    ({'when': 42}, 'when: unsupported value'),
    ({'encoding': 'UTF-42'}, 'encoding: unsupported encoding'),
    ({'timezone': 'Europe/Kharkiv'}, 'timezone: unsupported timezone'),
])
def test_param_bad_value(testapp, params, error):
    """run_processoror has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(source.process(testapp, [], **params))
