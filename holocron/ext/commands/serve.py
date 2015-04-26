# coding: utf-8
"""
    holocron.ext.commands.serve
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a serve command.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os

from http.server import HTTPServer, SimpleHTTPRequestHandler

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import holocron
from holocron import app
from holocron.ext import abc


class _ChangeWatcher(FileSystemEventHandler):

    def __init__(self, app, recreate_app=False, watch_for=None, ignore=None):
        super(_ChangeWatcher, self).__init__()

        self._app = app
        self._recreate_app = recreate_app
        self._watch_for = watch_for
        self._ignore = ignore

    def process(self, document):
        """
        Checks a given document and performs appropriate actions in order
        to rebuild a blog.

        :param document: an absolute  path to created/modified document
        """
        # We shouldn't rebuild blog if changed/created file is not one
        # we are watching for. For example, we add entire directory to
        # watchdog, but interested to handle events only from certain
        # files.
        if self._watch_for and document not in self._watch_for:
            return

        # We also shouldn't rebuild blog if changed/created file is in
        # ignore list.
        if self._ignore and document in self._ignore:
            return

        # If some file is changed/created in output directory then do not
        # rebuild blog again, because it's senseless.
        output = os.path.abspath(self._app.conf['paths.output'])
        if document.startswith(output):
            return

        # Recreate application if it's possible and we have to.
        if self._recreate_app:
            self._app = app.create_app(document) or self._app
        self._app.run()

    def on_created(self, event):
        if not event.is_directory:
            self.process(os.path.abspath(event.src_path))

    def on_modified(self, event):
        self.on_created(event)


def create_holocron_handler(path):
    """
    This factory method is used to create the http handler class with
    a custom attribute indicating a serve path.

    :param path: path to a directory to serve files from
    """
    class HolocronHandler(SimpleHTTPRequestHandler):

        serve = path

        def translate_path(self, path):
            """
            Changes default serving directory to the one specified in
            configurations under paths.output section.
            """
            path = super(HolocronHandler, self).translate_path(path)
            return os.path.join(self.serve, os.path.relpath(path))

    return HolocronHandler


class Serve(abc.Command):
    """
    Run a local development server for previewing content in browser.

    Serve class is responsible for serving the holocron application at
    a local server. Command creates a simple http server and shares html
    files that generated in the output directory (build_/ by default).
    """

    def execute(self, app, arguments):
        app.run()

        self._watch(app, arguments)
        self._serve(app)

    def _watch(self, app, arguments):
        # By default we're watching for events in both content and default
        # theme directories.
        watch_paths = [
            app.conf['paths.content'],
            os.path.join(os.path.dirname(holocron.__file__), 'theme'),
        ]

        # If user has his own theme - watch it too.
        if os.path.exists(app.conf['paths.theme']):
            watch_paths.append(app.conf['paths.theme'])

        observer = Observer()
        for path in watch_paths:
            observer.schedule(
                _ChangeWatcher(app, ignore=[
                    os.path.abspath(arguments.conf),
                ]),
                path, recursive=True)

        # We also should watch for user's settings explicitly, because
        # they may located not in the content directory. Unfortunately,
        if os.path.exists(arguments.conf):
            observer.schedule(
                _ChangeWatcher(app, recreate_app=True, watch_for=[
                    os.path.abspath(arguments.conf),
                ]),
                os.path.abspath(os.path.dirname(arguments.conf)))

        observer.start()

    def _serve(self, app):
        host = app.conf['commands.serve.host']
        port = int(app.conf['commands.serve.port'])

        print('HTTP server started at http://{0}:{1}/'.format(host, port))
        print('In order to stop serving, press Ctrl+C')

        holocron_handler = create_holocron_handler(app.conf['paths.output'])
        httpd = HTTPServer((host, port), holocron_handler)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(' recieved, shutting down server')
            httpd.socket.close()
