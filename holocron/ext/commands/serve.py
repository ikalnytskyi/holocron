# coding: utf-8
"""
    holocron.ext.commands.serve
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The module implements a serve command.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import time
import threading

from http.server import HTTPServer, SimpleHTTPRequestHandler

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from holocron import app
from holocron.ext import abc


class _ChangeWatcher(FileSystemEventHandler):
    """
    Handles filesystem events and decides whether blog should be rebuilt
    or not. The class asks a :class:`_Builder` to rebuild blog on next
    schedule if there were some "interesting" events.

    :param builder: a :class:`_Builder` instance
    :param recreate_app: recreated the app as well as rebuilt blog if True
    :param watch_for: a list of paths we should watch for
    :param ignore: a list of files which should be ignored
    """

    def __init__(self, builder, recreate_app=False, watch_for=None,
                 ignore=None):
        super(_ChangeWatcher, self).__init__()

        self._builder = builder
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
        output = os.path.abspath(self._builder._app.conf['paths.output'])
        if document.startswith(output):
            return

        # Recreate application if it's possible and we have to.
        if self._recreate_app:
            self._builder.recreate_app()
        self._builder.rebuild()

    def on_created(self, event):
        if not event.is_directory:
            self.process(os.path.abspath(event.src_path))

    def on_modified(self, event):
        self.on_created(event)


class _Builder(threading.Thread):
    """
    The class is intended to wake up each N seconds and rebuild blog if
    it was asked to do so.

    :param app: a Holocron instance to build blog
    :param confpath: a path to config file
    :param sleep: a time in seconds between awakenings
    """

    def __init__(self, app, confpath, sleep=1):
        super(_Builder, self).__init__()

        self._app = app
        self._confpath = confpath
        self._sleep = sleep
        self._recreate_app = False
        self._rebuild = False
        self._quit = False

    def recreate_app(self):
        self._recreate_app = True

    def rebuild(self):
        self._rebuild = True

    def shutdown(self):
        self._quit = True

    def run(self):
        while not self._quit:

            if self._recreate_app:
                self._app = app.create_app(self._confpath) or self._app
                self._recreate_app = False

            if self._rebuild:
                self._app.run()
                self._rebuild = False

            time.sleep(self._sleep)


def _create_holocron_handler(path):
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
    files that generated in the output directory (_build/ by default).
    """

    def execute(self, app, arguments):
        wakeup = int(app.conf['commands.serve.wakeup'])

        app.run()

        builder = _Builder(app, arguments.conf, wakeup)
        observer = self._watch(app, arguments, builder)
        httpd = self._serve(app)

        try:
            builder.start()
            observer.start()
            httpd.serve_forever()

        except KeyboardInterrupt:
            print(' recieved, shutting down server')

        finally:
            httpd.socket.close()
            observer.stop()
            builder.shutdown()

    def _watch(self, app, arguments, builder):
        # By default we're watching for events in content directory.
        watch_paths = [
            app.conf['paths.content'],
        ]

        # But it'd be nice to watch themes directories either.
        for theme in app._themes:
            if os.path.exists(theme):
                watch_paths.append(theme)

        observer = Observer()
        for path in watch_paths:
            observer.schedule(
                _ChangeWatcher(builder, ignore=[
                    os.path.abspath(arguments.conf),
                ]),
                path, recursive=True)

        # We also should watch for user's settings explicitly, because
        # they may located not in the content directory.
        if os.path.exists(arguments.conf):
            observer.schedule(
                _ChangeWatcher(builder, recreate_app=True, watch_for=[
                    os.path.abspath(arguments.conf),
                ]),
                os.path.abspath(os.path.dirname(arguments.conf)))

        return observer

    def _serve(self, app):
        host = app.conf['commands.serve.host']
        port = int(app.conf['commands.serve.port'])

        print('HTTP server started at http://{0}:{1}/'.format(host, port))
        print('In order to stop serving, press Ctrl+C')

        holocron_handler = _create_holocron_handler(app.conf['paths.output'])
        return HTTPServer((host, port), holocron_handler)
