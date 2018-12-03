"""Generate index page."""

import codecs
import schema

from ._misc import iterdocuments, parameters
from holocron.content import Document


@parameters(
    fallback={
        'encoding': ':metadata:#/encoding',
    },
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'template': schema.Schema(str),
        'encoding': schema.Schema(codecs.lookup, 'unsupported encoding'),
    }
)
def process(app,
            documents,
            *,
            when=None,
            template='index.j2',
            encoding='UTF-8'):
    selected = iterdocuments(documents, when)
    template = app.jinja_env.get_template(template)

    content = template.render(posts=selected, encoding=encoding)

    index = Document(app)
    index['source'] = 'virtual://index'
    index['destination'] = 'index.html'
    index['content'] = content.encode(encoding)
    index['encoding'] = encoding

    return documents + [index]
