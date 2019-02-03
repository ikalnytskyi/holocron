"""Run items through a pipeline."""

import schema

from ._misc import parameters


@parameters(
    schema={
        "pipeline": schema.Schema([{str: object}]),
    }
)
def process(app, stream, *, pipeline=[]):
    yield from app.invoke(pipeline, stream)
