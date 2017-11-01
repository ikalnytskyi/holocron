"""Various miscellaneous functions to make code easier to read & write."""

import re


_evaluators = {
    'match':
        lambda attribute, pattern, document: (
            bool(re.match(pattern, document[attribute]))
        ),
}


def evalcondition(condition, document):
    parameters = dict(condition.copy(), document=document)
    name = parameters.pop('operator')
    return _evaluators[name](**parameters)


def iterdocuments(documents, when):
    for document, is_matched in iterdocuments_ex(documents, when):
        if is_matched:
            yield document


def iterdocuments_ex(documents, when):
    for document in documents:
        is_matched = True

        if when is not None:
            if any((not evalcondition(cond, document) for cond in when)):
                is_matched = False

        yield document, is_matched
