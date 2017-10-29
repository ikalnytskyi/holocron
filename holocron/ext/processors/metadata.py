"""Set given metadata on document instances."""

from ._misc import iterdocuments


def process(app, documents, **options):
    metadata = options.pop('metadata', {})
    overwrite = options.pop('overwrite', True)
    when = options.pop('when', None)

    for document in iterdocuments(documents, when):
        for key, value in metadata.items():
            if overwrite or key not in document:
                document[key] = value

    return documents
