"""
    holocron.ext.abc
    ~~~~~~~~~~~~~~~~

    Abstract Base Classes (ABC) for Holocron extensions. They are not
    mandatory for usage, but strongly recommended.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import abc


class Extension(object, metaclass=abc.ABCMeta):
    """
    Abstract base class for Holocron extensions.

    Holocron uses entry points based approach for extensions discovering.
    Thus, entry points that are exported to ``holocron.ext`` namespace
    will be considered as extensions, and Holocron will call them and pass
    its instance as argument. Further, it will be up to extension to decide
    what to do (it can register a converter, generator, etc).

    .. versionadded:: 0.2.0

    :param app: an application instance
    """

    @abc.abstractmethod
    def __init__(self, app):
        """Initialize extension."""


class Command(object, metaclass=abc.ABCMeta):
    """
    Abstract base class for 'Command' extensions.

    Commands are used to interact with Holocron application instance.
    They could be used to build application (generate html blog entries),
    serve the application at a local webserver or online, etc.

    Example::

        from holocron.ext import abc

        class MyCoolCommand(abc.Command):
            def execute(self, app):
                # perform some actions

    TODO: revise the docstring
    """

    def set_arguments(self, parser):
        """
        Declare additional command line arguments for the command. By default,
        there are no arguments. Each command has to overwite this method in
        order to add new arguments.

        :param parser: an :class:`argparse.ArgumentParser` for the command
        """

    @abc.abstractmethod
    def execute(self, app, arguments):
        """
        Execute is a uniform method used to execute commands.

        :param app: an application instance
        :param arguments: a Namespace object with parsed command line arguments
        """


class Converter(object, metaclass=abc.ABCMeta):
    """
    The 'Converter' interface.

    Holocron converters hierarchy originates here. In the best traditions
    of the classical OOP, the class declares a converter interface, which
    has to be respected by all converters.

    Example::

        from holocron.ext import abc

        class MarkdownConverter(abc.Converter):
            extensions = ['.md', '.mkd']

            def to_html(self, text):
                # do conversion
                return meta, html

    """

    @property
    @abc.abstractmethod
    def extensions(self):
        """
        A converter's property, which have to returns a list of supported
        file extensions.

        :returns: a list of file extensions
        """

    @abc.abstractmethod
    def to_html(self, text):
        """
        Converts a given `text` to HTML and returns the result together
        with the extracted meta information.

        :param text: a text to be converted, should be markuped with Markdown
        :returns: a tuple of the following format `(meta, html)`
        """


class Generator(object, metaclass=abc.ABCMeta):
    """
    The 'Generator' interface.

    Generators are a special kind of Holocron extensions. They're designed
    to generate additional stuff based on input document collection. Good
    examples of generators are feed and sitemap.

    Example::

        from holocron.ext import abc

        class SitemapGenerator(abc.Generator):
            def generate(self, documents):
                # do some job based on input document collection

    """

    @abc.abstractmethod
    def generate(self, documents):
        """
        Generate some stuff based on input document collection.

        :param documents: a document collection
        """
