"""Pass items through a pipe."""

from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "pipe": {"type": "array", "items": {"type": "object"}},
        },
    },
)
def process(app, stream, *, pipe=[]):
    yield from app.invoke(pipe, stream)
