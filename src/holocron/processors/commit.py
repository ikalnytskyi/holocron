"""Commit (save) items from the stream on disk."""

import os

from ._misc import parameters


@parameters(
    fallback={
        "encoding": "metadata://#/encoding",
    },
    jsonschema={
        "type": "object",
        "properties": {
            "save_to": {"type": "string"},
            "encoding": {"type": "string", "format": "encoding"},
        },
    },
)
def process(app, stream, *, save_to="_site", encoding="UTF-8"):

    for item in stream:
        destination = os.path.join(save_to, item["destination"])

        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        if isinstance(item["content"], str):
            output = open(destination, "wt", encoding=encoding)
        else:
            output = open(destination, "wb")

        with output:
            output.write(item["content"])

        yield item
