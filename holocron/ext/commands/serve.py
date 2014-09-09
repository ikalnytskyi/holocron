# coding: utf-8
"""
    holocron.ext.commands.serve
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a serve command.

    :copyright: (c) 2014, Andrii Gamaiunov
    :license: BSD, see LICENSE for details
"""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from holocron import app
from holocron.ext import Command


class ChangeHandler(FileSystemEventHandler):
    """
    Implements catching system events of adding or changing files. Responsible
    for processing events and rebuilding theme files and blogposts.
    """
    def __init__(self, app):
        super(ChangeHandler, self).__init__()
        self.app = app

    def process(self, document_path):
        """
        Rebuilds the whole blog, if a blog post or theme file were changed.
        If the file from the output directiry was changed than do nothing.

        :param document_path: path to changed/added file
        """
        document = os.path.abspath(document_path)
        output = os.path.abspath(self.app.conf['paths.output'])

        # do not track changes in the output directory
        if document.startswith(output):
            return

        try:
            self.app.run()
        except Exception:
            self.app.logger.warning(
                'File %s is invalid. Building skipped.', document)

    def on_modified(self, event):
        if event.is_directory:
            return

        self.process(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return

        self.process(event.src_path)


def create_holocron_handler(path):
    """
    This factory method is used to create the http handler class with a custom
    attribute indicating a serve path.

    :param path: path to a directory to serve files from
    """
    class HolocronHandler(SimpleHTTPRequestHandler):

        serve = path

        def translate_path(self, path):
            """
            Changes default serving directory to the one specified in
            configurations under paths.output section
            """

            path = super(HolocronHandler, self).translate_path(path)
            return os.path.join(self.serve, os.path.relpath(path))

    return HolocronHandler


class Serve(Command):
    """
    Serve is a serve command class.

    Serve class is responsible for serving the holocron application at a local
    server. Command creates a simple htttp server and shares html files that
    generated in the output directory (build_/ by default).
    """
    # path to the default theme
    app_path = os.path.abspath(os.path.dirname(app.__file__))
    theme_default = os.path.join(app_path, 'themes', 'default')

    def execute(self, app):
        self.host = app.conf['commands.serve.host']
        self.port = int(app.conf['commands.serve.port'])

        # paths to track for chnages
        watch_paths = [os.curdir, self.theme_default]

        # check if there is a user theme and add it to watch directories list
        if os.path.exists(os.path.abspath(app.conf['paths.theme'])):
            watch_paths.append(os.path.abspath(app.conf['paths.theme']))

        observer = Observer()

        for path in watch_paths:
            observer.schedule(ChangeHandler(app), path=path, recursive=True)

        holocron_handler = create_holocron_handler(app.conf['paths.output'])
        httpd = HTTPServer((self.host, self.port), holocron_handler)

        print('HTTP server started at {host}\n'.format(host=self.full_host))
        print('In order to stop serving, press Ctrl+C\n')

        try:
            observer.start()
            httpd.serve_forever()

        except KeyboardInterrupt:
            print(' recieved, shutting down server')
            httpd.socket.close()
            observer.stop()

        observer.join()

    @property
    def full_host(self):
        return 'http://{host}:{port}'.format(host=self.host, port=self.port)
