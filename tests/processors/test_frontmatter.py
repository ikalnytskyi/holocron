"""Frontmatter processor test suite."""

import textwrap

import pytest
import yaml

from holocron import core
from holocron.processors import frontmatter


@pytest.fixture(scope="function")
def testapp():
    return core.Application()


def test_item(testapp):
    """YAML front matter has to be processed and cut out."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """),
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": "May the Force be with you!\n",
            "author": "Yoda",
            "master": True,
            "labels": ["force", "motto"],
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_without_frontmatter(testapp):
    """item without front matter has to be ignored."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ...

                        May the Force be with you!
                    """),
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": textwrap.dedent("""\
                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ...

                May the Force be with you!
            """),
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_with_frontmatter_in_text(testapp):
    """Only front matter on the beginning has to be processed."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        I am a Jedi, like my father before me.

                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """),
                }),
        ])

    assert next(stream) == core.Item(
        {
            "content": textwrap.dedent("""\
                I am a Jedi, like my father before me.

                ---
                author: Yoda
                master: true
                labels: [force, motto]
                ---

                May the Force be with you!
            """),
        })

    with pytest.raises(StopIteration):
        next(stream)


def test_item_invalid_yaml(testapp):
    """Frontmatter processor has to fail in case of invalid front matter."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        ---
                        author: Yoda
                         the best jedi ever:
                        ---

                        May the Force be with you!
                    """),
                }),
        ])

    with pytest.raises(yaml.YAMLError):
        next(stream)


def test_item_with_exploit(testapp):
    """Frontmatter processor has to be protected from YAML attacks."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        ---
                        author: !!python/object/apply:subprocess.check_output
                          args: [ cat ~/.ssh/id_rsa ]
                          kwds: { shell: true }
                        ---

                        May the Force be with you!
                    """),
                }),
        ])

    with pytest.raises(yaml.YAMLError):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, amount):
    """Frontmatter processor has to work with stream."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        ---
                        master: %d
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """ % i)
                })
            for i in range(amount)
        ])

    for i in range(amount):
        assert next(stream) == core.Item(
            {
                "master": i,
                "labels": ["force", "motto"],
                "content": "May the Force be with you!\n",
            })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("delimiter", ["+++", "***"])
def test_param_delimiter(testapp, delimiter):
    """Frontmatter processor has to respect delimiter parameter."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "content": textwrap.dedent("""\
                        %s
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        %s

                        May the Force be with you!
                    """ % (delimiter, delimiter)),
                }),
        ],
        delimiter=delimiter)

    assert next(stream) == core.Item(
        {
            "content": "May the Force be with you!\n",
            "author": "Yoda",
            "master": True,
            "labels": ["force", "motto"],
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("overwrite", [False, True])
def test_param_overwrite(testapp, overwrite):
    """Frontmatter processor has to respect overwrite parameter."""

    stream = frontmatter.process(
        testapp,
        [
            core.Item(
                {
                    "author": "Obi-Wan Kenobi",
                    "content": textwrap.dedent("""\
                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """),
                }),
        ],
        overwrite=overwrite)

    assert next(stream) == core.Item(
        {
            "content": "May the Force be with you!\n",
            "author": "Yoda" if overwrite else "Obi-Wan Kenobi",
            "master": True,
            "labels": ["force", "motto"],
        })

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("params, error", [
    ({"delimiter": 42}, "delimiter: 42 is not of type 'string'"),
    ({"overwrite": "true"}, "overwrite: 'true' is not of type 'boolean'"),
])
def test_param_bad_value(testapp, params, error):
    """Frontmatter processor has to validate input parameters."""

    with pytest.raises(ValueError) as excinfo:
        next(frontmatter.process(testapp, [], **params))
    assert str(excinfo.value) == error
