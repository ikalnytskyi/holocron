"""Set given metadata on document instances."""

import schema

from ._misc import iterdocuments, parameters


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'metadata': schema.Schema({str: object}),
        'overwrite': schema.Schema(bool),
    }
)
def process(app, documents, when=None, metadata={}, overwrite=True):
    for document in iterdocuments(documents, when):
        for key, value in metadata.items():
            if overwrite or key not in document:
                document[key] = value

    return documents
