"""Provides a document model that goes through processors."""

import os


class Document(dict):
    """
    An abstract base class for Holocron documents.

    It provides a *document* interface and implements common stuff.

    :param filename: a path to physical file
    :param app: a reference to the application it's attached to
    """

    def __init__(self, app):
        self._app = app

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
