# coding: utf-8
"""
    holocron.main
    ~~~~~~~~~~~~~

    This module provides a command line interface and an entry point for
    end users.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import sys
import logging
import argparse

from dooku.ext import ExtensionManager

from holocron.app import create_app


logger = logging.getLogger(__name__)


def configure_logger(level):
    """
    Configure a root logger to print records in pretty format.

    The format is more readable for end users, since it's not necessary at
    all to know a record's dateime and a source of the record.

    Examples::

        [INFO] message
        [WARN] message
        [ERRO] message

    :param level: a minimum logging level to be printed
    """
    class _Formatter(logging.Formatter):
        def format(self, record):
            record.levelname = record.levelname[:4]
            return super(_Formatter, self).format(record)

    # create stream handler with custom formatter
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(_Formatter('[%(levelname)s] %(message)s'))

    # configure root logger
    logger = logging.getLogger()
    logger.addHandler(stream_handler)
    logger.setLevel(level)


def parse_command_line(commands):
    """
    Builds a command line interface, and parses its arguments. Returns
    an object with attributes, that are represent CLI arguments.

    :param commands: a list of available commands
    :returns: a parsed object with cli options
    """
    parser = argparse.ArgumentParser(
        description=(
            'Holocron is an easy and lightweight static blog generator, '
            'based on markup text and Jinja2 templates.'),
        epilog=(
            'With no CONF, read _config.yml in the current working dir. '
            'If no CONF found, the default settings will be used.'))

    parser.add_argument(
        'command', choices=commands, help='a command to execute')

    parser.add_argument(
        '-c', '--conf', dest='conf', default='_config.yml',
        help='set path to the settings file')

    parser.add_argument(
        '-q', '--quiet', dest='verbosity', action='store_const',
        const=logging.CRITICAL, help='show only critical errors')

    parser.add_argument(
        '-v', '--verbose', dest='verbosity', action='store_const',
        const=logging.INFO, help='show additional messages')

    parser.add_argument(
        '-d', '--debug', dest='verbosity', action='store_const',
        const=logging.DEBUG, help='show all messages')

    return parser.parse_args()


def main():
    # initialize command manager and get a list of available commands
    command_manager = ExtensionManager('holocron.ext.commands')
    arguments = parse_command_line(command_manager.names())

    # initial logger configuration - use custom format for records
    # and print records with WARNING level and higher.
    configure_logger(arguments.verbosity or logging.WARNING)

    # this hack's used to bypass lack of user's config file when init invoked
    if arguments.command in ('init', ):
        arguments.conf = None

    # create app instance
    holocron = create_app(arguments.conf)
    if holocron is None:
        sys.exit(1)

    command = command_manager[arguments.command]()
    command.execute(holocron)
