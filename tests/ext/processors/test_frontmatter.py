"""Frontmatter processor test suite."""

import textwrap

import pytest
import yaml

from holocron import app
from holocron.ext.processors import frontmatter


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron()


def test_document(testapp):
    """YAML front matter has to be processed and cut out."""

    stream = frontmatter.process(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    ---
                    author: Yoda
                    master: true
                    labels: [force, motto]
                    ---

                    May the Force be with you!
                '''),
            },
        ])

    assert next(stream) == \
        {
            'content': 'May the Force be with you!\n',
            'author': 'Yoda',
            'master': True,
            'labels': ['force', 'motto'],
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_document_without_frontmatter(testapp):
    """Document without front matter has to be ignored."""

    stream = frontmatter.process(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    ---
                    author: Yoda
                    master: true
                    labels: [force, motto]
                    ...

                    May the Force be with you!
                '''),
            },
        ])

    assert next(stream) == \
        {
            'content': textwrap.dedent('''\
                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ...

                May the Force be with you!
            '''),
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_document_with_frontmatter_in_text(testapp):
    """Only front matter on the beginning has to be processed."""

    stream = frontmatter.process(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    I am a Jedi, like my father before me.

                    ---
                    author: Yoda
                    master: true
                    labels: [force, motto]
                    ---

                    May the Force be with you!
                '''),
            },
        ])

    assert next(stream) == \
        {
            'content': textwrap.dedent('''\
                I am a Jedi, like my father before me.

                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ---

                May the Force be with you!
            '''),
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_document_invalid_yaml(testapp):
    """Frontmatter processor has to fail in case of invalid front matter."""

    stream = frontmatter.process(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    ---
                    author: Yoda
                     the best jedi ever:
                    ---

                    May the Force be with you!
                '''),
            },
        ])

    with pytest.raises(yaml.YAMLError):
        next(stream)


def test_document_with_exploit(testapp):
    """Frontmatter processor has to be protected from YAML attacks."""

    stream = frontmatter.process(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    ---
                    author: !!python/object/apply:subprocess.check_output
                      args: [ cat ~/.ssh/id_rsa ]
                      kwds: { shell: true }
                    ---

                    May the Force be with you!
                '''),
            },
        ])

    with pytest.raises(yaml.YAMLError):
        next(stream)


@pytest.mark.parametrize('delimiter', ['+++', '***'])
def test_param_delimiter(testapp, delimiter):
    """Frontmatter processor has to respect delimiter parameter."""

    stream = frontmatter.process(
        testapp,
        [
            {
                'content': textwrap.dedent('''\
                    %s
                    author: Yoda
                    master: true
                    labels: [force, motto]
                    %s

                    May the Force be with you!
                ''' % (delimiter, delimiter)),
            },
        ],
        delimiter=delimiter)

    assert next(stream) == \
        {
            'content': 'May the Force be with you!\n',
            'author': 'Yoda',
            'master': True,
            'labels': ['force', 'motto'],
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('overwrite', [False, True])
def test_param_overwrite(testapp, overwrite):
    """Frontmatter processor has to respect overwrite parameter."""

    stream = frontmatter.process(
        testapp,
        [
            {
                'author': 'Obi-Wan Kenobi',
                'content': textwrap.dedent('''\
                    ---
                    author: Yoda
                    master: true
                    labels: [force, motto]
                    ---

                    May the Force be with you!
                '''),
            },
        ],
        overwrite=overwrite)

    assert next(stream) == \
        {
            'content': 'May the Force be with you!\n',
            'author': 'Yoda' if overwrite else 'Obi-Wan Kenobi',
            'master': True,
            'labels': ['force', 'motto'],
        }

    with pytest.raises(StopIteration):
        next(stream)


def test_param_when(testapp):
    """Frontmatter processor has to ignore non-targeted documents."""

    content = textwrap.dedent('''\
        ---
        master: true
        labels: [force, motto]
        ---

        May the Force be with you!
    ''')

    stream = frontmatter.process(
        testapp,
        [
            {'content': content, 'source': '0.txt'},
            {'content': content, 'source': '1.md'},
            {'content': content, 'source': '2'},
            {'content': content, 'source': '3.markdown'},
        ],
        when=[
            {
                'operator': 'match',
                'attribute': 'source',
                'pattern': r'.*\.(markdown|mdown|mkd|mdwn|md)$',
            },
        ])

    assert next(stream) == \
        {
            'content': content,
            'source': '0.txt',
        }
    assert next(stream) == \
        {
            'content': 'May the Force be with you!\n',
            'source': '1.md',
            'master': True,
            'labels': ['force', 'motto'],
        }
    assert next(stream) == \
        {
            'content': content,
            'source': '2',
        }
    assert next(stream) == \
        {
            'content': 'May the Force be with you!\n',
            'source': '3.markdown',
            'master': True,
            'labels': ['force', 'motto'],
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('params, error', [
    ({'when': [42]}, 'when: unsupported value'),
    ({'delimiter': 42}, "delimiter: 42 should be instance of 'str'"),
    ({'overwrite': 'true'}, "overwrite: 'true' should be instance of 'bool'"),
])
def test_param_bad_value(testapp, params, error):
    """Frontmatter processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(frontmatter.process(testapp, [], **params))
