# coding: utf-8
"""
    holocron.ext.abc
    ~~~~~~~~~~~~~~~~

    Abstract Base Classes (ABC) for Holocron extensions. They are not
    mandatory for usage, but strongly recommended.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import abc


class Command(object, metaclass=abc.ABCMeta):
    """
    Abstract base class for 'Command' extensions.

    Commands are used to interact with Holocron application instance.
    They could be used to build application (generate html blog entries),
    serve the application at a local webserver or online, etc.

    Usage example::

        from holocron.ext import abc

        class MyCoolCommand(abc.Command):
            def execute(self, app):
                # perform some actions
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
    Abstract base class for 'Converter' extensions.

    Holocron converters hierarchy originates here. In the best traditions
    of the classical OOP, the class declares the converter interface, which
    has to be respected by all converters.

    So in case you want to write your own converter, you probably write
    something like that::

        from holocron.ext import abc

        class MarkdownConverter(abc.Converter):
            extensions = ['.md', '.mkd']

            def to_html(self, text):
                # do conversion
                return meta, html

    It's important to note, that a converter in terms of extension is not
    a converter in terms of application:

    * in terms of extension, the converter is an extension class, which
      registers a convert function in a given application instance;

    * in terms of application, the converter is a convert function, that
      can convert a given markuped text into HTML and extract some meta
      information.

    Converters receive a conf dictionary as a constructor argument that
    is extracted from `converters` node of your YAML settings file.

    :param conf: a :class:`~dooku.conf.Conf` with converters settings;
                 it's a good practice to use a separate setting-node for
                 each converter
    """
    def __init__(self, conf):
        self.conf = conf

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
    Abstract base class for 'Generator' extensions.

    Generators are a special kind of Holocron extensions. They're designed to
    generate helpful stuff based on input document collection (e.g. sitemap).

    Usage example::

        from holocron.ext import abc

        class SitemapGenerator(abc.Generator):
            def generate(self, documents):
                # do some job based on input document collection

    :param app: an application instance
    """
    def __init__(self, app):
        self.app = app

    @abc.abstractmethod
    def generate(self, documents):
        """
        Generate some stuff based on input document collection.

        :param documents: a document collection
        """
