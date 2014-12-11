# coding: utf-8
"""
    holocron.main
    ~~~~~~~~~~~~~

    This module provides a command line interface.
    It's a so called entry point of Holocron application.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""
import sys
import logging
import argparse

import yaml
from dooku.ext import ExtensionManager

from holocron.app import Holocron


def parse_command_line(commands):
    """
    Builds a command line interface, and parses it arguments.
    Returns an object with attributes, that are represent CLI arguments.

    :param commands: a list of available commands
    """

    parser = argparse.ArgumentParser(
        description=(
            'Holocron is an easy and lightweight static blog generator, '
            'based on markup text and Jinja2 templates.'),
        epilog=(
            'With no CONFIG, read _config.yml in the current working dir.'
            'If no CONFIG found, the default settings will be used.'))

    parser.add_argument(
        'command', choices=commands, help='a command to execute')

    parser.add_argument(
        '-c', '--conf', dest='conf', default='_config.yml',
        help='a path to settings file')

    parser.add_argument(
        '-v', '--verbose', dest='verbose', action='store_const',
        const=logging.INFO, default=logging.WARNING,
        help='show more information')

    return parser.parse_args()


def get_config(filename):
    """
    Gets settings from a given YAML file as a dictionary.

    :param filename: a path to settings file
    :returns: a dict with settings
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return yaml.load(f.read())

    except IOError:
        print('holocron: {0}: No such file or directory'.format(filename),
              file=sys.stderr)

    except yaml.YAMLError as e:
        print('Could not parse a given settings file: \n\n{0}'.format(e),
              file=sys.stderr)


def create_app(conf):
    """
    Creates and returns a :class:`holocron.app.Holocron` instance,
    that is built on top of a given config.

    :param conf: a config dict for application instance
    :returns: a holocron instance
    """
    app = Holocron(conf)
    return app


def configure_logger(logger_level=logging.WARNING):
    """
    Configure a root logger to print records in pretty format:

        [WARN] message

    This format is more useful and readable for end users, since it's
    not necessary to know a record's time and a source.

    :param logger_level: a minimum logging level to be printed
    """
    class formatter(logging.Formatter):
        def format(self, record):
            record.levelname = record.levelname[:4]
            return super(formatter, self).format(record)

    # create stream handler with custom formatter
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter('[%(levelname)s] %(message)s'))

    # configure root logger
    logger = logging.getLogger()
    logger.addHandler(stream_handler)
    logger.setLevel(logger_level)


def main():
    # initialize command manager and get a list of available commands
    command_manager = ExtensionManager('holocron.ext.commands')
    arguments = parse_command_line(command_manager.names())

    # initial logger configuration - use custom format for records
    # and print records with WARNING level and higher.
    configure_logger(arguments.verbose)

    # this hack's used to bypass lack of user's config file when init invoked
    conf = {}
    if arguments.command not in ('init', ):
        conf = get_config(arguments.conf)

    holocron = create_app(conf)
    command_manager[arguments.command]().execute(holocron)
