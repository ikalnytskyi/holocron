from holocron.ext import Command


class Build(Command):
    """
    Build class implements the build command.
    It is responsibe for running the application instance.
    """

    def execute(self, app):
        app.run()
