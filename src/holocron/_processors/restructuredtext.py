"""Convert reStructuredText into HTML."""

from docutils import nodes
from docutils.core import publish_parts
from docutils.writers import html5_polyglot

from ._misc import parameters


@parameters(
    jsonschema={
        "type": "object",
        "properties": {"settings": {"type": "object"}},
    }
)
def process(app, stream, *, settings=None):
    settings = dict(
        {
            # We need to start heading level with <h2> in case there are
            # few top-level sections, because it simply means there's no
            # title.
            "initial_header_level": 2,
            # Docutils is designed to convert reStructuredText files to
            # other formats such as, for instance, HTML. That's why it
            # produces full-featured HTML with embed CSS. Since we are
            # going to use our own templates we are not interested in
            # getting the whole HTML output. So let's turn off producing
            # a stylesheet and save both memory and CPU cycles.
            "embed_stylesheet": False,
            # Docutils uses Pygments to highlight code blocks, and the
            # later can produce HTML marked with either short or long
            # CSS classes. There are a lot of colorschemes designed for
            # the former notation, so it'd be better to use it in order
            # simplify customization flow.
            "syntax_highlight": "short",
        },
        **(settings or {}),
    )

    for item in stream:
        # Writer is mutable so we can't share the same instance between
        # conversions.
        writer = html5_polyglot.Writer()

        # Unfortunately we are not happy with out-of-box conversion to
        # HTML. For instance, we want to see inline code to be wrapped
        # into <code> tag rather than <span>. So we need to use custom
        # translator to fit our needs.
        writer.translator_class = _HTMLTranslator

        parts = publish_parts(item["content"], writer=writer, settings_overrides=settings)

        item["content"] = parts["fragment"].strip()
        item["destination"] = item["destination"].with_suffix(".html")

        # Usually converters go after frontmatter processor and that
        # means any explicitly specified attribute is already set on
        # the item. Since frontmatter processor is considered to
        # have a higher priority, let's set 'title' iff it does't
        # exist.
        if "title" not in item and parts.get("title"):
            item["title"] = parts["title"]

        yield item


class _HTMLTranslator(html5_polyglot.HTMLTranslator):
    """Translate reStructuredText nodes to HTML."""

    # skip <div class="section"> wrapper around sections

    def visit_section(self, node):
        self.section_level += 1

        for id_ in node.get("ids", []):
            self.body.append(f"<span id={id_}></span>")

    def depart_section(self, node):
        self.section_level -= 1

    # wrap inline code into <code> tag rather than <span>

    def visit_literal(self, node):
        self.body.extend(["<code>", node.astext(), "</code>"])

        # HTML tag has been produced. Thus, there's no need to call
        # depart_literal().
        raise nodes.SkipNode
