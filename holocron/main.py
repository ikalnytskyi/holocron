# coding: utf-8
"""
    holocron.main
    ~~~~~~~~~~~~~

    This module provides a command line interface.
    It's a so called entry point of Holocron application.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
import sys
import logging
import argparse

import yaml

from holocron.app import Holocron
from .command import CommandManager


def show_error_and_exit(message, exit_code=0):
    """
    Shows a given error message and terminates a current process.

    :param message: a message to be printed onto STDERR
    :param exit_code: an exit code
    """
    print(message, file=sys.stderr)
    sys.exit(exit_code)


def parse_command_line(commands):
    """
    Builds a command line interface, and parses it arguments.
    Returns an object with attributes, that are represent CLI arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            'Holocron is an easy and lightweight static blog generator, '
            'based on markup text and Jinja2 templates.'),
        epilog=(
            'With no CONFIG, read _config.yml in the current working dir.'
            'If no CONFIG found, the default settings will be used.')
    )

    parser.add_argument('command', choices=commands,
                        help='a command to execute')
    parser.add_argument('-c', '--conf', dest='conf', default='_config.yml',
                        help='a path to settings file')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
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
        show_error_and_exit(
            'holocron: {0}: No such file or directory'.format(filename)
        )
    except yaml.YAMLError as e:
        show_error_and_exit(
            'Could not parse a given settings file: \n\n{0}'.format(e)
        )


def create_app(conf):
    """
    Creates and returns a :class:`holocron.app.Holocron` instance,
    that is built on top of a given config.

    :param conf: a config dict for application instance
    :returns: a holocron instance
    """
    app = Holocron(conf)
    return app


def main():
    command_manager = CommandManager()
    commands = command_manager.get_commands()

    arguments = parse_command_line(commands)
    conf = get_config(arguments.conf)

    # print info level messages if verbose is true
    if arguments.verbose:
        logging.getLogger().setLevel(logging.INFO)

    holocron = create_app(conf)
    command_manager.call(arguments.command, holocron)
