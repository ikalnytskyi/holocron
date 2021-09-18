"""Render items using Jinja2 template engine."""

import pathlib

import jinja2
import jsonpointer

from .. import source
from .._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "template": {"type": "string"},
            "context": {"type": "object"},
            "themes": {"type": "array", "items": {"type": "string"}},
        },
    }
)
def process(app, stream, *, template="item.j2", context=None, themes=None):
    # Because it is easier to write themes if we assume that 'theme' variable
    # is always defined in context of template, let's ensure it is always
    # defined indeed. Frankly, I'm not exactly sure about this line and it may
    # change in the future.
    context = context or {}
    context.setdefault("theme", {})

    if themes is None:
        themes = [str(pathlib.Path(__file__).parent / "theme")]

    env = jinja2.Environment(
        loader=jinja2.ChoiceLoader(
            [
                jinja2.FileSystemLoader(str(pathlib.Path(theme, "templates")))
                for theme in themes
            ]
        )
    )
    env.filters["jsonpointer"] = jsonpointer.resolve_pointer

    for item in stream:
        render = env.get_template(item.get("template", template)).render
        item["content"] = render(item=item, metadata=app.metadata, **context)
        yield item

    # Themes may optionally come with various statics (e.g. css, images) they
    # depend on. That's why we need to inject these statics to the stream;
    # otherwise, rendered items may look improperly.
    for theme in themes:
        yield from source.process(app, [], path=theme, pattern=r"static/")
