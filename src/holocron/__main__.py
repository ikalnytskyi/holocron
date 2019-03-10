"""Yo! Holocron CLI is here!"""

import io
import os
import sys
import logging
import argparse
import warnings

import colorama
import termcolor
import yaml

from . import core
from holocron import __version__ as holocron_version


def create_app_from_yml(path):
    """Return an application instance created from YAML."""

    try:
        with open(path, "rt", encoding="UTF-8") as f:
            try:
                # Substitute ALL occurrences of '%(here)s' with a path to a
                # directory with '_config.yml'. Please note, we also want wrap
                # the result into 'io.StringIO' in order to preserve original
                # filename in 'yaml.safe_load()' errors.
                interpolated = io.StringIO(
                    f.read() % {"here": os.path.abspath(os.path.dirname(path))}
                )
                interpolated.name = f.name

                conf = yaml.safe_load(interpolated)
            except yaml.YAMLError as exc:
                raise RuntimeError(
                    "Cannot parse a configuration file. Context: " + str(exc)
                )

    except FileNotFoundError:
        conf = {"metadata": None, "pipes": {}}

    return core.create_app(conf["metadata"], pipes=conf["pipes"])


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
    stream_handler.setFormatter(_Formatter("[%(levelname)s] %(message)s"))

    # configure root logger
    logger = logging.getLogger()
    logger.addHandler(stream_handler)
    logger.setLevel(level)

    # capture warnings issued by 'warnings' module
    logging.captureWarnings(True)


def parse_command_line(args):
    """
    Builds a command line interface, and parses its arguments. Returns
    an object with attributes, that are represent CLI arguments.

    :param args: a list of command line arguments
    :returns: a parsed object with cli options
    """
    parser = argparse.ArgumentParser(
        description=(
            "Holocron is an easy and lightweight static blog generator, "
            "based on markup text and Jinja2 templates."
        ),
        epilog=(
            "With no CONF, read _config.yml in the current working dir. "
            "If no CONF found, the default settings will be used."
        ),
    )

    parser.add_argument(
        "-c",
        "--conf",
        dest="conf",
        default="_config.yml",
        help="set path to the settings file",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        dest="verbosity",
        action="store_const",
        const=logging.CRITICAL,
        help="show only critical errors",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="store_const",
        const=logging.INFO,
        help="show additional messages",
    )

    parser.add_argument(
        "-d",
        "--debug",
        dest="verbosity",
        action="store_const",
        const=logging.DEBUG,
        help="show all messages",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=holocron_version,
        help="show the holocron version and exit",
    )

    command_parser = parser.add_subparsers(
        dest="command", help="command to execute"
    )

    run_parser = command_parser.add_parser("run")
    run_parser.add_argument("pipe", help="a pipe to run")

    # parse cli and form arguments object
    arguments = parser.parse_args(args)

    # if no commands are specified display help
    if arguments.command is None:
        parser.print_help()
        parser.exit(1)

    return arguments


def main(args=sys.argv[1:]):
    # colorama.init() does two great things Holocron depends on. First, it
    # converts ANSI escape sequences printed to standard streams into proper
    # Windows API calls. Second, it strips ANSI colors away from a stream if
    # it's not connected to a tty (e.g. holocron is called from pipe).
    with colorama.colorama_text():
        arguments = parse_command_line(args)

        # initial logger configuration - use custom format for records
        # and print records with WARNING level and higher.
        configure_logger(arguments.verbosity or logging.WARNING)

        # show deprecation warnings in order to be prepared for backward
        # incompatible changes
        warnings.filterwarnings("always", category=DeprecationWarning)

        try:
            holocron = create_app_from_yml(arguments.conf)

            for item in holocron.invoke(arguments.pipe):
                print(
                    termcolor.colored("==>", "green", attrs=["bold"]),
                    termcolor.colored(item["destination"], attrs=["bold"]),
                )
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)
