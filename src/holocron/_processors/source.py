"""Populate stream with new items found on filesystem."""

import re
import os
import datetime
import pathlib

import dateutil.tz

import holocron
from ._misc import parameters


def _createitem(app, path, source, encoding, tzinfo):
    try:
        content = path.read_text(encoding)
    except UnicodeDecodeError:
        content = path.read_bytes()

    created = datetime.datetime.fromtimestamp(path.stat().st_ctime, tzinfo)
    updated = datetime.datetime.fromtimestamp(path.stat().st_mtime, tzinfo)

    return holocron.WebSiteItem(
        # Memorizing 'source' property is not required for application core,
        # however, it may be useful for troubleshooting pipes as well as
        # writing 'when' conditions.
        source=source,
        destination=source,
        content=content,
        created=created,
        updated=updated,
        baseurl=app.metadata["url"],
    )


def _finditems(app, path, pattern, encoding, tzinfo):
    if pattern:
        re_name = re.compile(pattern)

    for root, dirnames, filenames in os.walk(path, topdown=True):
        root = pathlib.Path(root)

        for filename in filenames:
            source = root.joinpath(filename).relative_to(path)

            if pattern and not re_name.match(str(source)):
                continue

            yield _createitem(
                app, root / filename, source, encoding=encoding, tzinfo=tzinfo
            )


@parameters(
    fallback={
        "encoding": "metadata://#/encoding",
        "timezone": "metadata://#/timezone",
    },
    jsonschema={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "pattern": {"type": "string"},
            "encoding": {"type": "string", "format": "encoding"},
            "timezone": {"type": "string", "format": "timezone"},
        },
    },
)
def process(
    app, stream, *, path=".", pattern=None, encoding="UTF-8", timezone="UTC"
):
    tzinfo = dateutil.tz.gettz(timezone)

    yield from stream
    yield from _finditems(app, path, pattern, encoding, tzinfo)
