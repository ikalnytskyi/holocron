# coding: utf-8
"""
    holocron.ext
    ~~~~~~~~~~~~

    The package contains base classes for all supported extension types.

    :copyright: (c) 2014, Igor Kalnitsky
    :license: BSD, see LICENSE for details
"""
import abc


class Converter(object, metaclass=abc.ABCMeta):
    """
    Base converter class.

    Holocron's converters hierarchy originates here. In the best traditions
    of the classical OOP, the class declares the converter interface, which
    has to be respected by all converters.

    So in case you want to write your own converter, you probably write
    something like that::

        from holocron.ext import Converter

        class MarkdownConverter(Converter):
            extensions = ['.md', '.mkd']

            def to_html(self, text):
                # do convertion
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
    Base generator class.

    Generators are a special kind of Holocron extensions. They're designed to
    generate helpful stuff based on input document collection (e.g. sitemap).

    Usage example::

        from holocron.ext import Generator

        class SitemapGenerator(Generator):
            def generate(self, documents):
                # create sitemap.xml for a given documents collection
                # should use only convertible documents

    :param conf: a :class:`~dooku.conf.Conf` with Holocron settings
    """
    def __init__(self, conf):
        self.conf = conf

    @abc.abstractmethod
    def generate(self, documents):
        """
        Generate some stuff based on input document collection.

        :param documents: a document collection
        :returns: nothing
        """


class Command(object, metaclass=abc.ABCMeta):
    """
    Base commands class.

    Commands are used to interact with Holocron application instance.
    They could be used to build application (generate html blog entries),
    serve the application at a local webserver or online, etc.

    Usage example::

        from holocron.ext import Command

        class MyCoolCommand(Command):
            def execute(self, app):
                # perform some actions and interact with application instance
                # the command class should provide execute() method as an entry
                point of a command
    """

    @abc.abstractmethod
    def execute(self, app):
        """
        Execute is a uniform method used to execute commands.

        :param app: an application instance
        :returns: nothing
        """
