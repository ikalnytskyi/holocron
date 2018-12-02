"""Tags processor test suite."""

import os
import datetime

import pytest
import bs4

from holocron import app, content
from holocron.ext.processors import tags


def _get_document(**kwargs):
    document = content.Document(app.Holocron({}))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})
    return instance


def test_document(testapp):
    """Tags processor has to work!"""

    documents = tags.process(
        testapp,
        [
            _get_document(
                title='the way of the Force',
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 4),
                tags=['kenobi', 'skywalker']),
        ])

    assert documents[0]['title'] == 'the way of the Force'
    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['published'] == datetime.date(2017, 10, 4)

    # - / -

    assert documents[-2]['source'] == 'virtual://tags/kenobi'
    assert documents[-2]['destination'] == 'tags/kenobi.html'

    soup = bs4.BeautifulSoup(documents[-2]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-04'
    assert entries[1].a.attrs['href'] == '/posts/1.html'

    # - / -

    assert documents[-1]['source'] == 'virtual://tags/skywalker'
    assert documents[-1]['destination'] == 'tags/skywalker.html'

    soup = bs4.BeautifulSoup(documents[-1]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-04'
    assert entries[1].a.attrs['href'] == '/posts/1.html'


def test_document_options(testapp):
    """Tags processor has to respect custom options."""

    documents = tags.process(
        testapp,
        [
            _get_document(
                title='the way of the Force',
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 4),
                tags=['kenobi', 'skywalker']),
        ],
        output='mytags/{tag}/index.html')

    assert documents[0]['title'] == 'the way of the Force'
    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['published'] == datetime.date(2017, 10, 4)

    # - / -

    assert documents[-2]['source'] == 'virtual://tags/kenobi'
    assert documents[-2]['destination'] == 'mytags/kenobi/index.html'

    soup = bs4.BeautifulSoup(documents[-2]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-04'
    assert entries[1].a.attrs['href'] == '/posts/1.html'

    # - / -

    assert documents[-1]['source'] == 'virtual://tags/skywalker'
    assert documents[-1]['destination'] == 'mytags/skywalker/index.html'

    soup = bs4.BeautifulSoup(documents[-1]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-04'
    assert entries[1].a.attrs['href'] == '/posts/1.html'


def test_documents_cross_tags(testapp):
    """Tags processor has to group tags"""

    documents = tags.process(
        testapp,
        [
            _get_document(
                title='the way of the Force #1',
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 1),
                tags=['kenobi', 'skywalker']),
            _get_document(
                title='the way of the Force #2',
                destination=os.path.join('posts', '2.html'),
                published=datetime.date(2017, 10, 2),
                tags=['yoda', 'skywalker']),
        ])

    assert documents[0]['title'] == 'the way of the Force #1'
    assert documents[0]['destination'] == os.path.join('posts', '1.html')
    assert documents[0]['published'] == datetime.date(2017, 10, 1)

    assert documents[1]['title'] == 'the way of the Force #2'
    assert documents[1]['destination'] == os.path.join('posts', '2.html')
    assert documents[1]['published'] == datetime.date(2017, 10, 2)

    # - / -

    assert documents[-3]['source'] == 'virtual://tags/kenobi'
    assert documents[-3]['destination'] == 'tags/kenobi.html'

    soup = bs4.BeautifulSoup(documents[-3]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-01'
    assert entries[1].a.attrs['href'] == '/posts/1.html'

    # - / -

    assert documents[-2]['source'] == 'virtual://tags/skywalker'
    assert documents[-2]['destination'] == 'tags/skywalker.html'

    soup = bs4.BeautifulSoup(documents[-2]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-02'
    assert entries[1].a.attrs['href'] == '/posts/2.html'
    assert entries[2].time.attrs['datetime'] == '2017-10-01'
    assert entries[2].a.attrs['href'] == '/posts/1.html'

    # - / -

    assert documents[-1]['source'] == 'virtual://tags/yoda'
    assert documents[-1]['destination'] == 'tags/yoda.html'

    soup = bs4.BeautifulSoup(documents[-1]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-02'
    assert entries[1].a.attrs['href'] == '/posts/2.html'


def test_documents(testapp):
    """Tags processor has to ignore non-relevant documents."""

    documents = tags.process(
        testapp,
        [
            _get_document(
                title='the way of the Force #1',
                source=os.path.join('posts', '1.md'),
                destination=os.path.join('posts', '1.html'),
                published=datetime.date(2017, 10, 1),
                tags=['kenobi']),
            _get_document(
                title='the way of the Force #2',
                source=os.path.join('pages', '2.md'),
                destination=os.path.join('pages', '2.html'),
                published=datetime.date(2017, 10, 2),
                tags=['kenobi']),
            _get_document(
                title='the way of the Force #3',
                source=os.path.join('posts', '3.md'),
                destination=os.path.join('posts', '3.html'),
                published=datetime.date(2017, 10, 3),
                tags=['kenobi']),
            _get_document(
                title='the way of the Force #4',
                source=os.path.join('pages', '4.md'),
                destination=os.path.join('pages', '4.html'),
                published=datetime.date(2017, 10, 4),
                tags=['kenobi']),
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

    # - / -

    assert documents[-1]['source'] == 'virtual://tags/kenobi'
    assert documents[-1]['destination'] == 'tags/kenobi.html'

    soup = bs4.BeautifulSoup(documents[-1]['content'], 'html.parser')
    entries = soup.find(class_='index').find_all(recursive=False)

    assert 'year' in entries[0].attrs['class']
    assert 'index-entry' in entries[1].attrs['class']

    assert entries[0].string == '2017'
    assert entries[1].time.attrs['datetime'] == '2017-10-03'
    assert entries[1].a.attrs['href'] == '/posts/3.html'

    assert entries[2].time.attrs['datetime'] == '2017-10-01'
    assert entries[2].a.attrs['href'] == '/posts/1.html'


@pytest.mark.parametrize('options, error', [
    ({'when': 42}, 'when: unsupported value'),
    ({'template': 42}, "template: 42 should be instance of 'str'"),
    ({'output': 42}, "output: 42 should be instance of 'str'"),
])
def test_parameters_schema(testapp, options, error):
    with pytest.raises(ValueError, match=error):
        tags.process(testapp, [], **options)
