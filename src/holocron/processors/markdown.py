"""Convert Markdown into HTML."""

import os
import re

import markdown

from ._misc import parameters


_top_heading_re = re.compile(
    (
        # Ignore optional newlines at the beginning of content, as well as
        # ignore character '#' preceded before heading if any.
        r"\n*#?"

        # Capture heading text regardless of which syntax is used, in other
        # words capture either text after '#' or text underlined with '='
        # at the beginning of contnet.
        r"(?P<heading>(?<=#)[^\n#]+|[^\n]+(?=\n=))"

        # Ignore underline of '=' if corresponding syntax for heading is
        # used, so it won't be matched by ANY pattern of content below.
        r"(?:\n=+)?"

        r"\s*(?P<content>.*)"
    ),
    re.DOTALL)


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "extensions": {
                "type": "object",
                "propertyNames": {
                    "pattern": r"^markdown\.extensions\..*",
                },
            },
        },
    },
)
def process(app, stream, *, extensions=None):
    markdown_ = markdown.Markdown(
        # No one use pure Markdown nowadays, so let's enhance it with some
        # popular and widely used extensions such as tables, footnotes and
        # syntax highlighting.
        extensions=list(extensions.keys()) if extensions is not None else [
            "markdown.extensions.codehilite",
            "markdown.extensions.extra",
        ],
        extension_configs=extensions if extensions is not None else {
            "markdown.extensions.codehilite": {
                # codehilite extension sets its own css class for pygmentized
                # code blocks; in order to be compatible with other markup
                # processors, let's use default class name by default
                "css_class": "highlight",
            },
        })

    for item in stream:
        match = _top_heading_re.match(item["content"])
        if match:
            title = match.group("heading").strip()
            item["content"] = match.group("content").strip()

            # Usually converters go after frontmatter processor and that means
            # any explicitly specified attribute is already set on the item.
            # Since frontmatter processor is considered to have a higher
            # priority, let's set 'title' iff it's not set.
            item["title"] = item.get("title", title)

        item["content"] = markdown_.convert(item["content"])
        item["destination"] = \
            "%s.html" % os.path.splitext(item["destination"])[0]

        yield item
