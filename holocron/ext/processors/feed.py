"""Generate RSS/Atom feed (with extensions if needed)."""

import codecs
import itertools

import feedgen.feed
import pkg_resources
import schema

from ._misc import iterdocuments, parameters, resolve_json_references
from holocron.content import Document


@parameters(
    fallback={
        'encoding': ':metadata:#/encoding',
    },
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'save_as': schema.Schema(str),
        'limit': schema.Or(None, schema.And(int, lambda x: x > 0),
                           error='must be null or positive integer'),
        'encoding': schema.Schema(codecs.lookup, 'unsupported encoding'),
        'pretty': schema.Schema(bool),
        'syndication_format': schema.Or('atom', 'rss'),
    }
)
def process(app,
            documents,
            *,
            feed,
            item,
            syndication_format='atom',
            when=None,
            save_as='feed.xml',
            limit=10,
            encoding='UTF-8',
            pretty=True):
    passthrough, documents = itertools.tee(documents)
    selected = list(iterdocuments(documents, when))

    # In order to decrease amount of traffic required to deliver feed content
    # (and thus increase the throughput), the number of items in the feed is
    # usually limited to the "N" latest items. This is handy because feed is
    # usually used to deliver news, and news are known to get outdated.
    selected = sorted(selected, key=lambda d: d['published'], reverse=True)
    if limit:
        selected = selected[:limit]

    def _resolvefeed(name):
        return resolve_json_references(feed.get(name), {
            ':feed:': feed,
        })

    def _resolveitem(name, document):
        return resolve_json_references(item.get(name), {
            ':document:': document,
            ':feed:': feed,
        })

    feed_generator = feedgen.feed.FeedGenerator()

    if any((key.startswith('itunes_') for key in feed)):
        feed_generator.load_extension('podcast')
        feed_generator.podcast.itunes_author(_resolvefeed('itunes_author'))
        feed_generator.podcast.itunes_block(_resolvefeed('itunes_block'))
        feed_generator.podcast.itunes_category(
            _resolvefeed('itunes_category'), replace=True)
        feed_generator.podcast.itunes_image(_resolvefeed('itunes_image'))
        feed_generator.podcast.itunes_explicit(_resolvefeed('itunes_explicit'))
        feed_generator.podcast.itunes_complete(_resolvefeed('itunes_complete'))
        feed_generator.podcast.itunes_owner(
            **(_resolvefeed('itunes_owner') or {}))
        feed_generator.podcast.itunes_subtitle(
            _resolvefeed('itunes_subtitle'))
        feed_generator.podcast.itunes_summary(_resolvefeed('itunes_summary'))
        feed_generator.podcast.itunes_new_feed_url(
            _resolvefeed('itunes_new_feed_url'))

    feed_generator.title(_resolvefeed('title'))
    feed_generator.id(_resolvefeed('id'))
    feed_generator.author(_resolvefeed('author'), replace=True)
    feed_generator.link(_resolvefeed('link'), replace=True)
    feed_generator.category(_resolvefeed('category'), replace=True)
    feed_generator.contributor(_resolvefeed('contributor'), replace=True)
    _generator_version = pkg_resources.get_distribution('holocron').version
    feed_generator.generator(
        generator='Holocron/v%s' % _generator_version,
        version=_generator_version,
        uri='https://holocron.readthedocs.io')
    feed_generator.icon(_resolvefeed('icon'))
    feed_generator.logo(_resolvefeed('logo'))
    feed_generator.image(**(_resolvefeed('image') or {}))
    feed_generator.rights(_resolvefeed('rights'))
    feed_generator.copyright(_resolvefeed('copyright'))
    feed_generator.subtitle(_resolvefeed('subtitle'))
    feed_generator.description(_resolvefeed('description'))
    feed_generator.docs(_resolvefeed('docs'))
    feed_generator.language(_resolvefeed('language'))
    feed_generator.managingEditor(_resolvefeed('managingEditor'))
    feed_generator.rating(_resolvefeed('rating'))
    feed_generator.skipHours(_resolvefeed('skipHours'), replace=True)
    feed_generator.skipDays(_resolvefeed('skipDays'), replace=True)
    feed_generator.ttl(_resolvefeed('ttl'))
    feed_generator.webMaster(_resolvefeed('webMaster'))

    for document in selected:
        feed_entry = feed_generator.add_entry(order='append')
        feed_entry.title(_resolveitem('title', document))
        feed_entry.id(_resolveitem('id', document))
        feed_entry.updated(_resolveitem('updated', document))
        feed_entry.author(_resolveitem('author', document), replace=True)
        feed_entry.content(_resolveitem('content', document), type='html')
        feed_entry.link(_resolveitem('link', document), replace=True)
        feed_entry.description(_resolveitem('description', document))
        feed_entry.summary(_resolveitem('summary', document))
        feed_entry.category(_resolveitem('category', document), replace=True)
        feed_entry.contributor(
            _resolveitem('contributor', document), replace=True)
        feed_entry.published(_resolveitem('published', document))
        feed_entry.rights(_resolveitem('rights', document))
        feed_entry.comments(_resolveitem('comments', document))
        feed_entry.enclosure(**(_resolveitem('enclosure', document) or {}))

        if hasattr(feed_generator, 'podcast'):
            feed_entry.podcast.itunes_author(
                _resolveitem('itunes_author', document))
            feed_entry.podcast.itunes_block(
                _resolveitem('itunes_block', document))
            feed_entry.podcast.itunes_image(
                _resolveitem('itunes_image', document))
            feed_entry.podcast.itunes_duration(
                _resolveitem('itunes_duration', document))
            feed_entry.podcast.itunes_duration(
                _resolveitem('itunes_duration', document))
            feed_entry.podcast.itunes_explicit(
                _resolveitem('itunes_explicit', document))
            feed_entry.podcast.itunes_is_closed_captioned(
                _resolveitem('itunes_is_closed_captioned', document))
            feed_entry.podcast.itunes_order(
                _resolveitem('itunes_order', document))
            feed_entry.podcast.itunes_subtitle(
                _resolveitem('itunes_subtitle', document))
            feed_entry.podcast.itunes_summary(
                _resolveitem('itunes_summary', document))

    to_bytes = {'atom': feed_generator.atom_str, 'rss': feed_generator.rss_str}
    to_bytes = to_bytes[syndication_format]

    feed_document = Document(app)
    feed_document['content'] = to_bytes(pretty=pretty, encoding=encoding)
    feed_document['source'] = 'virtual://feed'
    feed_document['destination'] = save_as

    yield from passthrough
    yield feed_document
