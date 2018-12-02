"""Find documents and add them to pipeline."""

import re
import os
import datetime
import codecs

import dateutil.tz
import schema

from holocron import content
from ._misc import iterdocuments, parameters


@parameters(
    schema={
        'path': str,
        'when': schema.Or([{str: object}], None, error='unsupported value'),
        'encoding': schema.Schema(codecs.lookup, 'unsupported encoding'),
        'timezone': schema.Schema(dateutil.tz.gettz, 'unsupported timezone'),
    }
)
def process(app,
            documents,
            *,
            path='.',
            when=None,
            encoding='UTF-8',
            timezone='UTC'):
    tzinfo = dateutil.tz.gettz(timezone)
    documents.extend(
        iterdocuments(_finddocuments(app, path, encoding, tzinfo), when))
    return documents


def _finddocuments(app, path, encoding, tzinfo):
    for root, dirnames, filenames in os.walk(path, topdown=True):
        for filename in filenames:
            yield _createdocument(
                app,
                os.path.join(root, filename),
                basepath=path,
                encoding=encoding,
                tzinfo=tzinfo)


def _createdocument(app, path, basepath, encoding, tzinfo):
    source = os.path.relpath(path, basepath)
    document = _getinstance(source, app)

    # A path to an input (source) document. Despite reading its content into
    # a memory, we still want to have this attribute in order to do pattern
    # matching against it.
    document['source'] = source
    document['destination'] = source

    document['created'] = \
        datetime.datetime.fromtimestamp(os.path.getctime(path), tzinfo)
    document['updated'] = \
        datetime.datetime.fromtimestamp(os.path.getmtime(path), tzinfo)

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
