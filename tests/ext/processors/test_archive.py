"""Archive processor test suite."""

import os

import pytest

from holocron import app
from holocron.ext.processors import archive


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron()


def test_item(testapp):
    """Archive processor has to work!"""

    stream = archive.process(
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
            'source': 'archive://index.html',
            'destination': 'index.html',
            'template': 'archive.j2',
            'items': [
                {
                    'title': 'the way of the Force',
                    'content': 'Obi-Wan'
                },
            ],
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('amount', [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """archive processor has to work with stream."""

    stream = archive.process(
        testapp,
        [
            {
                'title': 'the way of the Force #%d' % i,
            }
            for i in range(amount)
        ])

    for i in range(amount):
        assert next(stream) == \
            {
                'title': 'the way of the Force #%d' % i,
            }

    assert next(stream) == \
        {
            'source': 'archive://index.html',
            'destination': 'index.html',
            'template': 'archive.j2',
            'items': [
                {
                    'title': 'the way of the Force #%d' % i,
                }
                for i in range(amount)
            ],
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_template(testapp):
    """archive processor has respect template parameter."""

    stream = archive.process(
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
            'source': 'archive://index.html',
            'destination': 'index.html',
            'template': 'foobar.txt',
            'items': [
                {
                    'title': 'the way of the Force',
                    'content': 'Obi-Wan'
                },
            ],
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('save_as', [
    os.path.join('posts', 'skywalker.luke'),
    os.path.join('yoda.jedi'),
])
def test_param_save_as(testapp, save_as):
    """archive processor has to respect save_as parameter."""

    stream = archive.process(
        testapp,
        [
            {
                'title': 'the way of the Force',
                'content': 'Obi-Wan',
            },
        ],
        save_as=save_as)

    assert next(stream) == \
        {
            'title': 'the way of the Force',
            'content': 'Obi-Wan',
        }

    assert next(stream) == \
        {
            'source': 'archive://%s' % save_as,
            'destination': save_as,
            'template': 'archive.j2',
            'items': [
                {
                    'title': 'the way of the Force',
                    'content': 'Obi-Wan'
                },
            ],
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('params, error', [
    ({'save_as': 42}, "save_as: 42 should be instance of 'str'"),
    ({'template': 42}, "template: 42 should be instance of 'str'"),
])
def test_param_bad_value(testapp, params, error):
    """archive processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(archive.process(testapp, [], **params))
