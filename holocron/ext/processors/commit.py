"""Unload pipeline by committing documents."""

import os
import codecs

import schema

from ._misc import iterdocuments_ex, parameters


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

    for document, is_matched in iterdocuments_ex(documents, when):
        if is_matched:
            destination = os.path.join(path, document['destination'])
            if not os.path.exists(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))

            if isinstance(document['content'], str):
                output = open(destination, 'wt', encoding=encoding)
            else:
                output = open(destination, 'wb')

            with output:
                output.write(document['content'])

        # Preserve in the pipeline uncommitted documents because they may have
        # other committers in the pipeline. If unload is turned off, all
        # documents will be preserved.
        if not unload or not is_matched:
            yield document
