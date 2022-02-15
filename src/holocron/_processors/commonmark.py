"""Convert CommonMark into HTML."""

import logging

import markdown_it
import pygments
import pygments.formatters.html
import pygments.lexers
import pygments.util
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin

from ._misc import parameters

_LOGGER = logging.getLogger("holocron")


def _pygmentize(code, language, _):
    try:
        formatter = _pygmentize.formatter
    except AttributeError:

        class HtmlFormatter(pygments.formatters.html.HtmlFormatter):
            def wrap(self, source, _):
                # Since 'markdown-it' creates required '<pre>' & '<code>'
                # containers, there's no need to duplicate them with pygments.
                yield from source

        formatter = _pygmentize.formatter = HtmlFormatter(wrapcode=True)

    try:
        lexer = pygments.lexers.get_lexer_by_name(language)
    except pygments.util.ClassNotFound:
        _LOGGER.warning("pygmentize: no such langauge: '%s'", language)
        return None

    return pygments.highlight(code, lexer, formatter)


@parameters(
    jsonschema={
        "type": "object",
        "properties": {"pygmentize": {"type": "boolean"}},
    }
)
def process(
    app,
    stream,
    *,
    pygmentize=False,
    infer_title=False,
    strikethrough=False,
    table=False,
    footnote=False,
    admonition=False,
    definition=False,
):
    commonmark = markdown_it.MarkdownIt()

    if pygmentize:
        commonmark.options.highlight = _pygmentize
    if strikethrough:
        commonmark.enable("strikethrough")
    if table:
        commonmark.enable("table")
    if footnote:
        commonmark.use(footnote_plugin)
    if admonition:
        commonmark.use(container_plugin, "warning")
        commonmark.use(container_plugin, "note")
    if definition:
        commonmark.use(deflist_plugin)

    for item in stream:
        env = {}
        tokens = commonmark.parse(item["content"], env)

        # Here's where the commonmark processor is being "smart". If the stream
        # item doesn't have a title set and the commonmark content starts with
        # a heading, the heading is considered the item's title and is removed
        # from the content in order to avoid being rendered twice.
        if (
            infer_title
            and tokens
            and tokens[0].type == "heading_open"
            and int(tokens[0].tag[1]) == 1
            and "title" not in item
        ):
            item["title"] = tokens[1].content
            tokens = tokens[3:]

        item["content"] = commonmark.renderer.render(tokens, commonmark.options, env)
        item["destination"] = item["destination"].with_suffix(".html")
        yield item
