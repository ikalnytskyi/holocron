"""Feed processor test suite."""

import os
import datetime
import unittest.mock

import pkg_resources
import pytest
import untangle

from holocron import app
from holocron.processors import feed


_HOLOCRON_VERSION = pkg_resources.get_distribution('holocron').version


@pytest.fixture(scope='function')
def testapp():
    return app.Holocron({}, metadata={
        'url': 'http://obi-wan.jedi',
    })


def test_item_atom(testapp):
    """Feed (atom) processor has to work with minimum amount of metadata!"""

    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': datetime.date(2017, 9, 25),
            },
        ],
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': 'Once upon a time',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': datetime.date(2017, 9, 25),
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    parsed = untangle.parse(item['content'].decode('UTF-8'))
    assert set(dir(parsed.feed)) == {
        'id',
        'title',
        'subtitle',
        'link',
        'generator',
        'updated',
        'entry',
    }
    assert parsed.feed['xmlns'] == 'http://www.w3.org/2005/Atom'
    assert parsed.feed.id == 'kenobi-way'
    assert parsed.feed.title == "Kenobi's Way"
    assert parsed.feed.subtitle == 'Labours of Obi-Wan'
    assert parsed.feed.link['href'] == testapp.metadata['url']
    assert parsed.feed.generator['uri'] == 'https://holocron.readthedocs.io'
    assert parsed.feed.generator['version'] == _HOLOCRON_VERSION
    assert parsed.feed.generator == 'Holocron/v%s' % _HOLOCRON_VERSION

    assert set(dir(parsed.feed.entry)) == {
        'id',
        'title',
        'content',
        'updated',
    }
    assert parsed.feed.entry.id == 'day-one'
    assert parsed.feed.entry.title == 'Day 1'
    assert parsed.feed.entry.content == 'Once upon a time'
    assert parsed.feed.entry.content['type'] == 'html'

    with pytest.raises(StopIteration):
        next(stream)


def test_item_atom_feed_metadata(testapp):
    """Feed (atom) processor has to work with full metadata set!"""

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': published,
            },
        ],
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'subtitle': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
            'author': {'name': 'Obi-Wan', 'email': 'obi1@kenobi.com'},
            'contributor': {'name': 'Yoda', 'email': 'yoda@jedi.com'},
            'icon': 'path/to/icon',
            'logo': 'path/to/logo',
            'rights': '(c) Obi-Wan',
            'language': 'uk',
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': 'Once upon a time',
            'author': {'name': 'Obi-Wan', 'email': 'obi1@kenobi.com'},
            'link': {'href': 'path/to/webpage', 'rel': 'alternate'},
            'summary': 'about the Force',
            'contributor': {'name': 'Dooku', 'email': 'dooku@sith.com'},
            'published': {'$ref': 'item://#/published'},
            'rights': '(c) Obi-Wan and the Jedi Order',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': published,
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    parsed = untangle.parse(item['content'].decode('UTF-8'))
    assert set(dir(parsed.feed)) == {
        'id',
        'title',
        'subtitle',
        'link',
        'generator',
        'updated',
        'author',
        'contributor',
        'icon',
        'logo',
        'rights',
        'entry',
    }
    assert parsed.feed['xmlns'] == 'http://www.w3.org/2005/Atom'
    assert parsed.feed['xml:lang'] == 'uk'
    assert parsed.feed.id == 'kenobi-way'
    assert parsed.feed.title == "Kenobi's Way"
    assert parsed.feed.subtitle == 'Labours of Obi-Wan'
    assert parsed.feed.link['href'] == testapp.metadata['url']
    assert parsed.feed.generator['uri'] == 'https://holocron.readthedocs.io'
    assert parsed.feed.generator['version'] == _HOLOCRON_VERSION
    assert parsed.feed.generator == 'Holocron/v%s' % _HOLOCRON_VERSION
    assert parsed.feed.author.name == 'Obi-Wan'
    assert parsed.feed.author.email == 'obi1@kenobi.com'
    assert parsed.feed.contributor.name == 'Yoda'
    assert parsed.feed.contributor.email == 'yoda@jedi.com'
    assert parsed.feed.icon == 'path/to/icon'
    assert parsed.feed.logo == 'path/to/logo'
    assert parsed.feed.rights == '(c) Obi-Wan'

    assert set(dir(parsed.feed.entry)) == {
        'id',
        'title',
        'content',
        'updated',
        'author',
        'link',
        'summary',
        'contributor',
        'published',
        'rights',
    }
    assert parsed.feed.entry.id == 'day-one'
    assert parsed.feed.entry.title == 'Day 1'
    assert parsed.feed.entry.content == 'Once upon a time'
    assert parsed.feed.entry.content['type'] == 'html'
    assert parsed.feed.entry.author.name == 'Obi-Wan'
    assert parsed.feed.entry.author.email == 'obi1@kenobi.com'
    assert parsed.feed.entry.link['href'] == 'path/to/webpage'
    assert parsed.feed.entry.link['rel'] == 'alternate'
    assert parsed.feed.entry.summary == 'about the Force'
    assert parsed.feed.entry.contributor.name == 'Dooku'
    assert parsed.feed.entry.contributor.email == 'dooku@sith.com'
    assert parsed.feed.entry.published == published.isoformat()
    assert parsed.feed.entry.rights == '(c) Obi-Wan and the Jedi Order'

    with pytest.raises(StopIteration):
        next(stream)


