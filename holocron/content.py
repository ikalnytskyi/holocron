"""
    holocron.content
    ~~~~~~~~~~~~~~~~

    This module contains models for all content types supported by Holocron.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import re
import abc
import shutil
import logging
import datetime

import yaml

from dooku.datetime import UTC, Local
from dooku.decorator import cached_property

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

    # let's assume that if we have a converter for a given file
    # then it's either a post or a page
    _, ext = os.path.splitext(filename)
    if ext in app._converters:
        # by Holocron convention, post is a convertible document that
        # has the following format YEAR/MONTH/DAY in its path
        content_path = os.path.abspath(app.conf['paths.content'])
        document_path = os.path.abspath(filename)[len(content_path) + 1:]
        if _post_pattern.search(document_path):
            return Post(filename, app)
        return Page(filename, app)
    return Static(filename, app)


class Document(metaclass=abc.ABCMeta):
    """
    An abstract base class for Holocron documents.

    It provides a *document* interface and implements common stuff.

    :param filename: a path to physical file
    :param app: a reference to the application it's attached to
    """

    def __init__(self, filename, app):
        logger.info(
            '%s: creating %s', filename, self.__class__.__name__.lower())
        self._app = app

        #: an absolute path to the source document
        self.source = os.path.abspath(filename)

        #: a path to the source document relative to the content folder
        self.short_source = self.source[
            len(os.path.abspath(self._app.conf['paths.content'])) + 1:]

        #: a created date in UTC as :class:`datetime.datetime` object
        self.created = datetime.datetime.fromtimestamp(
            os.path.getctime(self.source), UTC)
        self.created_local = self.created.astimezone(Local)

        #: an updated date in UTC as :class:`datetime.datetime` object
        self.updated = datetime.datetime.fromtimestamp(
            os.path.getmtime(self.source), UTC)
        self.updated_local = self.updated.astimezone(Local)

        #: an absolute url to the built document
        self.abs_url = self._app.conf['site.url'] + self.url

    @abc.abstractmethod
    def build(self):
        """
        Builds a current document object.
        """

    @property
    @abc.abstractmethod
    def url(self):
        """
        Returns a URL to the resource this object represents.
        """


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

    #: A regex for splitting page header and page content.
    _re_extract_header = re.compile('(---\s*\n.*?\n)---\s*\n(.*)', re.M | re.S)

    #: A default template for page documents.
    template = 'page.html'

    #: A default title for page documents.
    title = 'Untitled'

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)

        # set default author (if none was specified in the document)
        self.author = self._app.conf['site.author']

        # set extracted information and override default one
        meta = self._parse_document()
        for key, value in meta.items():
            setattr(self, key, value)

    def _parse_document(self):
        """
        Parses a given document and returns result

        :returns: a dictionary with parsed information
        """
        encoding = self._app.conf['encoding.content']
        with open(self.source, encoding=encoding) as f:
            headers = {}
            content = f.read()

            # parse yaml header if exists
            match = self._re_extract_header.match(content)
            if match:
                headers, content = match.groups()
                headers = yaml.safe_load(headers)

            # get converter for building a given document
            converter = self._app._converters[os.path.splitext(self.source)[1]]
            # convert markup to html, extracting some meta
            metadata, html = converter.to_html(content)
            metadata['content'] = html
            # override extracted meta information with document's headers
            metadata.update(headers)
        return metadata

    def build(self):
        filename, _ = os.path.splitext(self.short_source)
        destination = os.path.join(
            self._app.conf['paths.output'], filename, 'index.html')
        mkdir(os.path.dirname(destination))

        template = self._app.jinja_env.get_template(self.template)
        encoding = self._app.conf['encoding.output']

        with open(destination, 'w', encoding=encoding) as f:
            f.write(template.render(document=self))

    @cached_property
    def url(self):
        filename, _ = os.path.splitext(self.short_source)
        return '/' + filename + '/'


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
    template = 'post.html'

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)

        published = ''.join(self.short_source.split(os.sep)[:3])
        published = datetime.datetime.strptime(published, '%Y%m%d')

        self.published = published.replace(tzinfo=Local)


class Static(Document):
    """
    A Static document implementation and representation.

    Just copy "As Is" from the content directory to the output directory.
    Here's an example of building basics:

      ===================  ===================  ===================
          Content Dir           Output Dir              URL
      ===================  ===================  ===================
         /about/me.png        /about/me.png        /about/me.png
      ===================  ===================  ===================

    """

    @cached_property
    def url(self):
        # A URL to the static document is the same as a path to this file.
        # There is only one note: the path to this file should be relative
        # to the content/output directory.
        return '/' + self.short_source

    def build(self):
        destination = os.path.join(
            self._app.conf['paths.output'], self.short_source)

        mkdir(os.path.dirname(destination))
        shutil.copy(self.source, destination)
