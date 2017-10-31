"""Source processor test suite."""

import os
import datetime

import pytest

from holocron import app, content
from holocron.ext.processors import source


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})

    # Create a fake converter for "*.md" files so source processor can
    # specially treat such files and create a convertible document.
    instance._converters['.md'] = None
    return instance


@pytest.mark.parametrize('path, cls', [
    (['about', 'cv.pdf'], content.Document),
    (['about', 'cv.md'], content.Page),
    (['2017', '09', '17', 'cv.md'], content.Post),
    (['2017', '09', '17', 'cv.rst'], content.Document),
    (['2017', '09', '17', 'cv.pdf'], content.Document),
])
def test_document(testapp, tmpdir, path, cls):
    """Source processor has to work."""

    tmpdir.ensure(*path).write_text('text', encoding='utf-8')

    preserved = content.Document(testapp)
    preserved['source'] = os.path.join('images', 'me.png')
    preserved['destination'] = os.path.join('images', 'me.png')

    documents = source.process(
        testapp,
        [
            preserved,
        ],
        path=tmpdir.strpath)

    assert len(documents) == 2

    assert documents[0]['source'] == os.path.join('images', 'me.png')
    assert documents[0]['destination'] == os.path.join('images', 'me.png')

    assert isinstance(documents[1], cls)
    assert documents[1]['source'] == os.path.join(*path)
    assert documents[1]['destination'] == os.path.join(*path)
    assert documents[1]['created'].timestamp() \
        == pytest.approx(tmpdir.join(*path).stat().ctime, 0.00001)
    assert documents[1]['updated'].timestamp() \
        == pytest.approx(tmpdir.join(*path).stat().mtime, 0.00001)
    assert documents[1]['content'] == 'text'

    if path[0] == '2017':
        assert documents[1]['published'] == datetime.date(2017, 9, 17)

        if path[3].endswith('.md'):
            assert isinstance(documents[1], content.Post)


@pytest.mark.parametrize('data, cls', [
    (u'text', str),
    (b'\xf1', bytes),
])
def test_document_content_types(testapp, tmpdir, data, cls):
    """Source processor has to properly read documents' content."""

    localpath = tmpdir.ensure('cv.md')

    if isinstance(data, bytes):
        localpath.write_binary(data)
    else:
        localpath.write_text(data, encoding='utf-8')

    documents = source.process(testapp, [], path=tmpdir.strpath)
    assert documents[0]['content'] == data
    assert isinstance(documents[0]['content'], cls)


def test_documents(testapp, tmpdir):
    """Source processor has to ignore non-matched documents."""

    structure = sorted([
        (['2017', '09', '20', 'the-force.md'], content.Post),
        (['2017', '09', '20', 'yoda.jpg'], content.Document),
        (['about', 'index.md'], content.Page),
        (['about', 'me.png'], content.Document),
        (['cv.pdf'], content.Document),
    ])

    for path, _ in structure:
        tmpdir.ensure(*path)
    tmpdir.ensure('_config.yml')

    documents = source.process(
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
    documents = sorted(documents, key=lambda document: document['source'])

    for document, (path, cls) in zip(documents, structure):
        assert document['source'] == os.path.join(*path)
        assert document['destination'] == os.path.join(*path)
        assert document['created'].timestamp() \
            == pytest.approx(tmpdir.join(*path).stat().ctime, 0.00001)
        assert document['updated'].timestamp() \
            == pytest.approx(tmpdir.join(*path).stat().mtime, 0.00001)
        assert isinstance(document, cls)
