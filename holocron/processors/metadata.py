"""Set given metadata on document instances."""

import schema

from ._misc import parameters


@parameters(
    schema={
        'metadata': schema.Schema({str: object}),
        'overwrite': schema.Schema(bool),
    }
)
def process(app, stream, *, metadata={}, overwrite=True):
    for item in stream:
        for key, value in metadata.items():
            if overwrite or key not in item:
                item[key] = value
        yield item
