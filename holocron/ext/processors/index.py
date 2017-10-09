"""Generate index page."""

import schema

from ._misc import iterdocuments, parameters
from holocron.content import Document


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'template': schema.Schema(str),
    }
)
def process(app,
            documents,
            *,
            when=None,
            template='index.j2'):
    index = Document(app)
    index['source'] = 'virtual://index'
    index['destination'] = 'index.html'
    index['template'] = template
    index['documents'] = list(iterdocuments(documents, when))

    return documents + [index]
