"""
    holocron.content
    ~~~~~~~~~~~~~~~~

    This module contains models for all content types supported by Holocron.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import re
import logging
import datetime

from dooku.datetime import UTC, Local

from .utils import mkdir


logger = logging.getLogger(__name__)


def create_document(filename, app):
    """
    Creates and returns a concrete :class:`Document` instance.

    Here's some rules which describe how the factory is working:

    #. There are two document types: convertible and static.
    #. Convertible document is a document that could be converted by one of
       registered converters. Otherwise - it's a static document.
    #. If a document has year, month and day in its path then it's a post.
       Otherwise - it's a page.

       (e.g. 2014/12/24/test.mdown is a post, when talks/test.mdown is a page)

    :param filename: a path to physical file
    :param app: a reference to the application it's attached to
    """
    #: regex pattern for separating posts from pages
    _post_pattern = re.compile(r'^\d{2,4}/\d{1,2}/\d{1,2}')

    with open(filename, 'rb') as f:
        content = f.read()

    # let's assume that if we have a converter for a given file
    # then it's either a post or a page
    _, ext = os.path.splitext(filename)
    if ext in app._converters:
        # by Holocron convention, post is a convertible document that
        # has the following format YEAR/MONTH/DAY in its path
        content_path = os.path.abspath(app.conf['paths.content'])
        document_path = os.path.abspath(filename)[len(content_path) + 1:]
        if _post_pattern.search(document_path):
            post = Post(filename, app, content)

            # Temporary solution to make documents as abstract as possible.
            # As we move towards, this is going to be removed.
            published = ''.join(
                _post_pattern.search(document_path).group(0).split(os.sep)[:3])
            published = datetime.datetime.strptime(published, '%Y%m%d')
            post.published = published.replace(tzinfo=Local)

            return post

        return Page(filename, app, content)
    return Document(filename, app, content)


def make_document(document, app):
    # This function is intermediate step required to incrementally implement
    # processors pipeline.

    if isinstance(document, Page):
        template = app.jinja_env.get_template(document.template)
        document.content = template.render(document=document)

    mkdir(os.path.dirname(document.destination))

    if isinstance(document.content, str):
        output = open(
            document.destination, 'wt', encoding=app.conf['encoding.output'])
    else:
        output = open(document.destination, 'wb')

    with output:
        output.write(document.content)


class Document:
    """
    An abstract base class for Holocron documents.

    It provides a *document* interface and implements common stuff.

    :param filename: a path to physical file
    :param app: a reference to the application it's attached to
    """

    def __init__(self, filename, app, content=b''):
        logger.info(
            '%s: creating %s', filename, self.__class__.__name__.lower())
        self._app = app

        #: an absolute path to the source document
        self.source = os.path.abspath(filename)

        #: bytes or string with file content
        self.content = content

        #: an absolute destination path
        self.destination = os.path.join(
            os.path.abspath(app.conf['paths.output']),
            self.source[
                len(os.path.abspath(self._app.conf['paths.content'])) + 1:])

        #: a created date in UTC as :class:`datetime.datetime` object
        self.created = datetime.datetime.fromtimestamp(
            os.path.getctime(self.source), UTC)
        self.created_local = self.created.astimezone(Local)

        #: an updated date in UTC as :class:`datetime.datetime` object
        self.updated = datetime.datetime.fromtimestamp(
            os.path.getmtime(self.source), UTC)
        self.updated_local = self.updated.astimezone(Local)

    @property
    def url(self):
        destination = self.destination[
            len(os.path.abspath(self._app.conf['paths.output'])) + 1:]

        # Most modern HTTP servers implicitly serve these files when
        # someone requested URL that points to directory. It's a
        # common practice to do not end URLs with those filenames as
        # they are assumed by default.
        if os.path.basename(destination) in ('index.html', 'index.htm'):
            destination = os.path.dirname(destination) + '/'

        return '/' + destination

    @property
    def abs_url(self):
        return self._app.conf['site.url'] + self.url


class Page(Document):
    """
    A Page document implementation and representation.

    The Page document is a kind of Holocron's documents that converts some
    markuped text document (e.g. markdown, restructuredtext) into HTML. The
    conversion process is complex and includes both YAML-header parsing and
    searching for valuable information in the content body (e.g. title).

    The resulted HTML will be saved as ``{filename}/index.html``, preserving
    the filesystem structure of the content directory. Here's an example of
    conversion basics:

      ===================  ========================  ==============
          Content Dir             Output Dir              URL
      ===================  ========================  ==============
        /about/cv.mdown      /about/cv/index.html     /about/cv/
      ===================  ========================  ==============

    """

    #: A default template for page documents.
    template = 'page.j2'

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)

        self.destination = os.path.join(
            os.path.abspath(self._app.conf['paths.output']),
            os.path.splitext(
                self.source[
                    len(os.path.abspath(self._app.conf['paths.content'])) + 1:
                ])[0],
            'index.html')

        self.author = self._app.conf['site.author']
        self.content = self.content.decode(self._app.conf['encoding.content'])


class Post(Page):
    """
    A Post document implementation and representation.

    To be honest, a Post document is almost same as Page document. There
    are a lot of common things, that's why the Post inherits the Page.

    Still, we need to separate those two models, because, for instance, only
    posts should be used by feed generator. Looking forward we see many
    similar pitfalls.

    So how the Holocron decides whether it's a post or a page? Simple.
    If a path to the document represents a date - ``/2015/01/04/`` - and
    there's a converter for this document, the document is a post.
    """

    #: We're using a separate template, since unlike a page we need to show
    #: post's author, published date and a list of tags.
    template = 'post.j2'
