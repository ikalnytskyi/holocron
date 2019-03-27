"""Save items to a filesystem."""

import pathlib

from ._misc import parameters


@parameters(
    fallback={
        "encoding": "metadata://#/encoding",
    },
    jsonschema={
        "type": "object",
        "properties": {
            "to": {"type": "string", "format": "path"},
            "encoding": {"type": "string", "format": "encoding"},
        },
    },
)
def process(app, stream, *, to="_site", encoding="UTF-8"):
    to = pathlib.Path(to)

    for item in stream:
        destination = to.joinpath(item["destination"])
        destination.parent.mkdir(exist_ok=True, parents=True)

        # Content may be either bytes or string based on the type of content we
        # deal with (e.g. pictures, pages, etc), and therefore this content
        # must be saved accordingly.
        if isinstance(item["content"], str):
            destination.write_text(item["content"], encoding=encoding)
        else:
            destination.write_bytes(item["content"])

        yield item
