"""Pipeline processor test suite."""


import os

import pytest

from holocron import app, content
from holocron.ext.processors import pipeline


def _get_document(cls=content.Document, **kwargs):
    document = cls(app.Holocron({}))
    document.update(kwargs)
    return document


@pytest.fixture(scope='function')
def testapp():
    def spam(app, documents, **options):
        for document in documents:
            document['spam'] = options.get('text', 42)
        return documents

    def eggs(app, documents, **options):
        for document in documents:
            document['content'] += ' #friedeggs'
        return documents

    def rice(app, documents, **options):
        document = content.Document(app)
        document['content'] = 'rice'
        documents.append(document)
        return documents

    instance = app.Holocron({})
    instance.add_processor('spam', spam)
    instance.add_processor('eggs', eggs)
    instance.add_processor('rice', rice)

    return instance


def test_document(testapp):
    """Pipeline processor has to work!"""

    documents = pipeline.process(
        testapp,
        [
            _get_document(content='the Force', author='skywalker'),
        ],
        processors=[
            {'name': 'spam'},
            {'name': 'eggs'},
            {'name': 'rice'},
        ])

    assert len(documents) == 2

    assert documents[0]['content'] == 'the Force #friedeggs'
    assert documents[0]['author'] == 'skywalker'
    assert documents[0]['spam'] == 42

    assert documents[1]['content'] == 'rice'


def test_document_processor_with_option(testapp):
    """Pipeline processor has to pass down processors options."""

    documents = pipeline.process(
        testapp,
        [
            _get_document(content='the Force', author='skywalker'),
        ],
        processors=[
            {'name': 'spam', 'text': 1},
        ])

    assert len(documents) == 1

    assert documents[0]['content'] == 'the Force'
    assert documents[0]['author'] == 'skywalker'
    assert documents[0]['spam'] == 1


def test_document_no_processors(testapp):
    """Pipeline processor with no processors has to passed by."""

    documents = pipeline.process(
        testapp,
        [
            _get_document(content='the Force', author='skywalker'),
        ])

    assert len(documents) == 1

    assert documents[0]['content'] == 'the Force'
    assert documents[0]['author'] == 'skywalker'


def test_documents(testapp):
    """Metadata processor has to ignore non-targeted documents."""

    documents = pipeline.process(
        testapp,
        [
            _get_document(
                content='the way of the Force #1',
                source=os.path.join('posts', '1.md')),
            _get_document(
                content='the way of the Force #2',
                source=os.path.join('pages', '2.md')),
            _get_document(
                content='the way of the Force #3',
                source=os.path.join('posts', '3.md')),
            _get_document(
                content='the way of the Force #4',
                source=os.path.join('pages', '4.md')),
        ],
        processors=[
            {'name': 'spam'},
            {'name': 'eggs'},
            {'name': 'rice'},
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'^posts.*$',
            },
        ])

    assert len(documents) == 5

    assert documents[0]['content'] == 'the way of the Force #2'
    assert documents[0]['source'] == os.path.join('pages', '2.md')
    assert 'spam' not in documents[0]

    assert documents[1]['content'] == 'the way of the Force #4'
    assert documents[1]['source'] == os.path.join('pages', '4.md')
    assert 'spam' not in documents[1]

    assert documents[2]['content'] == 'the way of the Force #1 #friedeggs'
    assert documents[2]['source'] == os.path.join('posts', '1.md')
    assert documents[2]['spam'] == 42

    assert documents[3]['content'] == 'the way of the Force #3 #friedeggs'
    assert documents[3]['source'] == os.path.join('posts', '3.md')
    assert documents[3]['spam'] == 42

    assert documents[4]['content'] == 'rice'


def test_parameters_jsonref(testapp):
    testapp.conf.update({'extra': {'procs': [{'name': 'rice'}]}})

    documents = pipeline.process(
        testapp,
        [],
        processors={'$ref': ':application:#/extra/procs'})

    assert len(documents) == 1
    assert documents[0]['content'] == 'rice'


@pytest.mark.parametrize('options, error', [
    ({'when': [42]}, 'when: unsupported value'),
    ({'processors': 42}, "processors: 42 should be instance of 'list'"),
])
def test_parameters_schema(testapp, options, error):
    with pytest.raises(ValueError, match=error):
        pipeline.process(testapp, [], **options)


@pytest.mark.parametrize('option_name, option_value, error', [
    ('when', [42], 'when: unsupported value'),
    ('processors', 42, "processors: 42 should be instance of 'list'"),
])
def test_parameters_jsonref_schema(testapp, option_name, option_value, error):
    testapp.conf.update({'test': {option_name: option_value}})

    with pytest.raises(ValueError, match=error):
        pipeline.process(
            testapp,
            [],
            **{option_name: {'$ref': ':application:#/test/%s' % option_name}})
