"""Sitemap processor test suite."""

import collections.abc
import datetime
import gzip
import itertools
import pathlib
import unittest.mock

import pytest
import xmltodict

import holocron
from holocron._processors import sitemap


class _pytest_xmlasdict:
    """Assert that a given XML has the same semantic meaning."""

    def __init__(self, expected, ungzip=False, **kwargs):
        self._expected = expected
        self._ungzip = ungzip
        self._kwargs = kwargs

    def __eq__(self, actual):
        if self._ungzip:
            actual = gzip.decompress(actual)
        actual = xmltodict.parse(actual, "UTF-8", **self._kwargs)
        return self._expected == actual

    def __repr__(self):
        return self._expected


@pytest.fixture(scope="function")
def testapp():
    return holocron.Application({"url": "https://yoda.ua"})


@pytest.mark.parametrize(
    ["filename", "escaped"],
    [
        pytest.param("s.html", "s.html"),
        pytest.param("ы.html", "%D1%8B.html"),
        pytest.param("a&b.html", "a%26b.html"),
        pytest.param("a<b.html", "a%3Cb.html"),
        pytest.param("a>b.html", "a%3Eb.html"),
        pytest.param('a"b.html', "a%22b.html"),
        pytest.param("a'b.html", "a%27b.html"),
    ],
)
def test_item(testapp, filename, escaped):
    """Sitemap processor has to work!"""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            holocron.WebSiteItem(
                {
                    "destination": pathlib.Path(filename),
                    "updated": timepoint,
                    "baseurl": testapp.metadata["url"],
                }
            )
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.WebSiteItem(
            {
                "destination": pathlib.Path(filename),
                "updated": timepoint,
                "baseurl": testapp.metadata["url"],
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("sitemap://sitemap.xml"),
                "destination": pathlib.Path("sitemap.xml"),
                "content": _pytest_xmlasdict(
                    {
                        "urlset": {
                            "@xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
                            "url": {
                                "loc": "https://yoda.ua/" + escaped,
                                "lastmod": "1970-01-01T00:00:00+00:00",
                            },
                        }
                    }
                ),
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["amount"],
    [pytest.param(1), pytest.param(2), pytest.param(5), pytest.param(10)],
)
def test_item_many(testapp, amount):
    """Sitemap processor has to work with stream."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            holocron.WebSiteItem(
                {
                    "destination": pathlib.Path(str(i)),
                    "updated": timepoint,
                    "baseurl": testapp.metadata["url"],
                }
            )
            for i in range(amount)
        ],
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == list(
        itertools.chain(
            [
                holocron.WebSiteItem(
                    {
                        "destination": pathlib.Path(str(i)),
                        "updated": timepoint,
                        "baseurl": testapp.metadata["url"],
                    }
                )
                for i in range(amount)
            ],
            [
                holocron.WebSiteItem(
                    {
                        "source": pathlib.Path("sitemap://sitemap.xml"),
                        "destination": pathlib.Path("sitemap.xml"),
                        "content": _pytest_xmlasdict(
                            {
                                "urlset": {
                                    "@xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
                                    "url": [
                                        {
                                            "loc": "https://yoda.ua/%d" % i,
                                            "lastmod": "1970-01-01T00:00:00+00:00",
                                        }
                                        for i in range(amount)
                                    ],
                                }
                            },
                            force_list=["url"],
                        ),
                        "baseurl": testapp.metadata["url"],
                    }
                )
            ],
        )
    )


def test_item_many_zero(testapp):
    """Sitemap processor has to work with stream of zero items."""

    stream = sitemap.process(testapp, [])

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("sitemap://sitemap.xml"),
                "destination": pathlib.Path("sitemap.xml"),
                "content": _pytest_xmlasdict(
                    {
                        "urlset": {
                            "@xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"
                        }
                    }
                ),
                "baseurl": testapp.metadata["url"],
            }
        )
    ]


def test_args_gzip(testapp):
    """Sitemap processor has to respect gzip argument."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            holocron.WebSiteItem(
                {
                    "destination": pathlib.Path("1.html"),
                    "updated": timepoint,
                    "baseurl": testapp.metadata["url"],
                }
            )
        ],
        gzip=True,
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.WebSiteItem(
            {
                "destination": pathlib.Path("1.html"),
                "updated": timepoint,
                "baseurl": testapp.metadata["url"],
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("sitemap://sitemap.xml.gz"),
                "destination": pathlib.Path("sitemap.xml.gz"),
                "content": _pytest_xmlasdict(
                    {
                        "urlset": {
                            "@xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
                            "url": {
                                "loc": "https://yoda.ua/1.html",
                                "lastmod": "1970-01-01T00:00:00+00:00",
                            },
                        }
                    },
                    ungzip=True,
                ),
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["save_as"],
    [
        pytest.param(pathlib.Path("posts", "skywalker.luke"), id="deep"),
        pytest.param(pathlib.Path("yoda.jedi"), id="flat"),
    ],
)
def test_args_save_as(testapp, save_as):
    """Sitemap processor has to respect save_as argument."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            holocron.WebSiteItem(
                {
                    "destination": pathlib.Path("posts", "1.html"),
                    "updated": timepoint,
                    "baseurl": testapp.metadata["url"],
                }
            )
        ],
        save_as=str(save_as),
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.WebSiteItem(
            {
                "destination": pathlib.Path("posts", "1.html"),
                "updated": timepoint,
                "baseurl": testapp.metadata["url"],
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("sitemap://", save_as),
                "destination": pathlib.Path(save_as),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["document_path", "sitemap_path"],
    [
        pytest.param(pathlib.Path("1.html"), pathlib.Path("b", "sitemap.xml")),
        pytest.param(
            pathlib.Path("a", "1.html"), pathlib.Path("b", "sitemap.xml")
        ),
        pytest.param(
            pathlib.Path("a", "1.html"), pathlib.Path("a", "c", "sitemap.xml")
        ),
        pytest.param(
            pathlib.Path("ab", "1.html"), pathlib.Path("a", "sitemap.xml")
        ),
    ],
)
def test_args_save_as_unsupported(testapp, document_path, sitemap_path):
    """Sitemap process has to check enlisted URLs for compatibility."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            holocron.WebSiteItem(
                {
                    "destination": document_path,
                    "updated": timepoint,
                    "baseurl": testapp.metadata["url"],
                }
            )
        ],
        save_as=str(sitemap_path),
    )

    assert isinstance(stream, collections.abc.Iterable)

    with pytest.raises(ValueError) as excinfo:
        next(stream)

    excinfo.match(
        "The location of a Sitemap file determines the set of URLs "
        "that can be included in that Sitemap. A Sitemap file located "
        "at .* can include any URLs starting with .* but can not "
        "include .*."
    )


