"""Unload pipeline by committing documents."""

import os

from ._misc import iterdocuments


def process(app, documents, **options):
    path = options.pop('path', '_site')
    when = options.pop('when', None)
    unload = options.pop('unload', True)
    encoding = options.pop('encoding', 'UTF-8')

    to_remove = []

    for document in iterdocuments(list(documents), when):
        to_remove.append(document)

        destination = os.path.join(path, document['destination'])
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        # Once Jinja2 is a standalone processor, these lines will be gone.
        if 'template' in document:
            template = app.jinja_env.get_template(document['template'])
            document['content'] = template.render(document=document)

        if isinstance(document['content'], str):
            # A document may suggest its own encoding as it might be pretty
            # important to have this one. One of such examples is sitemap.xml
            # which must be a UTF-8 encoded by design.
            enc = document.get('encoding', encoding)
            output = open(destination, 'wt', encoding=enc)
        else:
            output = open(destination, 'wb')

        with output:
            output.write(document['content'])

    if unload:
        for document in to_remove:
            documents.remove(document)

    return documents
