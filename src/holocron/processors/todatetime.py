"""Convert string based value to a datetime instance."""

import re

import schema
import dateutil.parser
import dateutil.tz

from ._misc import parameters


@parameters(
    fallback={
        "timezone": "metadata://#/timezone",
    },
    schema={
        "todatetime": schema.Or(str, [str], error="unsupported todatetime"),
        "parsearea": schema.Schema(re.compile, "unsupported regexp"),
        "timezone": schema.Schema(dateutil.tz.gettz, "unsupported timezone"),
        "fuzzy": schema.Schema(bool),
    }
)
def process(app,
            stream,
            *,
            todatetime,
            parsearea=".*",
            fuzzy=False,
            timezone="UTC"):
    tzinfo = dateutil.tz.gettz(timezone)
    re_parsearea = re.compile(parsearea)

    for item in stream:
        # Todatetime option may be a string, which means convert and save a
        # property under the same name, or pair, which means convert and save
        # properties under the given names. The latter may be handy in cases
        # when you want to extract a datetime string, let's say, from a
        # filename.
        if isinstance(todatetime, str):
            parsein, saveto = todatetime, todatetime
        else:
            parsein, saveto = todatetime

        # Usually raising an error when contract is violated is a preferred
        # option. However, taking into account the use case of 'todatetime'
        # processor, we better ignore such items in the stream to save users
        # from wrapping this processor with 'when' processor.
        if parsein not in item:
            yield item
            continue

        # Reduce a parse area by applying a regular expression. May be handy if
        # you want to extract a datetime from, let's say, a filename. If a
        # regular expression matches nothing, ignore and skip an item to avoid
        # using 'when' processor to make things *safe*.
        parsearea = re_parsearea.search(item[parsein])
        if not parsearea:
            yield item
            continue

        parsearea = parsearea.group(0)
        converted = dateutil.parser.parse(parsearea, fuzzy=fuzzy)

        # Attach passed timezone to a parsed datetime instance if tzinfo
        # hasn't been found.
        if not converted.tzinfo:
            converted = converted.replace(tzinfo=tzinfo)
        item[saveto] = converted

        yield item
