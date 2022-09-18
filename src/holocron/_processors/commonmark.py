"""Convert CommonMark into HTML."""

import json
import logging
import pathlib

import markdown_it
import markdown_it.renderer
import markdown_it.token
import pygments
import pygments.formatters.html
import pygments.lexers
import pygments.util
import pygraphviz
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin

import holocron

from ._misc import parameters

_LOGGER = logging.getLogger("holocron")


class HolocronRendererHTML(markdown_it.renderer.RendererHTML):
    def __init__(self, parser):
        super().__init__(parser)
        self._parser = parser

    def fence(self, tokens, idx, options, env):
        token = tokens[idx]
        match token.info.split(maxsplit=1):
            case ["dot", params]:
                env.setdefault("diagrams", [])
                params = json.loads(params)
                diagram_name = f"diagram-{len(env['diagrams'])}.svg"
                diagram_data = pygraphviz.AGraph(token.content).draw(
                    format=params["format"],
                    prog=params.get("engine", "dot"),
                )
                env["diagrams"].append((diagram_name, diagram_data))
                return self._parser.render(f"![]({diagram_name})")
        return super().fence(tokens, idx, options, env)


def _pygmentize(code: str, language: str, _: str) -> str:
    if not language:
        return code

    try:
        formatter = _pygmentize.formatter
    except AttributeError:
        formatter = pygments.formatters.html.HtmlFormatter(nowrap=True)
        _pygmentize.formatter = formatter

    try:
        lexer = pygments.lexers.get_lexer_by_name(language)
    except pygments.util.ClassNotFound:
        _LOGGER.warning("pygmentize: no such langauge: '%s'", language)
        return code

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
    commonmark = markdown_it.MarkdownIt(renderer_cls=HolocronRendererHTML)

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

        for diagram_name, diagram_bytes in env.get("diagrams", []):
            yield holocron.WebSiteItem(
                {
                    "source": pathlib.Path("dot://", str(item["source"]), diagram_name),
                    "destination": item["destination"].with_name(diagram_name),
                    "baseurl": app.metadata["url"],
                    "content": diagram_bytes,
                }
            )
