"""Find documents and add them to pipeline."""

import re
import os
import datetime

from dooku.datetime import UTC

from holocron import content
from ._misc import iterdocuments


def process(app, documents, **options):
    path = options.pop('path', '.')
    when = options.pop('when', None)
    encoding = options.pop('encoding', 'utf-8')

    documents.extend(iterdocuments(_finddocuments(app, path, encoding), when))
    return documents


def _finddocuments(app, path, encoding):
    for root, dirnames, filenames in os.walk(path, topdown=True):
        for filename in filenames:
            yield _createdocument(
                app,
                os.path.join(root, filename),
                basepath=path,
                encoding=encoding)


def _createdocument(app, path, basepath, encoding):
    source = os.path.relpath(path, basepath)
    document = _getinstance(source, app)

    # A path to an input (source) document. Despite reading its content into
    # a memory, we still want to have this attribute in order to do pattern
    # matching against it.
    document['source'] = source
    document['destination'] = source

    document['created'] = \
        datetime.datetime.fromtimestamp(os.path.getctime(path), UTC)
    document['updated'] = \
        datetime.datetime.fromtimestamp(os.path.getmtime(path), UTC)

    try:
        with open(path, 'rt', encoding=encoding) as f:
            document['content'] = f.read()
    except UnicodeDecodeError:
        with open(path, 'rb') as f:
            document['content'] = f.read()

    return document


def _getinstance(filename, app):
    post_pattern = re.compile(r'^\d{2,4}/\d{1,2}/\d{1,2}')

    # Extract 'published' date out of document path.
    published = None
    if post_pattern.search(filename):
        published = ''.join(
            post_pattern.search(filename).group(0).split(os.sep)[:3])
        published = datetime.datetime.strptime(published, '%Y%m%d')

    _, ext = os.path.splitext(filename)

    document = content.Document(app)
    if published:
        document['published'] = published.date()
    return document
