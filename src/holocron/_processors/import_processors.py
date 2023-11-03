"""Import processors from 3rd party sources."""

import contextlib
import importlib.metadata
import sys

from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "imports": {"type": "array", "items": {"type": "string"}},
            "from_": {"type": "string"},
        },
    }
)
def process(app, items, *, imports, from_=None):
    with contextlib.ExitStack() as exit:
        if from_:
            sys.path.insert(0, from_)
            exit.callback(sys.path.pop, 0)

        for import_ in imports:
            name, path = importlib.metadata.Pair.parse(import_)
            entry_point = importlib.metadata.EntryPoint(name, path, name)
            app.add_processor(name, entry_point.load())

    # Processors are generators, so we must return iterable to be compliant
    # with the protocol. The only reason why a top-level 'process' function is
    # not a processor itself is because otherwise processors will be imported
    # pipeline evaluation time while we need them be imported pipeline creation
    # time.
    def passgen(app, items):
        yield from items

    return passgen(app, items)
