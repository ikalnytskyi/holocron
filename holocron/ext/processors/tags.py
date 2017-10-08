"""Generate tags page."""

import collections

from ._misc import iterdocuments
from holocron import content


def process(app, documents, **options):
    when = options.pop('when', None)
    template = options.pop('template', 'index.j2')
    output = options.pop('output', 'tags/{tag}.html')

    app.add_theme_ctx(show_tags=True)

    # map: tag -> [posts]
    tags = collections.defaultdict(list)

    for post in iterdocuments(documents, when):
        if hasattr(post, 'tags'):
            tag_objects = []
            for tag in post.tags:
                tags[tag].append(post)
                tag_objects.append(_Tag(tag, output))
            post.tags = tag_objects

    template = app.jinja_env.get_template(template)
    inserted = []

    for tag in sorted(tags):
        tag_doc = content.Document(app)
        tag_doc.content = template.render(posts=tags[tag])
        tag_doc.source = 'virtual://tags/%s' % tag
        tag_doc.destination = output.format(tag=tag)
        inserted.append(tag_doc)

    return documents + inserted


class _Tag:
    def __init__(self, name, output):
        self.name = name
        self.url = '/{0}/'.format(
            output.format(tag=name).lstrip('/').rstrip('/'))
