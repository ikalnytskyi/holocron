"""Pass a stream item to a processor based on condition."""

import re
import collections

import jinja2


def _re_match(value, pattern, flags=0):
    return re.match(pattern, value, flags)


class _WhenEvaluator:
    """Evaluate a python-like expression using Jinja2 syntax.

    When processor requires some means to evaluate string conditions. Turns
    out there're not so many simple and safe solutions, so we decided to go
    same approach Ansible went and use Jinja2 to evaluate expressions. It's
    safe, fast, extensible, and we already have dependency on Jinja2.
    """

    def __init__(self):
        self._env = jinja2.Environment()
        self._env.filters.update({"match": _re_match})

    def eval(self, when, **context):
        template = self._env.from_string(
            "{%% if %s %%}true{%% endif %%}" % when)
        return template.render(**context) == "true"


def process(app, stream, *, when, processor):
    untouched = collections.deque()
    evaluator = _WhenEvaluator()

    def smartstream():
        for item in stream:
            if all(evaluator.eval(cond, item=item) for cond in when):
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
