"""Generate tags page."""

import collections
import schema

from ._misc import iterdocuments, parameters
from holocron import content


@parameters(
    schema={
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'template': schema.Schema(str),
        'output': schema.Schema(str),
    }
)
def process(app,
            documents,
            *,
            when=None,
            template='index.j2',
            output='tags/{tag}.html'):
    app.metadata['show_tags'] = True

    # map: tag -> [posts]
    tags = collections.defaultdict(list)

    for post in iterdocuments(documents, when):
        if 'tags' in post:
            tag_objects = []
            for tag in post['tags']:
                tags[tag].append(post)
                tag_objects.append(_Tag(tag, output))
            post['tags'] = tag_objects

    inserted = []

    for tag in sorted(tags):
        tag_doc = content.Document(app)
        tag_doc['source'] = 'virtual://tags/%s' % tag
        tag_doc['destination'] = output.format(tag=tag)
        tag_doc['template'] = template
        tag_doc['documents'] = tags[tag]
        inserted.append(tag_doc)

    return documents + inserted


class _Tag:
    def __init__(self, name, output):
        self.name = name
        self.url = '/{0}/'.format(
            output.format(tag=name).lstrip('/').rstrip('/'))
