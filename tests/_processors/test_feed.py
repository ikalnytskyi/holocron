"""Feed processor test suite."""

import collections.abc
import datetime
import importlib.metadata
import itertools
import pathlib
import unittest.mock

import pytest
import untangle

import holocron
from holocron._processors import feed

_HOLOCRON_VERSION = importlib.metadata.version("holocron")


@pytest.fixture(scope="function")
def testapp():
    return holocron.Application({"url": "https://yoda.ua"})


def test_item_atom(testapp):
    """Feed (atom) processor has to work with minimum amount of metadata!"""

    stream = feed.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the way of the Force",
                    "published": datetime.date(2017, 9, 25),
                }
            )
        ],
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": "Once upon a time",
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.Item(
            {
                "content": "the way of the Force",
                "published": datetime.date(2017, 9, 25),
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://feed.xml"),
                "destination": pathlib.Path("feed.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]

    parsed = untangle.parse(items[-1]["content"].decode("UTF-8"))
    assert set(dir(parsed.feed)) == {
        "id",
        "title",
        "subtitle",
        "link",
        "generator",
        "updated",
        "entry",
    }
    assert parsed.feed["xmlns"] == "http://www.w3.org/2005/Atom"
    assert parsed.feed.id == "kenobi-way"
    assert parsed.feed.title == "Kenobi's Way"
    assert parsed.feed.subtitle == "Labours of Obi-Wan"
    assert parsed.feed.link["href"] == testapp.metadata["url"]
    assert parsed.feed.generator["uri"] == "https://github.com/ikalnytskyi/holocron"
    assert parsed.feed.generator["version"] == _HOLOCRON_VERSION
    assert parsed.feed.generator == f"Holocron/v{_HOLOCRON_VERSION}"

    assert set(dir(parsed.feed.entry)) == {"id", "title", "content", "updated"}
    assert parsed.feed.entry.id == "day-one"
    assert parsed.feed.entry.title == "Day 1"
    assert parsed.feed.entry.content == "Once upon a time"
    assert parsed.feed.entry.content["type"] == "html"


def test_item_atom_feed_metadata(testapp):
    """Feed (atom) processor has to work with full metadata set!"""

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [holocron.Item({"content": "the way of the Force", "published": published})],
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "subtitle": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
            "author": {"name": "Obi-Wan", "email": "obi1@kenobi.com"},
            "contributor": {"name": "Yoda", "email": "yoda@jedi.com"},
            "icon": "path/to/icon",
            "logo": "path/to/logo",
            "rights": "(c) Obi-Wan",
            "language": "uk",
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": "Once upon a time",
            "author": {"name": "Obi-Wan", "email": "obi1@kenobi.com"},
            "link": {"href": "path/to/webpage", "rel": "alternate"},
            "summary": "about the Force",
            "contributor": {"name": "Dooku", "email": "dooku@sith.com"},
            "published": {"$ref": "item://#/published"},
            "rights": "(c) Obi-Wan and the Jedi Order",
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.Item({"content": "the way of the Force", "published": published}),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://feed.xml"),
                "destination": pathlib.Path("feed.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]

    parsed = untangle.parse(items[-1]["content"].decode("UTF-8"))
    assert set(dir(parsed.feed)) == {
        "id",
        "title",
        "subtitle",
        "link",
        "generator",
        "updated",
        "author",
        "contributor",
        "icon",
        "logo",
        "rights",
        "entry",
    }
    assert parsed.feed["xmlns"] == "http://www.w3.org/2005/Atom"
    assert parsed.feed["xml:lang"] == "uk"
    assert parsed.feed.id == "kenobi-way"
    assert parsed.feed.title == "Kenobi's Way"
    assert parsed.feed.subtitle == "Labours of Obi-Wan"
    assert parsed.feed.link["href"] == testapp.metadata["url"]
    assert parsed.feed.generator["uri"] == "https://github.com/ikalnytskyi/holocron"
    assert parsed.feed.generator["version"] == _HOLOCRON_VERSION
    assert parsed.feed.generator == f"Holocron/v{_HOLOCRON_VERSION}"
    assert parsed.feed.author.name == "Obi-Wan"
    assert parsed.feed.author.email == "obi1@kenobi.com"
    assert parsed.feed.contributor.name == "Yoda"
    assert parsed.feed.contributor.email == "yoda@jedi.com"
    assert parsed.feed.icon == "path/to/icon"
    assert parsed.feed.logo == "path/to/logo"
    assert parsed.feed.rights == "(c) Obi-Wan"

    assert set(dir(parsed.feed.entry)) == {
        "id",
        "title",
        "content",
        "updated",
        "author",
        "link",
        "summary",
        "contributor",
        "published",
        "rights",
    }
    assert parsed.feed.entry.id == "day-one"
    assert parsed.feed.entry.title == "Day 1"
    assert parsed.feed.entry.content == "Once upon a time"
    assert parsed.feed.entry.content["type"] == "html"
    assert parsed.feed.entry.author.name == "Obi-Wan"
    assert parsed.feed.entry.author.email == "obi1@kenobi.com"
    assert parsed.feed.entry.link["href"] == "path/to/webpage"
    assert parsed.feed.entry.link["rel"] == "alternate"
    assert parsed.feed.entry.summary == "about the Force"
    assert parsed.feed.entry.contributor.name == "Dooku"
    assert parsed.feed.entry.contributor.email == "dooku@sith.com"
    assert parsed.feed.entry.published == published.isoformat()
    assert parsed.feed.entry.rights == "(c) Obi-Wan and the Jedi Order"


def test_item_rss(testapp):
    """Feed (rss) processor has to work with minimum amount of metadata!"""

    stream = feed.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the way of the Force",
                    "published": datetime.date(2017, 9, 25),
                }
            )
        ],
        syndication_format="rss",
        feed={
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={"title": "Day 1", "content": "Once upon a time"},
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.Item(
            {
                "content": "the way of the Force",
                "published": datetime.date(2017, 9, 25),
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://feed.xml"),
                "destination": pathlib.Path("feed.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]

    parsed = untangle.parse(items[-1]["content"].decode("UTF-8"))
    assert set(dir(parsed.rss.channel)) == {
        "title",
        "description",
        "link",
        "generator",
        "lastBuildDate",
        "docs",
        "item",
    }
    assert parsed.rss["xmlns:atom"] == "http://www.w3.org/2005/Atom"
    assert parsed.rss["xmlns:content"] == ("http://purl.org/rss/1.0/modules/content/")
    assert parsed.rss["version"] == "2.0"
    assert parsed.rss.channel.title == "Kenobi's Way"
    assert parsed.rss.channel.description == "Labours of Obi-Wan"
    assert parsed.rss.channel.link == testapp.metadata["url"]
    assert parsed.rss.channel.generator == f"Holocron/v{_HOLOCRON_VERSION}"

    assert set(dir(parsed.rss.channel.item)) == {"title", "description"}
    assert parsed.rss.channel.item.title == "Day 1"
    assert parsed.rss.channel.item.description == "Once upon a time"


def test_item_rss_feed_metadata(testapp):
    """Feed (rss) processor has to work with full metadata set!"""

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [holocron.Item({"content": "the way of the Force", "published": published})],
        syndication_format="rss",
        feed={
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
            "category": {"term": "Jedi"},
            "image": {"url": "path/to/image", "width": "100"},
            "copyright": "(c) Obi-Wan",
            "language": "uk",
            "managingEditor": "yoda@jedi.com",
            "rating": "some PICS rating",
            "skipHours": [7, 8, 9],
            "skipDays": ["Friday"],
            "ttl": 42,
            "webMaster": "luke@skywalker.com",
            "itunes_author": "dooku@sith.com",
            "itunes_block": False,
            "itunes_category": {"cat": "Arts", "sub": "Design"},
            "itunes_image": "path/to/image.png",
            "itunes_explicit": "clean",
            "itunes_complete": "no",
            "itunes_owner": {"name": "obi-wan", "email": "ben@kenobi.com"},
            "itunes_subtitle": "Labours of Obi-Wan Podcast",
            "itunes_summary": "Well, you know.. gibberish",
            "itunes_new_feed_url": "path/to/new/url",
        },
        item={
            "guid": "kenobi-way",
            "title": "Day 1",
            "content": "Once upon a time",
            "author": {"name": "Obi-Wan", "email": "obi1@kenobi.com"},
            "link": {"href": "path/to/webpage", "rel": "alternate"},
            "description": "about the Force",
            "enclosure": {"url": "x.mp3", "length": "42", "type": "audio/mp3"},
            "published": {"$ref": "item://#/published"},
            "ttl": "13",
            "itunes_author": "vader@sith.com",
            "itunes_block": False,
            "itunes_image": "path/to/episode/image.png",
            "itunes_duration": "00:32:13",
            "itunes_explicit": "yes",
            "itunes_is_closed_captioned": True,
            "itunes_order": 42,
            "itunes_subtitle": "cherry",
            "itunes_summary": "berry",
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.Item({"content": "the way of the Force", "published": published}),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://feed.xml"),
                "destination": pathlib.Path("feed.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]

    parsed = untangle.parse(items[-1]["content"].decode("UTF-8"))
    assert set(dir(parsed.rss.channel)) == {
        "title",
        "description",
        "link",
        "generator",
        "lastBuildDate",
        "docs",
        "category",
        "copyright",
        "image",
        "language",
        "managingEditor",
        "rating",
        "skipDays",
        "skipHours",
        "ttl",
        "webMaster",
        "item",
        "itunes_author",
        "itunes_block",
        "itunes_category",
        "itunes_image",
        "itunes_explicit",
        "itunes_complete",
        "itunes_owner",
        "itunes_subtitle",
        "itunes_summary",
        "itunes_new_feed_url",
    }
    assert parsed.rss["xmlns:atom"] == "http://www.w3.org/2005/Atom"
    assert parsed.rss["xmlns:itunes"] == ("http://www.itunes.com/dtds/podcast-1.0.dtd")
    assert parsed.rss["xmlns:content"] == ("http://purl.org/rss/1.0/modules/content/")
    assert parsed.rss["version"] == "2.0"
    assert parsed.rss.channel.title == "Kenobi's Way"
    assert parsed.rss.channel.description == "Labours of Obi-Wan"
    assert parsed.rss.channel.link == testapp.metadata["url"]
    assert parsed.rss.channel.generator == f"Holocron/v{_HOLOCRON_VERSION}"
    assert parsed.rss.channel.category == "Jedi"
    assert parsed.rss.channel.image.url == "path/to/image"
    assert parsed.rss.channel.image.title == "Kenobi's Way"
    assert parsed.rss.channel.image.link == testapp.metadata["url"]
    assert parsed.rss.channel.image.width == "100"
    assert parsed.rss.channel.copyright == "(c) Obi-Wan"
    assert parsed.rss.channel.language == "uk"
    assert parsed.rss.channel.managingEditor == "yoda@jedi.com"
    assert parsed.rss.channel.rating == "some PICS rating"
    assert {x.cdata for x in parsed.rss.channel.skipHours.children} == {
        "7",
        "8",
        "9",
    }
    assert parsed.rss.channel.skipDays.day == "Friday"
    assert parsed.rss.channel.ttl == "42"
    assert parsed.rss.channel.webMaster == "luke@skywalker.com"
    assert parsed.rss.channel.itunes_author == "dooku@sith.com"
    assert parsed.rss.channel.itunes_block == "no"
    assert parsed.rss.channel.itunes_category["text"] == "Arts"
    assert parsed.rss.channel.itunes_category.itunes_category["text"] == "Design"
    assert parsed.rss.channel.itunes_image["href"] == "path/to/image.png"
    assert parsed.rss.channel.itunes_explicit == "clean"
    assert parsed.rss.channel.itunes_complete == "no"
    assert parsed.rss.channel.itunes_owner.itunes_name == "obi-wan"
    assert parsed.rss.channel.itunes_owner.itunes_email == "ben@kenobi.com"
    assert parsed.rss.channel.itunes_subtitle == "Labours of Obi-Wan Podcast"
    assert parsed.rss.channel.itunes_summary == "Well, you know.. gibberish"
    assert parsed.rss.channel.itunes_new_feed_url == "path/to/new/url"

    assert set(dir(parsed.rss.channel.item)) == {
        "title",
        "description",
        "author",
        "content_encoded",
        "enclosure",
        "link",
        "pubDate",
        "itunes_author",
        "itunes_block",
        "itunes_image",
        "itunes_duration",
        "itunes_explicit",
        "itunes_isClosedCaptioned",
        "itunes_order",
        "itunes_subtitle",
        "itunes_summary",
    }
    assert parsed.rss.channel.item.title == "Day 1"
    assert parsed.rss.channel.item.description == "about the Force"
    assert parsed.rss.channel.item.author == "obi1@kenobi.com (Obi-Wan)"
    assert parsed.rss.channel.item.content_encoded == "Once upon a time"
    assert parsed.rss.channel.item.enclosure["url"] == "x.mp3"
    assert parsed.rss.channel.item.enclosure["length"] == "42"
    assert parsed.rss.channel.item.enclosure["type"] == "audio/mp3"
    assert parsed.rss.channel.item.link == "path/to/webpage"
    assert parsed.rss.channel.item.pubDate == "Mon, 25 Sep 2017 00:00:00 +0000"

    assert parsed.rss.channel.item.itunes_author == "vader@sith.com"
    assert parsed.rss.channel.item.itunes_block == "no"
    assert parsed.rss.channel.item.itunes_image["href"] == "path/to/episode/image.png"
    assert parsed.rss.channel.item.itunes_duration == "00:32:13"
    assert parsed.rss.channel.item.itunes_explicit == "yes"
    assert parsed.rss.channel.item.itunes_isClosedCaptioned == "yes"
    assert parsed.rss.channel.item.itunes_order == "42"
    assert parsed.rss.channel.item.itunes_subtitle == "cherry"
    assert parsed.rss.channel.item.itunes_summary == "berry"


@pytest.mark.parametrize(
    ["syndication_format"], [pytest.param("atom"), pytest.param("rss")]
)
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
def test_item_many(testapp, syndication_format, amount):
    """Feed processor has to work with stream."""

    stream = feed.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the key is %d" % i,
                    "published": datetime.date(2017, 9, 25),
                }
            )
            for i in range(amount)
        ],
        syndication_format=syndication_format,
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": "Once upon a time",
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == list(
        itertools.chain(
            [
                holocron.Item(
                    {
                        "content": "the key is %d" % i,
                        "published": datetime.date(2017, 9, 25),
                    }
                )
                for i in range(amount)
            ],
            [
                holocron.WebSiteItem(
                    {
                        "source": pathlib.Path("feed://feed.xml"),
                        "destination": pathlib.Path("feed.xml"),
                        "content": unittest.mock.ANY,
                        "baseurl": testapp.metadata["url"],
                    }
                )
            ],
        )
    )


@pytest.mark.parametrize(
    ["syndication_format"], [pytest.param("atom"), pytest.param("rss")]
)
@pytest.mark.parametrize(["encoding"], [pytest.param("CP1251"), pytest.param("UTF-16")])
def test_args_encoding(testapp, syndication_format, encoding):
    """Feed processor has to respect encoding argument."""

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [holocron.Item({"content": "the way of the Force", "published": published})],
        syndication_format=syndication_format,
        encoding=encoding,
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": "Once upon a time",
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.Item({"content": "the way of the Force", "published": published}),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://feed.xml"),
                "destination": pathlib.Path("feed.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]
    assert untangle.parse(items[-1]["content"].decode(encoding))


@pytest.mark.parametrize(
    ["syndication_format"], [pytest.param("atom"), pytest.param("rss")]
)
@pytest.mark.parametrize(["encoding"], [pytest.param("CP1251"), pytest.param("UTF-16")])
def test_args_encoding_fallback(testapp, syndication_format, encoding):
    """Feed processor has to respect encoding argument (fallback)."""

    testapp.metadata.update({"encoding": encoding})

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [holocron.Item({"content": "the way of the Force", "published": published})],
        syndication_format=syndication_format,
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": "Once upon a time",
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.Item({"content": "the way of the Force", "published": published}),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://feed.xml"),
                "destination": pathlib.Path("feed.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]
    assert untangle.parse(items[-1]["content"].decode(encoding))


@pytest.mark.parametrize(
    ["syndication_format"], [pytest.param("atom"), pytest.param("rss")]
)
@pytest.mark.parametrize(
    ["save_as"],
    [
        pytest.param(pathlib.Path("foo.xml")),
        pytest.param(pathlib.Path("foo", "bar.xml")),
    ],
)
def test_args_save_as(testapp, syndication_format, save_as):
    """Feed processor has to respect save_as argument."""

    stream = feed.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the way of the Force",
                    "published": datetime.date(2017, 9, 25),
                }
            )
        ],
        syndication_format=syndication_format,
        save_as=str(save_as),
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": "Once upon a time",
        },
    )

    assert isinstance(stream, collections.abc.Iterable)
    assert list(stream) == [
        holocron.Item(
            {
                "content": "the way of the Force",
                "published": datetime.date(2017, 9, 25),
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://", save_as),
                "destination": pathlib.Path(save_as),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]


@pytest.mark.parametrize(
    ["syndication_format"], [pytest.param("atom"), pytest.param("rss")]
)
@pytest.mark.parametrize(["limit"], [pytest.param(2), pytest.param(5)])
def test_args_limit(testapp, syndication_format, limit):
    """Feed processor has to respect limit argument."""

    stream = feed.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the way of the Force, part %d" % i,
                    "published": datetime.date(2017, 9, i + 1),
                }
            )
            for i in range(10)
        ],
        syndication_format=syndication_format,
        limit=limit,
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": {"$ref": "item:#/content"},
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == list(
        itertools.chain(
            [
                holocron.Item(
                    {
                        "content": "the way of the Force, part %d" % i,
                        "published": datetime.date(2017, 9, i + 1),
                    }
                )
                for i in range(10)
            ],
            [
                holocron.WebSiteItem(
                    {
                        "source": pathlib.Path("feed://feed.xml"),
                        "destination": pathlib.Path("feed.xml"),
                        "content": unittest.mock.ANY,
                        "baseurl": testapp.metadata["url"],
                    }
                )
            ],
        )
    )

    parsed = untangle.parse(items[-1]["content"].decode("UTF-8"))

    if syndication_format == "atom":
        items = parsed.feed.entry
    else:
        items = parsed.rss.channel.item

    assert len(items) == limit

    for i, item in enumerate(items):
        if syndication_format == "atom":
            content = item.content
        else:
            content = item.description

        assert item.title == "Day 1"
        assert content == "the way of the Force, part %d" % (9 - i)


