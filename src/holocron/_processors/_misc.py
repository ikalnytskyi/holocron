"""Various miscellaneous functions to make code easier to read & write."""

import collections.abc
import inspect
import logging
import functools
import urllib.parse

import jsonschema
import jsonpointer


_logger = logging.getLogger("holocron")


def resolve_json_references(value, context, keep_unknown=True):
    def _do_resolve(node):
        if isinstance(node, collections.abc.Mapping) and "$ref" in node:
            uri, fragment = urllib.parse.urldefrag(node["$ref"])
            try:
                return jsonpointer.resolve_pointer(context[uri], fragment)
            except KeyError:
                if keep_unknown:
                    return node
                raise
        elif isinstance(node, collections.abc.Mapping):
            for k, v in node.items():
                node[k] = _do_resolve(v)
        elif isinstance(node, collections.abc.Sequence) and not isinstance(
            node, str
        ):
            if not isinstance(node, collections.abc.MutableSequence):
                node = list(node)

            for i in range(len(node)):
                node[i] = _do_resolve(node[i])
        return node

    return _do_resolve(value)


class parameters:
    def __init__(self, *, fallback=None, jsonschema=None):
        self._fallback = fallback or {}
        self._jsonschema = jsonschema

    def __call__(self, fn):
        @functools.wraps(fn)
        def wrapper(app, *args, **kwargs):
            signature = inspect.signature(fn)
            arguments = signature.bind_partial(app, *args, **kwargs).arguments

            # First two arguments always are an application instance and a
            # stream of items to process. Since they are passed by Holocron
            # core as positional arguments, there's no real need to check their
            # schema, so we strip them away.
            arguments = dict(list(arguments.items())[2:])
            parameters = dict(list(signature.parameters.items())[2:])

            # If some parameter has not been passed, a value from a fallback
            # must be used instead (if any).
            for param in parameters:
                if param not in arguments:
                    try:
                        value = resolve_json_references(
                            {"$ref": self._fallback[param]},
                            {"metadata:": app.metadata},
                        )
                    except (jsonpointer.JsonPointerException, KeyError):
                        continue

                    # We need to save resolved value in both arguments and
                    # kwargs mappings, because the former is used to *validate*
                    # passed arguments, and the latter to supply a value from a
                    # fallback.
                    arguments[param] = kwargs[param] = value

            if self._jsonschema:
                try:
                    format_checker = jsonschema.FormatChecker()

                    @format_checker.checks("encoding", (LookupError,))
                    def is_encoding(value):
                        if isinstance(value, str):
                            import codecs

                            return codecs.lookup(value)

                    @format_checker.checks("timezone", ())
                    def is_timezone(value):
                        if isinstance(value, str):
                            import dateutil.tz

                            return dateutil.tz.gettz(value)

                    @format_checker.checks("path", (TypeError,))
                    def is_path(value):
                        if isinstance(value, str):
                            import pathlib

                            return pathlib.Path(value)

                    jsonschema.validate(
                        arguments,
                        self._jsonschema,
                        format_checker=format_checker,
                    )
                except jsonschema.exceptions.ValidationError as exc:
                    message = exc.message

                    if exc.absolute_path:
                        message = (
                            f"{'.'.join(exc.absolute_path)}: {exc.message}"
                        )

                    raise ValueError(message)

            return fn(app, *args, **kwargs)

        return wrapper
