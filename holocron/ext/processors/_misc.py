"""Various miscellaneous functions to make code easier to read & write."""

import re


_evaluators = {
    'match':
        lambda attribute, pattern, document: (
            bool(re.match(pattern, getattr(document, attribute)))
        ),
}


def evalcondition(condition, document):
    parameters = dict(condition.copy(), document=document)
    name = parameters.pop('operator')
    return _evaluators[name](**parameters)


def iterdocuments(documents, when):
    for document in documents:
        if when is not None:
            if all((evalcondition(cond, document) for cond in when)):
                yield document
        else:
            yield document
