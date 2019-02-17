"""Render stream using Jinja2 template engine."""

import os

import jinja2
import jsonpointer
import schema

from . import source
from ._misc import parameters


@parameters(
    schema={
        "template": schema.Schema(str),
        "context": schema.Or({str: object}, error="must be a dict"),
        "themes": schema.Or([str], None, error="unsupported value"),
    }
)
def process(app, stream, *, template="item.j2", context={}, themes=None):
    if themes is None:
        import holocron
        themes = [os.path.join(os.path.dirname(holocron.__file__), "theme")]

    env = jinja2.Environment(loader=jinja2.ChoiceLoader([
        # Jinja2 processor may receive a list of themes, and we want to look
        # for templates in passed order. The rationale here is to provide
        # a way to override templates or populate a list of supported ones.
        jinja2.FileSystemLoader(os.path.join(theme, "templates"))
        for theme in themes
    ]))
    env.filters["jsonpointer"] = jsonpointer.resolve_pointer

    for item in stream:
        item["content"] = \
            env.get_template(item.get("template", template)).render(
                document=item,
                metadata=app.metadata,
                **context)
        yield item

    # Themes may optionally come with various statics (e.g. css, images) they
    # depend on. That's why we need to inject these statics to the stream;
    # otherwise, rendered items may look improperly.
    for theme in themes:
        yield from source.process(app, [], path=theme, pattern=r"static/")
