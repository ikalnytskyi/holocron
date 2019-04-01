"""Generate an archive page."""

import itertools

from ..core import WebSiteItem
from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "template": {"type": "string"},
            "save_as": {"type": "string"},
        },
    },
)
def process(app, stream, *, template="archive.j2", save_as="index.html"):
    passthrough, stream = itertools.tee(stream)

    index = WebSiteItem(
        {
            "source": "archive://%s" % save_as,
            "destination": save_as,
            "template": template,
            "items": list(stream),
            "baseurl": app.metadata["url"],
        }
    )

    yield from passthrough
    yield index
