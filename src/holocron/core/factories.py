"""Factory functions to create core instances."""

from . import Application
from ..processors import import_processors


def create_app(metadata, processors=None, pipes=None):
    """Return an application instance with processors & pipes setup."""

    instance = Application(metadata)

    import_processors.process(
        instance,
        [],
        imports=[
            "archive = holocron.processors.archive:process",
            "commit = holocron.processors.commit:process",
            "commonmark = holocron.processors.commonmark:process",
            "feed = holocron.processors.feed:process",
            "frontmatter = holocron.processors.frontmatter:process",
            "import-processors = holocron.processors.import_processors:process",
            "jinja2 = holocron.processors.jinja2:process",
            "markdown = holocron.processors.markdown:process",
            "metadata = holocron.processors.metadata:process",
            "pipe = holocron.processors.pipe:process",
            "prettyuri = holocron.processors.prettyuri:process",
            "restructuredtext = holocron.processors.restructuredtext:process",
            "sitemap = holocron.processors.sitemap:process",
            "source = holocron.processors.source:process",
            "todatetime = holocron.processors.todatetime:process",
            "when = holocron.processors.when:process",
        ],
    )

    for name, processor in (processors or {}).items():
        instance.add_processor(name, processor)

    for name, pipeline in (pipes or {}).items():
        instance.add_pipe(name, pipeline)

    return instance
