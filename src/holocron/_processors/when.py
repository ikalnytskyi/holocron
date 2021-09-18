"""Pass a stream item to a processor based on condition."""

import collections
import pathlib
import re

import jinja2

from ._misc import parameters


def _re_match(value, pattern, flags=0):
    # If a regular expression is used agains a Python's path class, we can cast
    # the path object to string for user, because it's a behaviour a user would
    # expect anyway.
    if isinstance(value, pathlib.PurePath):
        value = str(value)
    return re.match(pattern, value, flags)


class _ConditionEvaluator:
    """Evaluate a python-like expressions in boolean context."""

    def __init__(self):
        # When processor requires some means to evaluate string conditions.
        # Turns out there're not so many simple and safe solutions, so we
        # decided to go same approach Ansible went and use Jinja2 to evaluate
        # expressions. It's safe, fast, extensible, and we already have
        # dependency on Jinja2.
        self._env = jinja2.Environment()
        self._env.filters.update({"match": _re_match})

    def eval(self, cond, **context):
        template = self._env.from_string(f"{{% if {cond} %}}true{{% endif %}}")
        return template.render(**context) == "true"


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "condition": {"type": "array", "items": {"type": "string"}},
            "processor": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "args": {"type": ["object", "array"]},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    }
)
def process(app, stream, processor, *_condition, condition=None):
    untouched = collections.deque()
    evaluator = _ConditionEvaluator()

    # Since Holocron's processor wrappers support both positional and keyword
    # arguments interface, we want to receive conditions either via positional
    # or keyword arguments, but not both simultaneously.
    condition = _condition or condition

    if not condition:
        raise TypeError("missing argument or value: 'condition'")

    def smartstream():
        for item in stream:
            if all(evaluator.eval(cond, item=item) for cond in condition):
                yield item
            else:
                untouched.append(item)

    for item in app.invoke([processor], smartstream()):
        # Some untouched items may be collected during an attempt to retrieve
        # at least one item from a processor. In order to preserve relative
        # order between items from an original input stream and items produced
        # by a processor, we need to yield these untouched items first.
        while untouched:
            yield untouched.popleft()
        yield item

    # Untouched collection may contain some items if app.invoke() drained
    # an input stream without yielding a new item. Ensure they are propagated
    # down the stream.
    yield from untouched