@pytest.mark.parametrize(
    ["pretty", "lines"], [pytest.param(False, 1), pytest.param(True, 7)]
)
def test_args_pretty(testapp, pretty, lines):
    """Sitemap processor has to respect pretty argument."""

    timepoint = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
    stream = sitemap.process(
        testapp,
        [
            holocron.WebSiteItem(
                {
                    "destination": pathlib.Path("1.html"),
                    "updated": timepoint,
                    "baseurl": testapp.metadata["url"],
                }
            )
        ],
        pretty=pretty,
    )

    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.WebSiteItem(
            {
                "destination": pathlib.Path("1.html"),
                "updated": timepoint,
                "baseurl": testapp.metadata["url"],
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("sitemap://sitemap.xml"),
                "destination": pathlib.Path("sitemap.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]
    assert len(items[-1]["content"].splitlines()) == lines


@pytest.mark.parametrize(
    ["args", "error"],
    [
        pytest.param(
            {"gzip": "true"},
            "gzip: 'true' is not of type 'boolean'",
            id="gzip-str",
        ),
        pytest.param(
            {"save_as": 42},
            "save_as: 42 is not of type 'string'",
            id="save_as-int",
        ),
        pytest.param(
            {"pretty": "true"},
            "pretty: 'true' is not of type 'boolean'",
            id="pretty-str",
        ),
    ],
)
def test_args_bad_value(testapp, args, error):
    """Sitemap processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(sitemap.process(testapp, [], **args))
    assert str(excinfo.value) == error
