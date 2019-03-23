"""Convert CommonMark into HTML."""

import os
import io
import logging

import mistletoe
import pygments
import pygments.formatters.html
import pygments.lexers
import pygments.util

from ._misc import parameters


_logger = logging.getLogger("holocron")


def _pygmentize(code, language):
    try:
        formatter = _pygmentize.formatter
    except AttributeError:
        formatter = _pygmentize.formatter = \
            pygments.formatters.html.HtmlFormatter()

    lexer = pygments.lexers.get_lexer_by_name(language)
    return pygments.highlight(code, lexer, formatter)


class _HTMLRenderer(mistletoe.HTMLRenderer):

    def __init__(self, *extras, pygmentize):
        super(_HTMLRenderer, self).__init__(*extras)
        self._pygmentize = pygmentize
        self._extract_title = True
        self.extracted = {}

    def render_document(self, token):
        if self._extract_title and token.children:
            node = token.children[0]
            is_heading = node.__class__.__name__ in (
                "Heading",
                "SetextHeading",
            )
            if is_heading and node.level == 1:
                self.extracted["title"] = self.render_inner(node)
                token.children.pop(0)
        return super(_HTMLRenderer, self).render_document(token)

    def render_block_code(self, token):
        if token.language and self._pygmentize:
            try:
                code = token.children[0].content
                return self._pygmentize(code, token.language)
            except pygments.util.ClassNotFound:
                _logger.warning(
                    "pygmentize: no such langauge: '%s'", token.language)
        return super(_HTMLRenderer, self).render_block_code(token)


@parameters(
    jsonschema={
        "type": "object",
        "properties": {
            "pygmentize": {"type": "boolean"},
        },
    },
)
def process(app, stream, *, pygmentize=False):
    pygmentize = pygmentize and _pygmentize

    for item in stream:
        renderer = _HTMLRenderer(pygmentize=pygmentize)

        with renderer:
            item["content"] = renderer.render(
                mistletoe.Document(io.StringIO(item["content"]))).strip()

        if "title" in renderer.extracted:
            item["title"] = item.get("title", renderer.extracted["title"])

        item["destination"] = \
            "%s.html" % os.path.splitext(item["destination"])[0]

        yield item
