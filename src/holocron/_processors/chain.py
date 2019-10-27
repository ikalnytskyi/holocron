"""Chain and order stream of items."""

import operator

import more_itertools

from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "order_by": {"type": "string"},
            "direction": {"type": "string", "enum": ["asc", "desc"]},
        },
    }
)
def process(app, stream, *, order_by=None, direction=None):
    if direction and not order_by:
        raise ValueError("'direction' cannot be set without 'order_by'")

    if order_by:
        # WARNING: Sorting the stream requires evaluating all items from the
        # stream. This alone sets a requirement that all items must fit into,
        # which may not be achievable in certain cases.
        stream = sorted(
            stream,
            key=operator.itemgetter(order_by),
            reverse=direction == "desc",
        )

    for prev, curr in more_itertools.windowed(stream, 2):
        if curr:
            curr["prev"] = prev
            prev["next"] = curr

        if prev:
            yield prev

    if curr:
        yield curr
