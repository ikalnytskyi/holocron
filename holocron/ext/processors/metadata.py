"""Set given metadata on document instances."""

import schema

from ._misc import iterdocuments_ex, parameters


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'metadata': schema.Schema({str: object}),
        'overwrite': schema.Schema(bool),
    }
)
def process(app, documents, *, when=None, metadata={}, overwrite=True):
    for document, is_matched in iterdocuments_ex(documents, when):
        if is_matched:
            for key, value in metadata.items():
                if overwrite or key not in document:
                    document[key] = value

        yield document
