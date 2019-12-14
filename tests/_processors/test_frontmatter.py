"""Frontmatter processor test suite."""

import collections.abc
import textwrap

import pytest
import yaml

import holocron
from holocron._processors import frontmatter


@pytest.fixture(scope="function")
def testapp():
    return holocron.Application()


@pytest.mark.parametrize(
    ["frontsnippet"],
    [
        pytest.param(
            """\
            author: Yoda
            master: true
            labels: [force, motto]
            """,
            id="yaml",
        ),
        pytest.param(
            """\
            {
                "author": "Yoda",
                "master": true,
                "labels": ["force", "motto"]
            }
            """,
            id="json",
        ),
        pytest.param(
            """\
            author = "Yoda"
            master = true
            labels = ["force", "motto"]
            """,
            id="toml",
        ),
    ],
)
def test_item(testapp, frontsnippet):
    """Frontmatter has to be processed and removed from the content."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        ---
                        %s
                        ---

                        May the Force be with you!
                        """
                    )
                    % textwrap.dedent(frontsnippet)
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "May the Force be with you!\n",
                "author": "Yoda",
                "master": True,
                "labels": ["force", "motto"],
            }
        )
    ]


def test_item_without_frontmatter(testapp):
    """Item without frontmatter has to be ignored."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ...

                        May the Force be with you!
                    """
                    )
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": textwrap.dedent(
                    """\
                    ---
                    author: Yoda
                    master: true
                    labels: [force, motto]
                    ...

                    May the Force be with you!
                """
                )
            }
        )
    ]


def test_item_with_frontmatter_in_text(testapp):
    """Only frontmatter at the beginning has to be processed."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        I am a Jedi, like my father before me.

                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """
                    )
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": textwrap.dedent(
                    """\
                    I am a Jedi, like my father before me.

                    ---
                    author: Yoda
                    master: true
                    labels: [force, motto]
                    ---

                    May the Force be with you!
                """
                )
            }
        )
    ]


def test_item_with_frontmatter_leading_whitespaces(testapp):
    """Leading whitespaces before frontmatter has to be ignored."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\


                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """
                    )
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "May the Force be with you!\n",
                "author": "Yoda",
                "master": True,
                "labels": ["force", "motto"],
            }
        )
    ]


def test_item_yaml_invalid(testapp):
    """Frontmatter processor has to fail in case of invalid YAML."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        ---
                        author: Yoda
                         the best jedi ever:
                        ---

                        May the Force be with you!
                    """
                    )
                }
            )
        ],
        format="yaml",
    )

    assert isinstance(stream, collections.abc.Iterable)

    with pytest.raises(yaml.YAMLError):
        next(stream)


def test_item_yaml_exploit(testapp):
    """Frontmatter processor has to be protected from YAML attacks."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        ---
                        author: !!python/object/apply:subprocess.check_output
                          args: [ cat ~/.ssh/id_rsa ]
                          kwds: { shell: true }
                        ---

                        May the Force be with you!
                    """
                    )
                }
            )
        ],
        format="yaml",
    )

    assert isinstance(stream, collections.abc.Iterable)

    with pytest.raises(yaml.YAMLError):
        next(stream)


@pytest.mark.parametrize(
    ["amount"],
    [
        pytest.param(0),
        pytest.param(1),
        pytest.param(2),
        pytest.param(5),
        pytest.param(10),
    ],
)
def test_item_many(testapp, amount):
    """Frontmatter processor has to work with stream."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        ---
                        master: %d
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """
                        % i
                    )
                }
            )
            for i in range(amount)
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "master": i,
                "labels": ["force", "motto"],
                "content": "May the Force be with you!\n",
            }
        )
        for i in range(amount)
    ]


@pytest.mark.parametrize(
    ["delimiter"], [pytest.param("+++"), pytest.param("***")]
)
def test_args_delimiter(testapp, delimiter):
    """Frontmatter processor has to respect 'delimiter' argument."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        f"""\
                        {delimiter}
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        {delimiter}

                        May the Force be with you!
                        """
                    )
                }
            )
        ],
        delimiter=delimiter,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "May the Force be with you!\n",
                "author": "Yoda",
                "master": True,
                "labels": ["force", "motto"],
            }
        )
    ]


@pytest.mark.parametrize(
    ["overwrite"], [pytest.param(False), pytest.param(True)]
)
def test_args_overwrite(testapp, overwrite):
    """Frontmatter processor has to respect 'overwrite' argument."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "author": "Obi-Wan Kenobi",
                    "content": textwrap.dedent(
                        """\
                        ---
                        author: Yoda
                        master: true
                        labels: [force, motto]
                        ---

                        May the Force be with you!
                    """
                    ),
                }
            )
        ],
        overwrite=overwrite,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "May the Force be with you!\n",
                "author": "Yoda" if overwrite else "Obi-Wan Kenobi",
                "master": True,
                "labels": ["force", "motto"],
            }
        )
    ]


@pytest.mark.parametrize(
    ["frontsnippet", "format", "exception"],
    [
        pytest.param(
            """\
            author: Yoda
            master: true
            labels: [force, motto]
            """,
            "yaml",
            None,
            id="yaml",
        ),
        pytest.param(
            """\
            {
                "author": "Yoda",
                "master": true,
                "labels": ["force", "motto"]
            }
            """,
            "json",
            None,
            id="json",
        ),
        pytest.param(
            """\
            author = "Yoda"
            master = true
            labels = ["force", "motto"]
            """,
            "toml",
            None,
            id="toml",
        ),
        pytest.param(
            """\
            author = "Yoda"
            master = true
            labels = ["force", "motto"]
            """,
            "yaml",
            ValueError(
                "Frontmatter must be a mapping (i.e. key-value pairs), "
                "not arrays."
            ),
            id="toml-yaml",
        ),
        pytest.param(
            """\
            {
                "author": "Yoda",
                "master": true,
                "labels": ["force", "motto"]
            }
            """,
            "toml",
            ValueError(
                "Key name found without value. Reached end of line. "
                "(line 1 column 2 char 1)"
            ),
            id="json-toml",
        ),
    ],
)
def test_args_format(testapp, frontsnippet, format, exception):
    """Frontmatter has to respect 'format' argument."""

    stream = frontmatter.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": textwrap.dedent(
                        """\
                        ---
                        %s
                        ---

                        May the Force be with you!
                        """
                    )
                    % textwrap.dedent(frontsnippet)
                }
            )
        ],
        format=format,
    )

    assert isinstance(stream, collections.abc.Iterable)

    if exception:
        with pytest.raises(exception.__class__) as excinfo:
            next(stream)

        assert str(excinfo.value) == str(exception)

    else:
        assert list(stream) == [
            holocron.Item(
                {
                    "content": "May the Force be with you!\n",
                    "author": "Yoda",
                    "master": True,
                    "labels": ["force", "motto"],
                }
            )
        ]


@pytest.mark.parametrize(
    ["args", "error"],
    [
        pytest.param(
            {"delimiter": 42},
            "delimiter: 42 is not of type 'string'",
            id="delimiter",
        ),
        pytest.param(
            {"overwrite": "true"},
            "overwrite: 'true' is not of type 'boolean'",
            id="overwrite",
        ),
    ],
)
def test_args_bad_value(testapp, args, error):
    """Frontmatter processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(frontmatter.process(testapp, [], **args))
    assert str(excinfo.value) == error
