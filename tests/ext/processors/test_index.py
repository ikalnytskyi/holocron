"""Index processor test suite."""

import pytest

from holocron import app
from holocron.ext.processors import index


@pytest.fixture(scope='function')
def testapp():
    instance = app.Holocron({})
    return instance


def test_document(testapp):
    """Index processor has to work!"""

    stream = index.process(
        testapp,
        [
            {
                'title': 'the way of the Force',
                'content': 'Obi-Wan',
            },
        ])

    assert next(stream) == \
        {
            'title': 'the way of the Force',
            'content': 'Obi-Wan',
        }

    assert next(stream) == \
        {
            'source': 'virtual://index',
            'destination': 'index.html',
            'template': 'index.j2',
            'documents': [
                {
                    'title': 'the way of the Force',
                    'content': 'Obi-Wan'
                }],
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_template(testapp):
    """Index processor has respect template parameter."""

    stream = index.process(
        testapp,
        [
            {
                'title': 'the way of the Force',
                'content': 'Obi-Wan',
            },
        ],
        template='foobar.txt')

    assert next(stream) == \
        {
            'title': 'the way of the Force',
            'content': 'Obi-Wan',
        }

    assert next(stream) == \
        {
            'source': 'virtual://index',
            'destination': 'index.html',
            'template': 'foobar.txt',
            'documents': [
                {
                    'title': 'the way of the Force',
                    'content': 'Obi-Wan'
                }],
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_when(testapp):
    """Index processor has to ignore non-relevant documents."""

    stream = index.process(
        testapp,
        [
            {
                'title': 'the way of the Force #1',
                'source': '1.md',
            },
            {
                'title': 'the way of the Force #2',
                'source': '2.rst',
            },
            {
                'title': 'the way of the Force #3',
                'source': '3.md',
            },
            {
                'title': 'the way of the Force #4',
                'source': '4.rst',
            },
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^.*\.md$',
            },
        ])

    for i, document in zip(range(1, 5), stream):
        assert document == \
            {
                'title': 'the way of the Force #%d' % i,
                'source': '%d.%s' % (i, 'md' if i % 2 else 'rst'),
            }

    assert next(stream) == \
        {
            'source': 'virtual://index',
            'destination': 'index.html',
            'template': 'index.j2',
            'documents': [
                {
                    'title': 'the way of the Force #1',
                    'source': '1.md',
                },
                {
                    'title': 'the way of the Force #3',
                    'source': '3.md',
                }],
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('params, error', [
    ({'when': 42}, 'when: unsupported value'),
    ({'template': 42}, "template: 42 should be instance of 'str'"),
])
def test_param_bad_value(testapp, params, error):
    """Index processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(index.process(testapp, [], **params))
