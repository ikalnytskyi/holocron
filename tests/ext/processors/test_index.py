"""Index processor test suite."""

import os
import datetime

import pytest
import bs4

from holocron import app, content
from holocron.ext.processors import index


def _get_document(cls=content.Page, **kwargs):
    document = cls(app.Holocron({}))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})
    return instance


def test_document(testapp):
    """Index processor has to work!"""

    documents = index.process(
        testapp,
        [
            _get_document(
                title='the way of the Force',
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 4)),
        ],
        encoding='cp1251')

    assert documents[0]['title'] == 'the way of the Force'
    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['published'] == datetime.date(2017, 10, 4)

    assert documents[-1]['source'] == 'virtual://index'
    assert documents[-1]['destination'] == 'index.html'
    assert documents[-1]['encoding'] == 'cp1251'

    soup = bs4.BeautifulSoup(documents[-1]['content'], 'html.parser')
    assert soup.original_encoding == 'cp1251'

    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-04'
    assert entries[1].a.attrs['href'] == '/posts/1.html'


def test_documents_multiple_years(testapp):
    """Index processor has to group documents by year."""

    documents = index.process(
        testapp,
        [
            _get_document(
                title='the way of the Force #1',
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2016, 10, 1)),
            _get_document(
                title='the way of the Force #2',
                source=os.path.join('posts', '2.md'),
                destination=os.path.join('posts', '2.html'),
                published=datetime.date(2017, 10, 2)),
            _get_document(
                title='the way of the Force #3',
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html'),
                published=datetime.date(2016, 10, 3)),
            _get_document(
                title='the way of the Force #4',
                source=os.path.join('posts', '4.md'),
                destination=os.path.join('posts', '4.html'),
                published=datetime.date(2017, 10, 4)),
        ])

    assert documents[-1]['source'] == 'virtual://index'
    assert documents[-1]['destination'] == 'index.html'

    soup = bs4.BeautifulSoup(documents[-1]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-04'
    assert entries[1].a.attrs['href'] == '/posts/4.html'
    assert entries[2].time.attrs['datetime'] == '2017-10-02'
    assert entries[2].a.attrs['href'] == '/posts/2.html'

    assert entries[3].string == '2016'
    assert entries[4].time.attrs['datetime'] == '2016-10-03'
    assert entries[4].a.attrs['href'] == '/posts/3.html'
    assert entries[5].time.attrs['datetime'] == '2016-10-01'
    assert entries[5].a.attrs['href'] == '/posts/1.html'


def test_documents(testapp):
    """Index processor has to ignore non-relevant documents."""

    documents = index.process(
        testapp,
        [
            _get_document(
                title='the way of the Force #1',
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 1)),
            _get_document(
                title='the way of the Force #2',
                source=os.path.join('pages', '2.md'),
                destination=os.path.join('pages', '2.html'),
                published=datetime.date(2017, 10, 2)),
            _get_document(
                title='the way of the Force #3',
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html'),
                published=datetime.date(2017, 10, 3)),
            _get_document(
                title='the way of the Force #4',
                source=os.path.join('pages', '4.md'),
                destination=os.path.join('pages', '4.html'),
                published=datetime.date(2017, 10, 4)),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    for i, document in enumerate(documents[:-1]):
        assert document['source'].endswith('%d.md' % (i + 1))
        assert document['title'] == 'the way of the Force #%d' % (i + 1)
        assert document['published'] == datetime.date(2017, 10, i + 1)

    assert documents[-1]['source'] == 'virtual://index'
    assert documents[-1]['destination'] == 'index.html'

    soup = bs4.BeautifulSoup(documents[-1]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-03'
    assert entries[1].a.attrs['href'] == '/posts/3.html'

    assert entries[2].time.attrs['datetime'] == '2017-10-01'
    assert entries[2].a.attrs['href'] == '/posts/1.html'
