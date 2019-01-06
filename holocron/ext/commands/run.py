"""Run named pipeline."""

from holocron.ext import abc


class Run(abc.Command):
    """A command that runs named pipeline."""

    def set_arguments(self, parser):
        parser.add_argument('pipeline', help='a pipeline to run')

    def execute(self, app, arguments):
        if arguments.pipeline not in app.conf['pipelines']:
            raise ValueError('%s: no such pipeline' % arguments.pipeline)

        pipeline = app.conf['pipelines'][arguments.pipeline]

        for _ in app.invoke_processors([], pipeline):
            pass
