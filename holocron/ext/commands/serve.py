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

from holocron.ext import Command
from holocron.content import Document


class Serve(Command):
    """
    Serve is a serve command class.

    Serve class is responsible for serving the holocron application
    at a local server. It assumes that serve command is run inside
    a directory with a '/_build' folder, where all the generated documnets
    are stored.
    """
    def execute(self, app):
        self.host = app.conf['commands.serve.host']
        self.port = int(app.conf['commands.serve.port'])

        class ChangeHandler(FileSystemEventHandler):

            def process(self, document):
                """
                Rebuilds document upon the path, passed
                by the watchdog library. Prevents files of the
                output directory from rebuilding.

                :param document: a path to document
                """
                document = os.path.abspath(document)
                output = os.path.abspath(app.conf['paths.output'])

                # do not track changes in the output directory
                if document.startswith(output):
                    return

                try:
                    Document(document, app).build()
                except FileNotFoundError:
                    app.logger.warning(
                        'File %s not found. Building skipped', document
                    )
                    return
                except Exception:
                    app.logger.warning(
                        'File %s is invalid. Building skipped', document
                    )
                    return

            def on_modified(self, event):
                if event.is_directory:
                    return

                document = event.src_path
                self.process(document)

            def on_created(self, event):
                if event.is_directory:
                    return

                document = event.src_path
                self.process(document)

        class HolocronHandler(SimpleHTTPRequestHandler):

            def translate_path(self, path):
                """
                Changes default serving directory to the one
                specified in configurations under paths.output
                section
                """
                path = SimpleHTTPRequestHandler.translate_path(self, path)
                return os.path.join(
                    app.conf['paths.output'],
                    os.path.relpath(path)
                )

        observer = Observer()

        observer.schedule(
            ChangeHandler(),
            path=os.path.join(os.curdir),
            recursive=True
        )

        httpd = HTTPServer((self.host, self.port), HolocronHandler)

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
