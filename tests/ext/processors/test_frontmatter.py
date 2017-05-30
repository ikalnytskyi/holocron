"""Frontmatter processor test suite."""

import textwrap

import mock
import pytest
import yaml

from holocron import app, content
from holocron.ext.processors import frontmatter


# We are forced to prepare documents this way as long as they smart.
# Fortunately, it's a temporary measure as we are going towards plain
# documents represented as dictionaries.
@mock.patch('holocron.content.os.path.getmtime', return_value=1420121400)
@mock.patch('holocron.content.os.path.getctime', return_value=662739000)
@mock.patch('holocron.content.os.getcwd', return_value='cwd')
def _get_document(content, _, __, ___, cls=content.Page, path='memory://'):
    return cls(path, app.Holocron({}), content.encode('utf-8'))


@pytest.fixture(scope='function')
def testapp():
    return mock.Mock()


def test_document(testapp):
    """YAML front matter has to be processed and cut out."""

    documents = frontmatter.process(
        testapp,
        [
            _get_document(textwrap.dedent('''\
                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ---

                May the Force be with you!
            '''))
        ])

    assert documents[0].author == 'Yoda'
    assert documents[0].master
    assert documents[0].labels == ['force', 'motto']
    assert documents[0].content == 'May the Force be with you!\n'


def test_document_without_frontmatter(testapp):
    """Document without front matter has to be ignored."""

    documents = frontmatter.process(
        testapp,
        [
            _get_document(textwrap.dedent('''\
                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ...

                May the Force be with you!
            '''))
        ])

    assert documents[0].content == textwrap.dedent('''\
        ---
        author: Yoda
        master: true
        labels: [force, motto]
        ...

        May the Force be with you!
    ''')


def text_document_with_frontmatter_in_text(testapp):
    """Only front matter on the beginning has to be processed."""

    documents = frontmatter.process(
        testapp,
        [
            _get_document(textwrap.dedent('''\
                I am a Jedi, like my father before me.

                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ---

                May the Force be with you!
            '''))
        ])

    assert documents[0].content == textwrap.dedent('''\
        I am a Jedi, like my father before me.

        ---
        author: Yoda
        master: true
        labels: [force, motto]
        ...

        May the Force be with you!
    ''')


def test_document_custom_delimiter(testapp):
    """YAML front matter has to be extracted even with custom delimiter."""

    documents = frontmatter.process(
        testapp,
        [
            _get_document(textwrap.dedent('''\
                +++
                author: Yoda
                master: true
                labels: [force, motto]
                +++

                May the Force be with you!
            '''))
        ],
        delimiter='+++')

    assert documents[0].author == 'Yoda'
    assert documents[0].master
    assert documents[0].labels == ['force', 'motto']
    assert documents[0].content == 'May the Force be with you!\n'


def test_document_overwrite_false(testapp):
    """Frontmatter processor has to respect 'overwrite' option."""

    documents = frontmatter.process(
        testapp,
        [
            _get_document(textwrap.dedent('''\
                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ---

                May the Force be with you!
            '''))
        ],
        overwrite=False)

    assert documents[0].author == 'Obi-Wan Kenobi'
    assert documents[0].master
    assert documents[0].labels == ['force', 'motto']
    assert documents[0].content == 'May the Force be with you!\n'


def test_document_invalid_yaml(testapp):
    """Frontmatter processor has to fail in case of invalid front matter."""

    with pytest.raises(yaml.YAMLError):
        frontmatter.process(
            testapp,
            [
                _get_document(textwrap.dedent('''\
                    ---
                    author: Yoda
                     the best jedi ever:
                    ---

                    May the Force be with you!
                '''))
            ])


def test_document_with_exploit(testapp):
    """Frontmatter processor has to be protected from YAML attacks."""

    with pytest.raises(yaml.YAMLError):
        frontmatter.process(
            testapp,
            [
                _get_document(textwrap.dedent('''\
                    ---
                    author: !!python/object/apply:subprocess.check_output
                      args: [ cat ~/.ssh/id_rsa ]
                      kwds: { shell: true }
                    ---

                    May the Force be with you!
                '''))
            ])


def test_documents(testapp):
    """Frontmatter processor has to ignore non-targeted documents."""

    content = textwrap.dedent('''\
        ---
        master: true
        labels: [force, motto]
        ---

        May the Force be with you!
    ''')

    documents = frontmatter.process(
        testapp,
        [
            _get_document(content, path='0.txt'),
            _get_document(content, path='1.md'),
            _get_document(content, path='2'),
            _get_document(content, path='3.markdown'),
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(markdown|mdown|mkd|mdwn|md)$',
            },
        ])

    assert not hasattr(documents[0], 'master')
    assert not hasattr(documents[0], 'labels')
    assert documents[0].content == content

    assert documents[1].master
    assert documents[1].labels == ['force', 'motto']
    assert documents[1].content == 'May the Force be with you!\n'

    assert not hasattr(documents[2], 'master')
    assert not hasattr(documents[2], 'labels')
    assert documents[2].content == content

    assert documents[3].master
    assert documents[3].labels == ['force', 'motto']
    assert documents[3].content == 'May the Force be with you!\n'