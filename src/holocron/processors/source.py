"""Populate stream with new items found on filesystem."""

import re
import os
import datetime
import codecs

import dateutil.tz
import schema

import holocron.core
from ._misc import parameters


def _createitem(app, path, basepath, encoding, tzinfo):
    try:
        with open(path, "rt", encoding=encoding) as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(path, "rb") as f:
            content = f.read()

    created = datetime.datetime.fromtimestamp(os.path.getctime(path), tzinfo)
    updated = datetime.datetime.fromtimestamp(os.path.getmtime(path), tzinfo)

    return holocron.core.WebSiteItem(
        # Memorizing 'source' property is not required for application core,
        # however, it may be useful for troubleshooting pipes as well as
        # writing 'when' conditions.
        source=os.path.relpath(path, basepath),
        destination=os.path.relpath(path, basepath),
        content=content,
        created=created,
        updated=updated,
        baseurl=app.metadata["url"],
    )


def _finditems(app, path, pattern, encoding, tzinfo):
    if pattern:
        re_name = re.compile(pattern)

    for root, dirnames, filenames in os.walk(path, topdown=True):
        for filename in filenames:
            source = os.path.relpath(os.path.join(root, filename), path)

            if pattern and not re_name.match(source):
                continue

            yield _createitem(
                app,
                os.path.join(root, filename),
                basepath=path,
                encoding=encoding,
                tzinfo=tzinfo,
            )


@parameters(
    fallback={
        "encoding": "metadata://#/encoding",
        "timezone": "metadata://#/timezone",
    },
    schema={
        "path": str,
        "pattern": str,
        "encoding": schema.Schema(codecs.lookup, "unsupported encoding"),
        "timezone": schema.Schema(dateutil.tz.gettz, "unsupported timezone"),
    },
)
def process(
    app, stream, *, path=".", pattern=None, encoding="UTF-8", timezone="UTC"
):
    tzinfo = dateutil.tz.gettz(timezone)

    yield from stream
    yield from _finditems(app, path, pattern, encoding, tzinfo)
