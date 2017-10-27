"""Find documents and add them to pipeline."""

import re
import os
import datetime

from dooku.datetime import UTC, Local

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

    document['created_local'] = document['created'].astimezone(Local)
    document['updated_local'] = document['updated'].astimezone(Local)

    try:
        with open(path, 'rt', encoding=encoding) as f:
            document['content'] = f.read()
    except UnicodeDecodeError:
        with open(path, 'rb') as f:
            document['content'] = f.read()

    return document


def _getinstance(filename, app):
    # this function is temporary

    # regex pattern for separating posts from pages
    _post_pattern = re.compile(r'^\d{2,4}/\d{1,2}/\d{1,2}')

    # let's assume that if we have a converter for a given file
    # then it's either a post or a page
    _, ext = os.path.splitext(filename)
    if ext in app._converters:
        # by Holocron convention, post is a convertible document that
        # has the following format YEAR/MONTH/DAY in its path
        content_path = os.path.abspath(app.conf['paths.content'])
        document_path = os.path.abspath(filename)[len(content_path) + 1:]
        if _post_pattern.search(document_path):
            post = content.Post(app)

            # Temporary solution to make documents as abstract as possible.
            # As we move towards, this is going to be removed.
            published = ''.join(
                _post_pattern.search(document_path).group(0).split(os.sep)[:3])
            published = datetime.datetime.strptime(published, '%Y%m%d')
            post['published'] = published.date()

            return post

        return content.Page(app)
    return content.Document(app)
