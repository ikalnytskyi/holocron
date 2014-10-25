# coding: utf-8
"""
    holocron.content
    ~~~~~~~~~~~~~~~~

    This module contains models for all the content types. The main idea
    is to divide the content into two parts:

    * convertible;
    * non-covertible (static).

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
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


class Document(metaclass=abc.ABCMeta):
    """
    Base document class.

    There are two document types in this hierarchy now:

    * a :class:`Convertible` document
    * a :class:`Static` document

    In addition to base class function, this class is used to creating
    a certain document class based on some input (so called factory
    constructor). For instance::

        # the doc will be either Convertible or Static
        doc = Document('/path/to/file', app)

    :param filename: a path to physical file
    :param app: a reference to the application it's attached to
    """
    def __new__(cls, filename, app):
        # converter-based decision for creating object
        _, ext = os.path.splitext(filename)
        if app._converters.get(ext) is not None:
            return super(Document, cls).__new__(Convertible)
        return super(Document, cls).__new__(Static)

    def __init__(self, filename, app):
        self.filename = os.path.abspath(filename)
        self.app = app

    def get_created_datetime(self, localtime=False):
        """
        Returns a :class:`datetime.datetime` object which represents the
        document's created date.
        """
        tz = Local if localtime else UTC
        created = os.path.getctime(self.source)
        return datetime.datetime.fromtimestamp(created, tz)

    def get_modified_datetime(self, localtime=False):
        """
        Returns a :class:`datetime.datetime` object which represents the
        document's modified date.
        """
        tz = Local if localtime else UTC
        lastmod = os.path.getmtime(self.source)
        return datetime.datetime.fromtimestamp(lastmod, tz)

    @property
    def source(self):
        """
        Returns a path to the source document.
        """
        return self.filename

    @cached_property
    def short_source(self):
        """
        Returns a short path to the source document. What is a short path?
        It's a path relative to the content directory.
        """
        path_to_content = os.path.abspath(self.app.conf['paths.content'])
        cut_length = len(path_to_content)

        # cut the path to content dir and the first slash of the following dir
        return self.filename[cut_length + 1:]

    @property
    @abc.abstractmethod
    def destination(self):
        """
        Returns a path to the destination document. The built document
        will be saved in this file.
        """

    @property
    @abc.abstractmethod
    def url(self):
        """
        Returns an URL to the resource this object represent.
        """

    @property
    @abc.abstractmethod
    def abs_url(self):
        """
        Returns an absolute URL to the resource this object represents.
        """

    @abc.abstractmethod
    def build(self):
        """
        Starts build process of the document.
        """


class Convertible(Document):
    """
    A convertible document representation.

    This type of documents is converts an input markuped document into
    an HTML document and saves the result into ``%filename%`` folder
    with ``index.html`` filename, preserving the directory structure of
    the content folder.

    For instance, a file::

        /2014/01/01/birthday.rst

    from the content folder will be converts into::

        /2014/01/01/birthday/index.html

    in the output folder.
    """

    #: A default template for convertible documents. Used if no template
    #: specified in the document metadata.
    template = 'document.html'
    default_title = 'Untitled'

    #: A regex for splitting post header and post content.
    re_extract_header = re.compile('(---\s*\n.*\n)---\s*\n(.*)', re.M | re.S)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logger.info('Found a convertible document: "%s"', self.source)

        # parse a given convertible document and save the result as attributes
        self.meta, self.html = self._parse_document(self.filename)

    def _parse_document(self, document):
        """
        Parses a given document and returns result

        :param document: a path to document
        :returns: a tuple with header and content
        """
        with open(document, encoding='utf-8') as f:
            content = f.read()

            # parse yaml header if exists
            match = self.re_extract_header.match(content)
            if match:
                header, content = match.groups()
                header = yaml.load(header)
            else:
                header = {}

            # get converter for building a given document
            converter = self.app._converters.get(
                os.path.splitext(document)[1])

            # convert markup to html, extracting some meta
            metadata, html = converter.to_html(content)

            # override extracted metainformation with document's one
            metadata.update(header)

            if 'author' not in metadata:
                metadata['author'] = self.app.conf['author']

            if 'title' not in metadata:
                metadata['title'] = self.default_title

        return metadata, html

    def get_created_datetime(self, localtime=False):
        """
        Returns a :class:`datetime.datetime` object which represents the
        document's created date.
        """
        # TODO: get created time from the folder structure
        return super(Convertible, self).get_created_datetime(localtime)

    def build(self):
        # create folder for the output file
        mkdir(os.path.dirname(self.destination))

        metadata = dict(self.meta)
        metadata['content'] = self.html
        metadata['created'] = self.get_created_datetime()
        metadata['modified'] = self.get_modified_datetime()
        metadata['author'] = self.app.conf['author']

        # render result file
        template = metadata.get('template', self.template)
        template = self.app.jinja_env.get_template(template)

        with open(self.destination, 'w', encoding='utf-8') as f:
            # TODO: I definetely need to do something with this ugly code
            f.write(template.render(
                document=metadata,
                sitename=self.app.conf['sitename'],
                siteurl=self.app.conf['siteurl'],
                author=self.app.conf['author'],
            ))

    @property
    def destination(self):
        filename, _ = os.path.splitext(self.short_source)
        return os.path.join(
            self.app.conf['paths.output'],
            filename, 'index.html'
        )

    @property
    def url(self):
        filename, _ = os.path.splitext(self.short_source)
        return '/' + filename + '/'

    @property
    def abs_url(self):
        return self.app.conf['siteurl'] + self.url


class Static(Document):
    """
    A static document representation.

    This type of documents are those documents that have not been identidied
    as convertible. Satic documents just copy an input file to output folder,
    preserving the directory structure of the content folder.

    For instance, an input file::

        /2014/01/01/cake.png

    will be built as::

        /2014/01/01/cake.png

    in the output folder.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        logger.info("Found a static document: '%s'", self.filename)

    def build(self):
        mkdir(os.path.dirname(self.destination))
        shutil.copy(self.source, self.destination)

    @property
    def destination(self):
        return os.path.join(self.app.conf['paths.output'], self.short_source)

    @property
    def url(self):
        return '/' + self.short_source

    @property
    def abs_url(self):
        return self.app.conf['siteurl'] + self.url
