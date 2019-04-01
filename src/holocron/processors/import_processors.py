"""Import processors from 3rd party sources."""

import contextlib
import sys

import pkg_resources

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
    distribution = pkg_resources.get_distribution("holocron")

    with contextlib.ExitStack() as exit:
        if from_:
            sys.path.insert(0, from_)
            exit.callback(sys.path.pop, 0)

        for import_ in imports:
            entry_point = pkg_resources.EntryPoint.parse(import_, distribution)
            app.add_processor(entry_point.name, entry_point.resolve())

    # Processors are generators, so we must return iterable to be compliant
    # with the protocol. The only reason why a top-level 'process' function is
    # not a processor itself is because otherwise processors will be imported
    # pipeline evaluation time while we need them be imported pipeline creation
    # time.
    def passgen(app, items):
        yield from items

    return passgen(app, items)