@pytest.mark.parametrize(
    ["syndication_format"], [pytest.param("atom"), pytest.param("rss")]
)
@pytest.mark.parametrize(
    ["pretty", "check_fn"],
    [
        pytest.param(False, lambda x: x == 2, id="no"),
        pytest.param(True, lambda x: x > 10, id="yes"),
    ],
)
def test_args_pretty(testapp, syndication_format, pretty, check_fn):
    """Feed processor has to respect pretty argument."""

    stream = feed.process(
        testapp,
        [
            holocron.Item(
                {
                    "content": "the way of the Force",
                    "published": datetime.date(2017, 9, 25),
                }
            )
        ],
        syndication_format=syndication_format,
        pretty=pretty,
        feed={
            "id": "kenobi-way",
            "title": "Kenobi's Way",
            "description": "Labours of Obi-Wan",
            "link": {"href": testapp.metadata["url"]},
        },
        item={
            "id": "day-one",
            "title": "Day 1",
            "content": "Once upon a time",
        },
    )
    assert isinstance(stream, collections.abc.Iterable)

    items = list(stream)
    assert items == [
        holocron.Item(
            {
                "content": "the way of the Force",
                "published": datetime.date(2017, 9, 25),
            }
        ),
        holocron.WebSiteItem(
            {
                "source": pathlib.Path("feed://feed.xml"),
                "destination": pathlib.Path("feed.xml"),
                "content": unittest.mock.ANY,
                "baseurl": testapp.metadata["url"],
            }
        ),
    ]
    assert check_fn(len(items[-1]["content"].splitlines()))


@pytest.mark.parametrize(
    ["args", "error"],
    [
        pytest.param(
            {"encoding": "UTF-42"},
            "encoding: 'UTF-42' is not a 'encoding'",
            id="encoding-wrong",
        ),
        pytest.param(
            {"limit": "42"},
            "limit: '42' is not valid under any of the given schemas",
            id="limit-str",
        ),
        pytest.param(
            {"save_as": 42},
            "save_as: 42 is not of type 'string'",
            id="save_as-int",
        ),
        pytest.param(
            {"pretty": 42},
            "pretty: 42 is not of type 'boolean'",
            id="pretty-int",
        ),
    ],
)
def test_args_bad_value(testapp, args, error):
    """Feed processor has to validate input arguments."""

    with pytest.raises(ValueError) as excinfo:
        next(feed.process(testapp, [], **args))
    assert str(excinfo.value) == error
