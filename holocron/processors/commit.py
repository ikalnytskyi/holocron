"""Commit (save) items from the stream on disk."""

import os
import codecs

import schema

from ._misc import parameters


@parameters(
    fallback={
        'encoding': 'metadata://#/encoding',
    },
    schema={
        'save_to': str,
        'encoding': schema.Schema(codecs.lookup, 'unsupported encoding'),
    }
)
def process(app, stream, *, save_to='_site', encoding='UTF-8'):

    for item in stream:
        destination = os.path.join(save_to, item['destination'])

        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        if isinstance(item['content'], str):
            output = open(destination, 'wt', encoding=encoding)
        else:
            output = open(destination, 'wb')

        with output:
            output.write(item['content'])

        yield item
