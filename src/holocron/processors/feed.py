"""Generate RSS/Atom feed (with extensions if needed)."""

import itertools

import feedgen.feed
import pkg_resources

from ..core import WebSiteItem
from ._misc import parameters, resolve_json_references


@parameters(
    fallback={
        "encoding": "metadata://#/encoding",
    },
    jsonschema={
        "type": "object",
        "properties": {
            "save_as": {"type": "string"},
            "limit": {
                "anyOf": [
                    {"type": "integer", "exclusiveMinimum": 0},
                    {"type": "null"},
                ],
            },
            "encoding": {"type": "string", "format": "encoding"},
            "pretty": {"type": "boolean"},
            "syndication_format": {"type": "string", "enum": ["atom", "rss"]},
        },
    },
)
def process(app,
            stream,
            *,
            feed,
            item,
            syndication_format="atom",
            save_as="feed.xml",
            limit=10,
            encoding="UTF-8",
            pretty=True):
    passthrough, stream = itertools.tee(stream)

    # In order to decrease amount of traffic required to deliver feed content
    # (and thus increase the throughput), the number of items in the feed is
    # usually limited to the "N" latest items. This is handy because feed is
    # usually used to deliver news, and news are known to get outdated.
    stream = sorted(stream, key=lambda d: d["published"], reverse=True)
    if limit:
        stream = stream[:limit]

    def _resolvefeed(name):
        return resolve_json_references(feed.get(name), {
            "feed:": feed,
        })

    def _resolveitem(name, streamitem):
        return resolve_json_references(item.get(name), {
            "item:": streamitem,
            "feed:": feed,
        })

    feed_generator = feedgen.feed.FeedGenerator()

    if any((key.startswith("itunes_") for key in feed)):
        feed_generator.load_extension("podcast")
        feed_generator.podcast.itunes_author(_resolvefeed("itunes_author"))
        feed_generator.podcast.itunes_block(_resolvefeed("itunes_block"))
        feed_generator.podcast.itunes_category(
            _resolvefeed("itunes_category"), replace=True)
        feed_generator.podcast.itunes_image(_resolvefeed("itunes_image"))
        feed_generator.podcast.itunes_explicit(_resolvefeed("itunes_explicit"))
        feed_generator.podcast.itunes_complete(_resolvefeed("itunes_complete"))
        feed_generator.podcast.itunes_owner(
            **(_resolvefeed("itunes_owner") or {}))
        feed_generator.podcast.itunes_subtitle(
            _resolvefeed("itunes_subtitle"))
        feed_generator.podcast.itunes_summary(_resolvefeed("itunes_summary"))
        feed_generator.podcast.itunes_new_feed_url(
            _resolvefeed("itunes_new_feed_url"))

    feed_generator.title(_resolvefeed("title"))
    feed_generator.id(_resolvefeed("id"))
    feed_generator.author(_resolvefeed("author"), replace=True)
    feed_generator.link(_resolvefeed("link"), replace=True)
    feed_generator.category(_resolvefeed("category"), replace=True)
    feed_generator.contributor(_resolvefeed("contributor"), replace=True)
    _generator_version = pkg_resources.get_distribution("holocron").version
    feed_generator.generator(
        generator="Holocron/v%s" % _generator_version,
        version=_generator_version,
        uri="https://holocron.readthedocs.io")
    feed_generator.icon(_resolvefeed("icon"))
    feed_generator.logo(_resolvefeed("logo"))
    feed_generator.image(**(_resolvefeed("image") or {}))
    feed_generator.rights(_resolvefeed("rights"))
    feed_generator.copyright(_resolvefeed("copyright"))
    feed_generator.subtitle(_resolvefeed("subtitle"))
    feed_generator.description(_resolvefeed("description"))
    feed_generator.docs(_resolvefeed("docs"))
    feed_generator.language(_resolvefeed("language"))
    feed_generator.managingEditor(_resolvefeed("managingEditor"))
    feed_generator.rating(_resolvefeed("rating"))
    feed_generator.skipHours(_resolvefeed("skipHours"), replace=True)
    feed_generator.skipDays(_resolvefeed("skipDays"), replace=True)
    feed_generator.ttl(_resolvefeed("ttl"))
    feed_generator.webMaster(_resolvefeed("webMaster"))

    for streamitem in stream:
        feed_entry = feed_generator.add_entry(order="append")
        feed_entry.title(_resolveitem("title", streamitem))
        feed_entry.id(_resolveitem("id", streamitem))
        feed_entry.updated(_resolveitem("updated", streamitem))
        feed_entry.author(_resolveitem("author", streamitem), replace=True)
        feed_entry.content(_resolveitem("content", streamitem), type="html")
        feed_entry.link(_resolveitem("link", streamitem), replace=True)
        feed_entry.description(_resolveitem("description", streamitem))
        feed_entry.summary(_resolveitem("summary", streamitem))
        feed_entry.category(_resolveitem("category", streamitem), replace=True)
        feed_entry.contributor(
            _resolveitem("contributor", streamitem), replace=True)
        feed_entry.published(_resolveitem("published", streamitem))
        feed_entry.rights(_resolveitem("rights", streamitem))
        feed_entry.comments(_resolveitem("comments", streamitem))
        feed_entry.enclosure(**(_resolveitem("enclosure", streamitem) or {}))

        if hasattr(feed_generator, "podcast"):
            feed_entry.podcast.itunes_author(
                _resolveitem("itunes_author", streamitem))
            feed_entry.podcast.itunes_block(
                _resolveitem("itunes_block", streamitem))
            feed_entry.podcast.itunes_image(
                _resolveitem("itunes_image", streamitem))
            feed_entry.podcast.itunes_duration(
                _resolveitem("itunes_duration", streamitem))
            feed_entry.podcast.itunes_duration(
                _resolveitem("itunes_duration", streamitem))
            feed_entry.podcast.itunes_explicit(
                _resolveitem("itunes_explicit", streamitem))
            feed_entry.podcast.itunes_is_closed_captioned(
                _resolveitem("itunes_is_closed_captioned", streamitem))
            feed_entry.podcast.itunes_order(
                _resolveitem("itunes_order", streamitem))
            feed_entry.podcast.itunes_subtitle(
                _resolveitem("itunes_subtitle", streamitem))
            feed_entry.podcast.itunes_summary(
                _resolveitem("itunes_summary", streamitem))

    to_bytes = {"atom": feed_generator.atom_str, "rss": feed_generator.rss_str}
    to_bytes = to_bytes[syndication_format]

    feed_item = WebSiteItem(
        {
            "source": "feed://%s" % save_as,
            "destination": save_as,
            "content": to_bytes(pretty=pretty, encoding=encoding),
            "baseurl": app.metadata["url"],
        })

    yield from passthrough
    yield feed_item