def test_item_rss(testapp):
    """Feed (rss) processor has to work with minimum amount of metadata!"""

    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': datetime.date(2017, 9, 25),
            },
        ],
        syndication_format='rss',
        feed={
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'title': 'Day 1',
            'content': 'Once upon a time',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': datetime.date(2017, 9, 25),
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    parsed = untangle.parse(item['content'].decode('UTF-8'))
    assert set(dir(parsed.rss.channel)) == {
        'title',
        'description',
        'link',
        'generator',
        'lastBuildDate',
        'docs',
        'item',
    }
    assert parsed.rss['xmlns:atom'] == 'http://www.w3.org/2005/Atom'
    assert parsed.rss['xmlns:content'] == (
        'http://purl.org/rss/1.0/modules/content/')
    assert parsed.rss['version'] == '2.0'
    assert parsed.rss.channel.title == "Kenobi's Way"
    assert parsed.rss.channel.description == 'Labours of Obi-Wan'
    assert parsed.rss.channel.link == testapp.metadata['url']
    assert parsed.rss.channel.generator \
        == 'Holocron/v%s' % _HOLOCRON_VERSION

    assert set(dir(parsed.rss.channel.item)) == {
        'title',
        'description',
    }
    assert parsed.rss.channel.item.title == 'Day 1'
    assert parsed.rss.channel.item.description == 'Once upon a time'

    with pytest.raises(StopIteration):
        next(stream)


def test_item_rss_feed_metadata(testapp):
    """Feed (rss) processor has to work with full metadata set!"""

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': published,
            },
        ],
        syndication_format='rss',
        feed={
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
            'category': {'term': 'Jedi'},
            'image': {'url': 'path/to/image', 'width': '100'},
            'copyright': '(c) Obi-Wan',
            'language': 'uk',
            'managingEditor': 'yoda@jedi.com',
            'rating': 'some PICS rating',
            'skipHours': [7, 8, 9],
            'skipDays': ['Friday'],
            'ttl': 42,
            'webMaster': 'luke@skywalker.com',
            'itunes_author': 'dooku@sith.com',
            'itunes_block': False,
            'itunes_category': {'cat': 'Arts', 'sub': 'Design'},
            'itunes_image': 'path/to/image.png',
            'itunes_explicit': 'clean',
            'itunes_complete': 'no',
            'itunes_owner': {'name': 'obi-wan', 'email': 'ben@kenobi.com'},
            'itunes_subtitle': 'Labours of Obi-Wan Podcast',
            'itunes_summary': 'Well, you know.. gibberish',
            'itunes_new_feed_url': 'path/to/new/url',
        },
        item={
            'guid': 'kenobi-way',
            'title': 'Day 1',
            'content': 'Once upon a time',
            'author': {'name': 'Obi-Wan', 'email': 'obi1@kenobi.com'},
            'link': {'href': 'path/to/webpage', 'rel': 'alternate'},
            'description': 'about the Force',
            'enclosure': {'url': 'x.mp3', 'length': '42', 'type': 'audio/mp3'},
            'published': {'$ref': 'item://#/published'},
            'ttl': '13',
            'itunes_author': 'vader@sith.com',
            'itunes_block': False,
            'itunes_image': 'path/to/episode/image.png',
            'itunes_duration': '00:32:13',
            'itunes_explicit': 'yes',
            'itunes_is_closed_captioned': True,
            'itunes_order': 42,
            'itunes_subtitle': 'cherry',
            'itunes_summary': 'berry',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': published,
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    parsed = untangle.parse(item['content'].decode('UTF-8'))
    assert set(dir(parsed.rss.channel)) == {
        'title',
        'description',
        'link',
        'generator',
        'lastBuildDate',
        'docs',
        'category',
        'copyright',
        'image',
        'language',
        'managingEditor',
        'rating',
        'skipDays',
        'skipHours',
        'ttl',
        'webMaster',
        'item',
        'itunes_author',
        'itunes_block',
        'itunes_category',
        'itunes_image',
        'itunes_explicit',
        'itunes_complete',
        'itunes_owner',
        'itunes_subtitle',
        'itunes_summary',
        'itunes_new_feed_url',
    }
    assert parsed.rss['xmlns:atom'] == 'http://www.w3.org/2005/Atom'
    assert parsed.rss['xmlns:itunes'] == (
        'http://www.itunes.com/dtds/podcast-1.0.dtd')
    assert parsed.rss['xmlns:content'] == (
        'http://purl.org/rss/1.0/modules/content/')
    assert parsed.rss['version'] == '2.0'
    assert parsed.rss.channel.title == "Kenobi's Way"
    assert parsed.rss.channel.description == 'Labours of Obi-Wan'
    assert parsed.rss.channel.link == testapp.metadata['url']
    assert parsed.rss.channel.generator \
        == 'Holocron/v%s' % _HOLOCRON_VERSION
    assert parsed.rss.channel.category == 'Jedi'
    assert parsed.rss.channel.image.url == 'path/to/image'
    assert parsed.rss.channel.image.title == "Kenobi's Way"
    assert parsed.rss.channel.image.link == testapp.metadata['url']
    assert parsed.rss.channel.image.width == '100'
    assert parsed.rss.channel.copyright == '(c) Obi-Wan'
    assert parsed.rss.channel.language == 'uk'
    assert parsed.rss.channel.managingEditor == 'yoda@jedi.com'
    assert parsed.rss.channel.rating == 'some PICS rating'
    assert {x.cdata for x in parsed.rss.channel.skipHours.children} \
        == {'7', '8', '9'}
    assert parsed.rss.channel.skipDays.day == 'Friday'
    assert parsed.rss.channel.ttl == '42'
    assert parsed.rss.channel.webMaster == 'luke@skywalker.com'
    assert parsed.rss.channel.itunes_author == 'dooku@sith.com'
    assert parsed.rss.channel.itunes_block == 'no'
    assert parsed.rss.channel.itunes_category['text'] == 'Arts'
    assert parsed.rss.channel.itunes_category.itunes_category['text'] \
        == 'Design'
    assert parsed.rss.channel.itunes_image['href'] == 'path/to/image.png'
    assert parsed.rss.channel.itunes_explicit == 'clean'
    assert parsed.rss.channel.itunes_complete == 'no'
    assert parsed.rss.channel.itunes_owner.itunes_name == 'obi-wan'
    assert parsed.rss.channel.itunes_owner.itunes_email == 'ben@kenobi.com'
    assert parsed.rss.channel.itunes_subtitle == 'Labours of Obi-Wan Podcast'
    assert parsed.rss.channel.itunes_summary == 'Well, you know.. gibberish'
    assert parsed.rss.channel.itunes_new_feed_url == 'path/to/new/url'

    assert set(dir(parsed.rss.channel.item)) == {
        'title',
        'description',
        'author',
        'content_encoded',
        'enclosure',
        'link',
        'pubDate',
        'itunes_author',
        'itunes_block',
        'itunes_image',
        'itunes_duration',
        'itunes_explicit',
        'itunes_isClosedCaptioned',
        'itunes_order',
        'itunes_subtitle',
        'itunes_summary',
    }
    assert parsed.rss.channel.item.title == 'Day 1'
    assert parsed.rss.channel.item.description == 'about the Force'
    assert parsed.rss.channel.item.author == 'obi1@kenobi.com (Obi-Wan)'
    assert parsed.rss.channel.item.content_encoded == 'Once upon a time'
    assert parsed.rss.channel.item.enclosure['url'] == 'x.mp3'
    assert parsed.rss.channel.item.enclosure['length'] == '42'
    assert parsed.rss.channel.item.enclosure['type'] == 'audio/mp3'
    assert parsed.rss.channel.item.link == 'path/to/webpage'
    assert parsed.rss.channel.item.pubDate == 'Mon, 25 Sep 2017 00:00:00 +0000'

    assert parsed.rss.channel.item.itunes_author == 'vader@sith.com'
    assert parsed.rss.channel.item.itunes_block == 'no'
    assert parsed.rss.channel.item.itunes_image['href'] \
        == 'path/to/episode/image.png'
    assert parsed.rss.channel.item.itunes_duration == '00:32:13'
    assert parsed.rss.channel.item.itunes_explicit == 'yes'
    assert parsed.rss.channel.item.itunes_isClosedCaptioned == 'yes'
    assert parsed.rss.channel.item.itunes_order == '42'
    assert parsed.rss.channel.item.itunes_subtitle == 'cherry'
    assert parsed.rss.channel.item.itunes_summary == 'berry'

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('syndication_format', ['atom', 'rss'])
@pytest.mark.parametrize('amount', [0, 1, 2, 5, 10])
def test_item_many(testapp, syndication_format, amount):
    """Feed processor has to work with stream."""

    stream = feed.process(
        testapp,
        [
            {
                'content': 'the key is %d' % i,
                'published': datetime.date(2017, 9, 25),
            }
            for i in range(amount)
        ],
        syndication_format=syndication_format,
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': 'Once upon a time',
        })

    for i in range(amount):
        assert next(stream) == \
            {
                'content': 'the key is %d' % i,
                'published': datetime.date(2017, 9, 25),
            }

    assert next(stream) == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('syndication_format', ['atom', 'rss'])
