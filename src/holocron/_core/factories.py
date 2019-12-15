"""Factory functions to create core instances."""

from . import Application
from .._processors import import_processors, when


def create_app(metadata, processors=None, pipes=None):
    """Return an application instance with processors & pipes setup."""

    instance = Application(metadata)

    # In order to avoid code duplication, we use existing built-in import
    # processor to import and register built-in processors on the application
    # instance. This is, to be honest, the main purpose of this factory
    # function, because otherwise one must create an Application instance
    # directly.
    import_processors.process(
        instance,
        [],
        imports=[
            "archive = holocron._processors.archive:process",
            "chain = holocron._processors.chain:process",
            "commonmark = holocron._processors.commonmark:process",
            "feed = holocron._processors.feed:process",
            "frontmatter = holocron._processors.frontmatter:process",
            "import-processors = holocron._processors.import_processors:process",
            "jinja2 = holocron._processors.jinja2:process",
            "markdown = holocron._processors.markdown:process",
            "metadata = holocron._processors.metadata:process",
            "pipe = holocron._processors.pipe:process",
            "prettyuri = holocron._processors.prettyuri:process",
            "restructuredtext = holocron._processors.restructuredtext:process",
            "save = holocron._processors.save:process",
            "sitemap = holocron._processors.sitemap:process",
            "source = holocron._processors.source:process",
            "todatetime = holocron._processors.todatetime:process",
        ],
    )

    # When is the only known processor wrapper, and, frankly, we don't expect
    # more. Processor wrappers are mere hacks to avoid hardcoding yet provide
    # better syntax for wrapping processors. So let's hardcode that knowledge
    # here, and think later about general approach when the need arise.
    instance.add_processor_wrapper("when", when.process)

    for name, processor in (processors or {}).items():
        instance.add_processor(name, processor)

    for name, pipeline in (pipes or {}).items():
        instance.add_pipe(name, pipeline)

    return instance
