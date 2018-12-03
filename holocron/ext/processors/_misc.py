"""Various miscellaneous functions to make code easier to read & write."""

import re
import collections
import inspect
import functools
import urllib.parse

import jsonpointer
import schema
import dooku.conf


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


def resolve_json_references(value, context, keep_unknown=True):
    def _do_resolve(node):
        if isinstance(node, collections.Mapping) and '$ref' in node:
            uri, fragment = urllib.parse.urldefrag(node['$ref'])
            try:
                return jsonpointer.resolve_pointer(context[uri], fragment)
            except KeyError:
                if keep_unknown:
                    return node
                raise
        elif isinstance(node, collections.Mapping):
            for k, v in node.items():
                node[k] = _do_resolve(v)
        elif isinstance(node, collections.Sequence) \
                and not isinstance(node, str):
            for i in range(len(node)):
                node[i] = _do_resolve(node[i])
        return node
    return _do_resolve(value)


class parameters:

    def __init__(self, *, fallback=None, schema=None):
        self._fallback = fallback or {}
        self._schema = schema

    def __call__(self, fn):
        @functools.wraps(fn)
        def wrapper(app, *args, **kwargs):
            signature = inspect.signature(fn)
            arguments = signature.bind_partial(app, *args, **kwargs).arguments

            # First two parameters are an application instance and a collection
            # of documents, and they are guaranteed to be passed as positional
            # arguments. Therefore, there's no need to check their schema or
            # resolve their fallback values. That's why we just ignore them and
            # start iterating from third parameter.
            for param in list(signature.parameters)[2:]:
                try:
                    value = arguments[param]
                except KeyError:
                    try:
                        value = resolve_json_references(
                            {'$ref': self._fallback[param]},
                            {':metadata:': app.metadata})
                    except (jsonpointer.JsonPointerException, KeyError):
                        continue

                # this is a temporary hack to workaround schema error
                # that dooku.conf.Conf is not a dict
                if isinstance(value, dooku.conf.Conf):
                    value = dict(value)

                if param in self._schema:
                    try:
                        schema.Schema(self._schema[param]).validate(value)
                    except schema.SchemaError as exc:
                        raise ValueError('%s: %s' % (param, str(exc)))

                kwargs[param] = value
            return fn(app, *args, **kwargs)
        return wrapper
