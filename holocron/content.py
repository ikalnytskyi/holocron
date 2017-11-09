"""
    holocron.content
    ~~~~~~~~~~~~~~~~

    This module contains models for all content types supported by Holocron.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import abc
import warnings


class Document(dict, metaclass=abc.ABCMeta):
    """
    An abstract base class for Holocron documents.

    It provides a *document* interface and implements common stuff.

    :param filename: a path to physical file
    :param app: a reference to the application it's attached to
    """

    def __init__(self, app):
        self._app = app

    def __getattr__(self, attr):
        try:
            warnings.warn(
                "Attributes are deprecated way to retrieve data out of "
                "documents, please use dict syntax instead.")
            return self[attr]
        except KeyError as exc:
            raise AttributeError(str(exc))

    def __setattr__(self, attr, value):
        # Provide object interface for new-style documents to maintain
        # backward compatibility. It will be removed in Holocron 0.5.0.
        self[attr] = value

    def __getitem__(self, item):
        if item in ('created_local', 'updated_local'):
            warnings.warn(
                "Do not use *_local datetimes as they are deprecated. "
                "Instead use UTC based datetimes and convert to local "
                "time explicitly where needed.")
        return super().__getitem__(item)

    @property
    def url(self):
        destination = self['destination']

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

    @classmethod
    def __subclasshook__(cls, subclass):
        warnings.warn(
            "isinstance() check for this class is deprecated, and the class "
            "itself will be removed in next release.")
        return super().__subclasshook__(subclass)


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
    pass


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
    pass


Document.register(Page)
