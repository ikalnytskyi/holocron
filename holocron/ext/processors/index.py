"""Generate index page."""

from ._misc import iterdocuments
from holocron import content


def process(app, documents, **options):
    when = options.pop('when', None)
    template = options.pop('template', 'index.j2')
    encoding = options.pop('encoding', 'utf-8')

    selected = iterdocuments(documents, when)
    template = app.jinja_env.get_template(template)

    index = content.Document(app)
    index['source'] = 'virtual://index'
    index['destination'] = 'index.html'
    index['content'] = template.render(posts=selected, encoding=encoding)
    index['encoding'] = encoding

    return documents + [index]
