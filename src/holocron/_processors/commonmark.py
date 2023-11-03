"""Convert CommonMark into HTML."""

import json
import logging
import subprocess
import typing as t

import markdown_it
import markdown_it.renderer
import markdown_it.token
import pygments
import pygments.formatters.html
import pygments.lexers
import pygments.util
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin

from ._misc import parameters

_LOGGER = logging.getLogger("holocron")


class HolocronRendererHTML(markdown_it.renderer.RendererHTML):
    def __init__(self, parser):
        super().__init__(parser)
        self._parser = parser

    def fence(self, tokens, idx, options, env) -> str:
        token = tokens[idx]

        match token.info.split(maxsplit=1):
            case [_, params]:
                params = json.loads(params)
                if "exec" in params:
                    standard_input = token.content.encode("UTF-8")
                    standard_output = _exec_pipe(params["exec"], standard_input)
                    return standard_output.decode("UTF-8")

        return super().fence(tokens, idx, options, env)


def _exec_pipe(args: t.List[str], input_: t.ByteString, timeout: int = 1000) -> bytes:
    try:
        completed_process = subprocess.run(
            args,
            input=input_,
            capture_output=True,
            timeout=timeout,
            check=True,
        )
    except subprocess.TimeoutExpired:
        return b"timed out executing the command"
    except subprocess.CalledProcessError as exc:
        return exc.stderr
    return completed_process.stdout


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
