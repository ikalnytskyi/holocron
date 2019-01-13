"""Generate index page."""

import itertools

import schema

from ._misc import parameters


@parameters(
    schema={
        'template': schema.Schema(str),
        'save_as': schema.Schema(str),
    }
)
def process(app, stream, *, template='index.j2', save_as='index.html'):
    passthrough, stream = itertools.tee(stream)

    index = {
        'source': 'index://%s' % save_as,
        'destination': save_as,
        'template': template,
        'documents': list(stream),
    }

    yield from passthrough
    yield index
