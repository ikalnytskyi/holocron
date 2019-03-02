"""Pass items through a pipe."""

import schema

from ._misc import parameters


@parameters(
    schema={
        "pipe": schema.Schema([{str: object}]),
    }
)
def process(app, stream, *, pipe=[]):
    yield from app.invoke(pipe, stream)
