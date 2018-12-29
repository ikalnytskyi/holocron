"""Render documents using Jinja2 template engine."""

import os

import jinja2
import jsonpointer
import schema

from . import source
from ._misc import iterdocuments_ex, parameters


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'template': schema.Schema(str),
        'themes': schema.Or([str], None, error='unsupported value'),
        'context': schema.Or({str: object}, error='must be a dict'),
    }
)
def process(app,
            documents,
            *,
            template='page.j2',
            themes=None,
            context={},
            when=None):
    if themes is None:
        import holocron
        themes = [os.path.join(os.path.dirname(holocron.__file__), 'theme')]

    env = jinja2.Environment(loader=jinja2.ChoiceLoader([
        # Jinja2 processor may receive a list of themes, and we want to look
        # for templates in passed order. The rationale here is to provide
        # a way to override templates or extend existing ones.
        jinja2.FileSystemLoader(os.path.join(theme, 'templates'))
        for theme in themes
    ]))
    env.filters['jsonpointer'] = jsonpointer.resolve_pointer

    for document, is_matched in iterdocuments_ex(documents, when):
        if is_matched:
            document['content'] = \
                env.get_template(document.get('template', template)).render(
                    document=document,
                    metadata=app.metadata,
                    **context)
        yield document

    # Themes may optionally come with various statics (e.g. css, images) they
    # depend on. That's why we need to inject these statics to a documents
    # pipeline; otherwise rendered documents may look improperly.
    for theme in themes:
        yield from source.process(app, [], path=theme, when=[{
            'operator': 'match',
            'attribute': 'source',
            'pattern': r'^static/',
        }])
