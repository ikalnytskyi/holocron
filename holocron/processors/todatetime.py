"""Convert string based value to a datetime instance."""

import re

import schema
import dateutil.parser
import dateutil.tz

from ._misc import parameters


@parameters(
    fallback={
        'timezone': 'metadata://#/timezone',
    },
    schema={
        'todatetime': schema.Or(str, [str], error='unsupported todatetime'),
        'parsearea': schema.Schema(re.compile, 'unsupported regexp'),
        'timezone': schema.Schema(dateutil.tz.gettz, 'unsupported timezone'),
        'fuzzy': schema.Schema(bool),
    }
)
def process(app,
            stream,
            *,
            todatetime,
            parsearea='.*',
            fuzzy=False,
            timezone='UTC'):
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

        # Reduce a parse area by applying a regular expression. May be handy
        # if you want to extract a datetime information from a filename.
        parsearea = re_parsearea.search(item[parsein])
        if not parsearea:
            raise RuntimeError(
                "'parsearea' is not found in '%s' property: '%s' has no "
                "occurance of '%s'" % (
                    parsein, item[parsein], re_parsearea.pattern))
        parsearea = parsearea.group(0)
        converted = dateutil.parser.parse(parsearea, fuzzy=fuzzy)

        # Attach passed timezone to a parsed datetime instance if tzinfo
        # hasn't been found.
        if not converted.tzinfo:
            converted = converted.replace(tzinfo=tzinfo)
        item[saveto] = converted

        yield item
