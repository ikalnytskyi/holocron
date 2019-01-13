"""Generate an archive page."""

import itertools

import schema

from ._misc import parameters


@parameters(
    schema={
        'template': schema.Schema(str),
        'save_as': schema.Schema(str),
    }
)
def process(app, stream, *, template='archive.j2', save_as='index.html'):
    passthrough, stream = itertools.tee(stream)

    index = {
        'source': 'archive://%s' % save_as,
        'destination': save_as,
        'template': template,
        'items': list(stream),
    }

    yield from passthrough
    yield index
