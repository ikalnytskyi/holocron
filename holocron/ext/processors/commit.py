"""Unload pipeline by committing documents."""

import os
import codecs

import schema

from ._misc import iterdocuments, parameters


@parameters(
    fallback={
        'encoding': ':metadata:#/encoding',
    },
    schema={
        'path': str,
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'encoding': schema.Schema(codecs.lookup, 'unsupported encoding'),
        'unload': schema.Schema(bool),
    }
)
def process(app,
            documents,
            *,
            path='_site',
            when=None,
            unload=True,
            encoding='UTF-8'):
    to_remove = []

    for document in iterdocuments(list(documents), when):
        to_remove.append(document)

        destination = os.path.join(path, document['destination'])
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        # A document may suggest its own encoding as it might be pretty
        # important to have this one.
        enc = document.get('encoding', encoding)

        # Once Jinja2 is a standalone processor, these lines will be gone.
        if 'template' in document:
            template = app.jinja_env.get_template(document['template'])
            document['content'] = \
                template.render(document=document, encoding=enc)

        if isinstance(document['content'], str):
            output = open(destination, 'wt', encoding=enc)
        else:
            output = open(destination, 'wb')

        with output:
            output.write(document['content'])

    if unload:
        for document in to_remove:
            documents.remove(document)

    return documents
