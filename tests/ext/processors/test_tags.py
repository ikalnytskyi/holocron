"""Tags processor test suite."""

import pytest

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


@pytest.fixture(scope='function')
def run_processor():
    streams = []

    def run(*args, **kwargs):
        streams.append(tags.process(*args, **kwargs))
        return streams[-1]

    yield run

    for stream in streams:
        with pytest.raises(StopIteration):
            next(stream)


def test_document(testapp, run_processor):
    """Tags processor has to work!"""

    stream = run_processor(
        testapp,
        [
            {
                'title': 'the way of the Force',
                'tags': ['kenobi', 'skywalker'],
            },
        ])

    document = \
        {
            'title': 'the way of the Force',
            'tags': [
                {'name': 'kenobi', 'url': '/tags/kenobi.html'},
                {'name': 'skywalker', 'url': '/tags/skywalker.html'},
            ],
        }

    assert next(stream) == document
    assert next(stream) == \
        {
            'source': 'virtual://tags/kenobi',
            'destination': 'tags/kenobi.html',
            'template': 'index.j2',
            'documents': [document],
        }
    assert next(stream) == \
        {
            'source': 'virtual://tags/skywalker',
            'destination': 'tags/skywalker.html',
            'template': 'index.j2',
            'documents': [document],
        }


def test_documents_cross_tags(testapp, run_processor):
    """Tags processor has to group tags"""

    stream = run_processor(
        testapp,
        [
            {
                'title': 'the way of the Force #1',
                'tags': ['kenobi', 'skywalker'],
            },
            {
                'title': 'the way of the Force #2',
                'tags': ['yoda', 'skywalker'],
            },
        ])

    document_a = \
        {
            'title': 'the way of the Force #1',
            'tags': [
                {'name': 'kenobi', 'url': '/tags/kenobi.html'},
                {'name': 'skywalker', 'url': '/tags/skywalker.html'},
            ],
        }

    document_b = \
        {
            'title': 'the way of the Force #2',
            'tags': [
                {'name': 'yoda', 'url': '/tags/yoda.html'},
                {'name': 'skywalker', 'url': '/tags/skywalker.html'},
            ],
        }

    assert next(stream) == document_a
    assert next(stream) == document_b
    assert next(stream) == \
        {
            'source': 'virtual://tags/kenobi',
            'destination': 'tags/kenobi.html',
            'template': 'index.j2',
            'documents': [document_a],
        }
    assert next(stream) == \
        {
            'source': 'virtual://tags/skywalker',
            'destination': 'tags/skywalker.html',
            'template': 'index.j2',
            'documents': [document_a, document_b],
        }
    assert next(stream) == \
        {
            'source': 'virtual://tags/yoda',
            'destination': 'tags/yoda.html',
            'template': 'index.j2',
            'documents': [document_b],
        }


def test_param_template(testapp, run_processor):
    """Tags processor has to respect template parameter."""

    stream = run_processor(
        testapp,
        [
            {
                'title': 'the way of the Force',
                'tags': ['kenobi'],
            },
        ],
        template='foobar.txt')

    document = \
        {
            'title': 'the way of the Force',
            'tags': [{'name': 'kenobi', 'url': '/tags/kenobi.html'}],
        }

    assert next(stream) == document
    assert next(stream) == \
        {
            'source': 'virtual://tags/kenobi',
            'destination': 'tags/kenobi.html',
            'template': 'foobar.txt',
            'documents': [document],
        }


def test_param_output(testapp, run_processor):
    """Tags processor has to respect output parameter."""

    stream = run_processor(
        testapp,
        [
            {
                'title': 'the way of the Force',
                'tags': ['kenobi', 'skywalker'],
            },
        ],
        output='mytags/{tag}/index.html')

    document = \
        {
            'title': 'the way of the Force',
            'tags': [
                {'name': 'kenobi', 'url': '/mytags/kenobi/index.html'},
                {'name': 'skywalker', 'url': '/mytags/skywalker/index.html'},
            ],
        }

    assert next(stream) == document
    assert next(stream) == \
        {
            'source': 'virtual://tags/kenobi',
            'destination': 'mytags/kenobi/index.html',
            'template': 'index.j2',
            'documents': [document],
        }
    assert next(stream) == \
        {
            'source': 'virtual://tags/skywalker',
            'destination': 'mytags/skywalker/index.html',
            'template': 'index.j2',
            'documents': [document],
        }


def test_param_when(testapp, run_processor):
    """Tags processor has to ignore non-relevant documents."""

    stream = tags.process(
        testapp,
        [
            {
                'title': 'the way of the Force #1',
                'source': '1.md',
                'tags': ['kenobi'],
            },
            {
                'title': 'the way of the Force #2',
                'source': '2.rst',
                'tags': ['kenobi'],
            },
            {
                'title': 'the way of the Force #3',
                'source': '3.md',
                'tags': ['kenobi'],
            },
            {
                'title': 'the way of the Force #4',
                'source': '4.rst',
                'tags': ['kenobi'],
            },
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^.*\.md$',
            },
        ])

    document_a = next(stream)
    document_b = next(stream)
    document_c = next(stream)
    document_d = next(stream)

    assert document_a == \
        {
            'title': 'the way of the Force #1',
            'source': '1.md',
            'tags': [{'name': 'kenobi', 'url': '/tags/kenobi.html'}],
        }

    assert document_b == \
        {
            'title': 'the way of the Force #2',
            'source': '2.rst',
            'tags': ['kenobi'],
        }

    assert document_c == \
        {
            'title': 'the way of the Force #3',
            'source': '3.md',
            'tags': [{'name': 'kenobi', 'url': '/tags/kenobi.html'}],
        }

    assert document_d == \
        {
            'title': 'the way of the Force #4',
            'source': '4.rst',
            'tags': ['kenobi'],
        }

    assert next(stream) == \
        {
            'source': 'virtual://tags/kenobi',
            'destination': 'tags/kenobi.html',
            'template': 'index.j2',
            'documents': [document_a, document_c],
        }


@pytest.mark.parametrize('params, error', [
    ({'when': 42}, 'when: unsupported value'),
    ({'template': 42}, "template: 42 should be instance of 'str'"),
    ({'output': 42}, "output: 42 should be instance of 'str'"),
])
def test_param_bad_value(testapp, params, error):
    """Tags processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        tags.process(testapp, [], **params)
