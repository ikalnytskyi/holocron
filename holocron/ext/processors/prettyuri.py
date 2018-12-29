"""Strip .HTML extension from URIs."""

import os
import schema

from ._misc import iterdocuments_ex, parameters


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
    }
)
def process(app, documents, *, when=None):
    for document, is_matched in iterdocuments_ex(documents, when):
        if is_matched:
            destination = os.path.basename(document['destination'])

            # Most modern HTTP servers implicitly serve one of these files when
            # requested URL is pointing to a directory on filesystem. Hence in
            # order to provide "pretty" URLs we need to transform destination
            # address accordingly.
            if destination not in ('index.html', 'index.htm'):
                document['destination'] = os.path.join(
                    os.path.splitext(document['destination'])[0], 'index.html')

        yield document
