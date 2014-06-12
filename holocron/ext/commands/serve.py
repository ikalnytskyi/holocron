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

from holocron.ext import Command


class Serve(Command):
    """
    Serve is a serve command class.

    Serve class is responsible for serving the holocron application
    at a local server. It assumes that serve command is run inside
    a directory with a '/_build' folder, where all the generated documnets
    are stored.
    """

    host = '0.0.0.0'
    port = 5000

    def execute(self, app):
        # change directory to output path of the build command
        os.chdir(os.path.join(os.curdir, app.conf['paths.output']))

        httpd = HTTPServer((self.host, self.port), SimpleHTTPRequestHandler)

        print('HTTP server started at {host}\n'.format(host=self.full_host))
        print('In order to stop serving, press Ctrl+C\n')

        try:
            httpd.serve_forever()

        except KeyboardInterrupt:
            print(' recieved, shutting down server')
            httpd.socket.close()

    @property
    def full_host(self):
        return 'http://{host}:{port}'.format(host=self.host, port=self.port)