@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding(testapp, syndication_format, encoding):
    """Feed processor has to respect encoding parameter."""

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': published,
            },
        ],
        syndication_format=syndication_format,
        encoding=encoding,
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': 'Once upon a time',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': published,
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    assert untangle.parse(item['content'].decode(encoding))

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('syndication_format', ['atom', 'rss'])
@pytest.mark.parametrize('encoding', ['CP1251', 'UTF-16'])
def test_param_encoding_fallback(testapp, syndication_format, encoding):
    """Feed processor has to respect encoding parameter (fallback)."""

    testapp.metadata.update({'encoding': encoding})

    published = datetime.datetime(2017, 9, 25, tzinfo=datetime.timezone.utc)
    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': published,
            },
        ],
        syndication_format=syndication_format,
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': 'Once upon a time',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': published,
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    assert untangle.parse(item['content'].decode(encoding))

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('syndication_format', ['atom', 'rss'])
@pytest.mark.parametrize('save_as', [
    'foo.xml',
    os.path.join('foo', 'bar.xml'),
])
def test_param_save_as(testapp, syndication_format, save_as):
    """Feed processor has to respect save_as parameter."""

    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': datetime.date(2017, 9, 25),
            },
        ],
        syndication_format=syndication_format,
        save_as=save_as,
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': 'Once upon a time',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': datetime.date(2017, 9, 25),
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://%s' % save_as,
            'destination': save_as,
            'content': unittest.mock.ANY,
        }

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('syndication_format', ['atom', 'rss'])
@pytest.mark.parametrize('limit', (2, 5))
def test_param_limit(testapp, syndication_format, limit):
    """Feed processor has to respect limit parameter."""

    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force, part %d' % i,
                'published': datetime.date(2017, 9, i + 1),
            }
            for i in range(10)
        ],
        syndication_format=syndication_format,
        limit=limit,
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': {'$ref': 'item:#/content'},
        })

    for i, item in zip(range(10), stream):
        assert item == \
            {
                'content': 'the way of the Force, part %d' % i,
                'published': datetime.date(2017, 9, i + 1),
            }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }

    parsed = untangle.parse(item['content'].decode('UTF-8'))

    if syndication_format == 'atom':
        items = parsed.feed.entry
    else:
        items = parsed.rss.channel.item

    assert len(items) == limit

    for i, item in enumerate(items):
        if syndication_format == 'atom':
            content = item.content
        else:
            content = item.description

        assert item.title == 'Day 1'
        assert content == 'the way of the Force, part %d' % (9 - i)

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('syndication_format', ['atom', 'rss'])
@pytest.mark.parametrize('pretty, check_fn', (
    (False, lambda x: x == 2),
    (True, lambda x: x > 10),
))
def test_param_pretty(testapp, syndication_format, pretty, check_fn):
    """Feed processor has to respect pretty parameter."""

    stream = feed.process(
        testapp,
        [
            {
                'content': 'the way of the Force',
                'published': datetime.date(2017, 9, 25),
            },
        ],
        syndication_format=syndication_format,
        pretty=pretty,
        feed={
            'id': 'kenobi-way',
            'title': "Kenobi's Way",
            'description': 'Labours of Obi-Wan',
            'link': {'href': testapp.metadata['url']},
        },
        item={
            'id': 'day-one',
            'title': 'Day 1',
            'content': 'Once upon a time',
        })

    assert next(stream) == \
        {
            'content': 'the way of the Force',
            'published': datetime.date(2017, 9, 25),
        }

    item = next(stream)
    assert item == \
        {
            'source': 'feed://feed.xml',
            'destination': 'feed.xml',
            'content': unittest.mock.ANY,
        }
    assert check_fn(len(item['content'].splitlines()))

    with pytest.raises(StopIteration):
        next(stream)


@pytest.mark.parametrize('params, error', [
    ({'encoding': 'UTF-42'}, 'encoding: unsupported encoding'),
    ({'limit': '42'}, "limit: must be null or positive integer"),
    ({'save_as': 42}, "save_as: 42 should be instance of 'str'"),
    ({'pretty': 42}, "pretty: 42 should be instance of 'bool'"),
])
def test_param_bad_value(testapp, params, error):
    """Feed processor has to validate input parameters."""

    with pytest.raises(ValueError, match=error):
        next(feed.process(testapp, [], **params))
