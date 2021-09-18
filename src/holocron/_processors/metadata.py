"""Set given metadata on document instances."""

from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "metadata": {"type": "object"},
            "overwrite": {"type": "boolean"},
        },
    }
)
def process(app, stream, *, metadata=None, overwrite=True):
    metadata = metadata or {}

    for item in stream:
        for key, value in metadata.items():
            if overwrite or key not in item:
                item[key] = value
        yield item
