"""Find stream and add them to pipeline."""

import re
import os
import datetime
import codecs

import dateutil.tz
import schema

from holocron import content
from ._misc import parameters


@parameters(
    fallback={
        'encoding': 'metadata://#/encoding',
        'timezone': 'metadata://#/timezone',
    },
    schema={
        'path': str,
        'pattern': str,
        'encoding': schema.Schema(codecs.lookup, 'unsupported encoding'),
        'timezone': schema.Schema(dateutil.tz.gettz, 'unsupported timezone'),
    }
)
def process(app,
            stream,
            *,
            path='.',
            pattern=None,
            encoding='UTF-8',
            timezone='UTC'):
    tzinfo = dateutil.tz.gettz(timezone)

    yield from stream
    yield from _finditems(app, path, pattern, encoding, tzinfo)


def _finditems(app, path, pattern, encoding, tzinfo):
    if pattern:
        re_name = re.compile(pattern)

    for root, dirnames, filenames in os.walk(path, topdown=True):
        for filename in filenames:
            source = os.path.relpath(os.path.join(root, filename), path)

            if pattern and not re_name.match(source):
                continue

            yield _createitem(
                app,
                os.path.join(root, filename),
                basepath=path,
                encoding=encoding,
                tzinfo=tzinfo)


def _createitem(app, path, basepath, encoding, tzinfo):
    source = os.path.relpath(path, basepath)
    item = _getinstance(source, app)

    # A path to an input (source) item. Despite reading its content into
    # a memory, we still want to have this attribute in order to do pattern
    # matching against it.
    item['source'] = source
    item['destination'] = source

    item['created'] = \
        datetime.datetime.fromtimestamp(os.path.getctime(path), tzinfo)
    item['updated'] = \
        datetime.datetime.fromtimestamp(os.path.getmtime(path), tzinfo)

    try:
        with open(path, 'rt', encoding=encoding) as f:
            item['content'] = f.read()
    except UnicodeDecodeError:
        with open(path, 'rb') as f:
            item['content'] = f.read()

    return item


def _getinstance(filename, app):
    post_pattern = re.compile(r'^\d{2,4}/\d{1,2}/\d{1,2}')

    # Extract 'published' date out of item path.
    published = None
    if post_pattern.search(filename):
        published = ''.join(
            post_pattern.search(filename).group(0).split(os.sep)[:3])
        published = datetime.datetime.strptime(published, '%Y%m%d')

    _, ext = os.path.splitext(filename)

    item = content.Document(app)
    if published:
        item['published'] = published.date()
    return item
