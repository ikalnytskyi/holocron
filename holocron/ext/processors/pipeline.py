"""Run separate processors pipeline on selected documents."""

import schema

from ._misc import iterdocuments_ex, parameters


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'processors': schema.Schema([{str: object}]),
    }
)
def process(app, documents, *, when=None, processors=[]):
    kept = []
    selected = []

    for document, is_matched in iterdocuments_ex(documents, when):
        if is_matched:
            selected.append(document)
        else:
            kept.append(document)

    yield from kept
    yield from app.invoke_processors(selected, processors)
