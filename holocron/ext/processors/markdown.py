"""Convert Markdown into HTML."""

import os
import re

import markdown

from ._misc import iterdocuments


_top_heading_re = re.compile(
    (
        # Ignore optional newlines at the beginning of content, as well as
        # ignore character '#' preceded before heading if any.
        r'\n*#?'

        # Capture heading text regardless of which syntax is used, in other
        # words capture either text after '#' or text underlined with '='
        # at the beginning of contnet.
        r'(?P<heading>(?<=#)[^\n#]+|[^\n]+(?=\n=))'

        # Ignore underline of '=' if corresponding syntax for heading is
        # used, so it won't be matched by ANY pattern of content below.
        r'(?:\n=+)?'

        r'\s*(?P<content>.*)'
    ),
    re.DOTALL)


def process(app, documents, **options):
    markdown_ = markdown.Markdown(
        # No one use pure Markdown nowadays, so let's enhance it with some
        # popular and widely used extensions such as tables, footnotes and
        # syntax highlighting.
        extensions=options.pop('extensions', [
            'markdown.extensions.codehilite',
            'markdown.extensions.extra',
        ]))
    when = options.pop('when', None)

    for document in iterdocuments(documents, when):
        # We need to strip top level heading out of the document because
        # its value is used separately in number of places.
        match = _top_heading_re.match(document.content)
        if match:
            title = match.group('heading').strip()
            document.content = match.group('content').strip()

            # Usually converters go after frontmatter processor and that
            # means any explicitly specified attribute is already set on
            # the document. Since frontmatter processor is considered to
            # have a higher priority, let's set 'title' iff it does't
            # exist.
            document.title = getattr(document, 'title', title)

        document.content = markdown_.convert(document.content)
        document.destination = \
            '%s.html' % os.path.splitext(document.destination)[0]

    return documents
