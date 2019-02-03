"""Jinja2 processor test suite."""

import os
import textwrap
import unittest.mock

import pytest
import bs4

from holocron import core
from holocron.processors import jinja2


@pytest.fixture(scope="function")
def testapp():
    return core.Application({"url": "https://yoda.ua"})


def test_item(testapp):
    """Jinja2 processor has to work!"""

    stream = jinja2.process(
        testapp,
        [core.Item({"title": "History of the Force", "content": "the Force"})],
    )

    item = next(stream)
    assert item == core.Item(
        {"title": "History of the Force", "content": unittest.mock.ANY}
    )

    soup = bs4.BeautifulSoup(item["content"], "html.parser")
    assert soup.meta["charset"] == "UTF-8"
    assert soup.article.header.h1.string == "History of the Force"
    assert list(soup.article.stripped_strings)[1] == "the Force"

    # Since we don't know in which order statics are discovered, we sort them
    # so we can avoid possible flakes.
    static = sorted(stream, key=lambda d: d["source"])
    assert static[0]["source"] == os.path.join("static", "logo.svg")
    assert static[0]["destination"] == static[0]["source"]
    assert static[1]["source"] == os.path.join("static", "pygments.css")
    assert static[1]["destination"] == static[1]["source"]
    assert static[2]["source"] == os.path.join("static", "style.css")
    assert static[2]["destination"] == static[2]["source"]
    assert len(static) == 3


def test_item_template(testapp, tmpdir):
    """Jinja2 processor has to respect item suggested template."""

    tmpdir.ensure("theme_a", "templates", "holiday.j2").write_text(
        textwrap.dedent(
            """\
            template: my super template
            rendered: {{ document.title }}
        """
        ),
        encoding="UTF-8",
    )

    stream = jinja2.process(
        testapp,
        [
            core.Item(
                {
                    "title": "History of the Force",
                    "content": "the Force",
                    "template": "holiday.j2",
                }
            )
        ],
        themes=[tmpdir.join("theme_a").strpath],
    )

    assert next(stream) == core.Item(
        {
            "title": "History of the Force",
            "template": "holiday.j2",
            "content": textwrap.dedent(
                """\
                template: my super template
                rendered: History of the Force"""
            ),
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize("amount", [0, 1, 2, 5, 10])
def test_item_many(testapp, tmpdir, amount):
    """Jinja2 processor has to work with stream."""

    stream = jinja2.process(
        testapp,
        [
            core.Item(
                {
                    "title": "History of the Force",
                    "content": "the Force #%d" % i,
                }
            )
            for i in range(amount)
        ],
    )

    for i in range(amount):
        item = next(stream)
        assert item == core.Item(
            {"title": "History of the Force", "content": unittest.mock.ANY}
        )

        soup = bs4.BeautifulSoup(item["content"], "html.parser")
        assert soup.meta["charset"] == "UTF-8"
        assert soup.article.header.h1.string == "History of the Force"
        assert list(soup.article.stripped_strings)[1] == "the Force #%d" % i

    # Since we don't know in which order statics are discovered, we sort them
    # so we can avoid possible flakes.
    static = sorted(stream, key=lambda d: d["source"])
    assert static[0]["source"] == os.path.join("static", "logo.svg")
    assert static[0]["destination"] == static[0]["source"]
    assert static[1]["source"] == os.path.join("static", "pygments.css")
    assert static[1]["destination"] == static[1]["source"]
    assert static[2]["source"] == os.path.join("static", "style.css")
    assert static[2]["destination"] == static[2]["source"]
    assert len(static) == 3


def test_param_themes(testapp, tmpdir):
    """Jinja2 processor has to respect themes parameter."""

    tmpdir.ensure("theme_a", "templates", "item.j2").write_text(
        textwrap.dedent(
            """\
            template: my super template
            rendered: {{ document.title }}
        """
        ),
        encoding="UTF-8",
    )

    tmpdir.ensure("theme_a", "static", "style.css").write_text(
        "article { margin: 0 }", encoding="UTF-8"
    )

    stream = jinja2.process(
        testapp,
        [core.Item({"title": "History of the Force", "content": "the Force"})],
        themes=[tmpdir.join("theme_a").strpath],
    )

    assert next(stream) == core.Item(
        {
            "title": "History of the Force",
            "content": textwrap.dedent(
                """\
                template: my super template
                rendered: History of the Force"""
            ),
        }
    )

    assert next(stream) == core.WebSiteItem(
        {
            "content": "article { margin: 0 }",
            "source": os.path.join("static", "style.css"),
            "destination": os.path.join("static", "style.css"),
            "created": unittest.mock.ANY,
            "updated": unittest.mock.ANY,
            "baseurl": testapp.metadata["url"],
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


def test_param_themes_two_themes(testapp, tmpdir):
    """Jinja2 processor has to respect themes parameter."""

    tmpdir.ensure("theme_a", "templates", "page.j2").write_text(
        textwrap.dedent(
            """\
            template: my super template from theme_a
            rendered: {{ document.title }}
        """
        ),
        encoding="UTF-8",
    )

    tmpdir.ensure("theme_b", "templates", "page.j2").write_text(
        textwrap.dedent(
            """\
            template: my super template from theme_b
            rendered: {{ document.title }}
        """
        ),
        encoding="UTF-8",
    )

    tmpdir.ensure("theme_b", "templates", "holiday.j2").write_text(
        textwrap.dedent(
            """\
            template: my holiday template from theme_b
            rendered: {{ document.title }}
        """
        ),
        encoding="UTF-8",
    )

    stream = jinja2.process(
        testapp,
        [
            core.Item(
                {
                    "title": "History of the Force",
                    "content": "the Force",
                    "template": "page.j2",
                }
            ),
            core.Item(
                {
                    "title": "History of the Force",
                    "content": "the Force",
                    "template": "holiday.j2",
                }
            ),
        ],
        themes=[
            tmpdir.join("theme_a").strpath,
            tmpdir.join("theme_b").strpath,
        ],
    )

    assert next(stream) == core.Item(
        {
            "title": "History of the Force",
            "template": "page.j2",
            "content": textwrap.dedent(
                """\
                template: my super template from theme_a
                rendered: History of the Force"""
            ),
        }
    )

    assert next(stream) == core.Item(
        {
            "title": "History of the Force",
            "template": "holiday.j2",
            "content": textwrap.dedent(
                """\
                template: my holiday template from theme_b
                rendered: History of the Force"""
            ),
        }
    )

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize(
    "params, error",
    [
        ({"template": 42}, "template: 42 should be instance of 'str'"),
        ({"context": 42}, "context: must be a dict"),
        ({"themes": {"foo": 1}}, "themes: unsupported value"),
    ],
)
def test_param_bad_value(testapp, params, error):
    """Commit processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(jinja2.process(testapp, [], **params))
