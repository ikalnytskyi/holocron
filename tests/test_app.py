"""
    tests.test_app
    ~~~~~~~~~~~~~~

    Tests the Holocron instance.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import textwrap

import mock

from holocron import core
from holocron.app import create_app

from tests import HolocronTestCase


class TestCreateApp(HolocronTestCase):

    def setUp(self):
        # By its design "warnings.warn" spawn a warning only once, and info
        # whether it"s spawned or not keeps in per-module registry. Since
        # it"s global by nature, it"s shared between test cases and break
        # them. Since Python 3.4 there"s a versioned registry, so any
        # changes to filters or calling to "catch_warnings" context manager
        # will reset it, but Holocron supports Python 3.3 too. So we use
        # manual registry resetting as temporary solution.
        import sys
        getattr(sys.modules["holocron.app"], "__warningregistry__", {}).clear()

    def _create_app(self, conf_raw=None, side_effect=None):
        """
        Creates an application instance with mocked settings file. All
        arguments will be passed into mock_open.
        """
        mopen = mock.mock_open(read_data=conf_raw)
        mopen.side_effect = side_effect if side_effect else None

        with mock.patch("holocron.app.open", mopen, create=True):
            return create_app("_config.yml")

    def test_default(self):
        """
        The create_app with no arguments has to create a Holocron instance
        with default settings.
        """
        app = create_app()

        self.assertIsNotNone(app)
        self.assertIsInstance(app, core.Application)

    def test_custom_conf(self):
        """
        Tests that custom conf overrides default one.
        """
        conf_raw = textwrap.dedent("""\
            metadata:
                skywalker: jedi
                yoda:
                    rank: master
        """)
        app = self._create_app(conf_raw=conf_raw)

        self.assertIsNotNone(app)
        self.assertEqual(app.metadata["skywalker"], "jedi")
        self.assertEqual(app.metadata["yoda"], {"rank": "master"})

    def test_illformed_conf(self):
        """
        Tests that in case of ill-formed conf we can"t create app instance.
        """
        conf_raw = textwrap.dedent("""\
            error
            site:
                name: MySite
        """)
        app = self._create_app(conf_raw=conf_raw)

        self.assertIsNone(app)

    def test_filenotfounderror(self):
        """
        Tests that we create application with default settings in case user"s
        settings wasn"t found.
        """
        app = self._create_app(side_effect=FileNotFoundError)

        self.assertIsNotNone(app)
        self.assertIsInstance(app, core.Application)

    def test_permissionerror(self):
        """
        Tests that we create application with default settings in case we
        don"t have permissions to read user settings.
        """
        app = self._create_app(side_effect=PermissionError)

        self.assertIsNotNone(app)
        self.assertIsInstance(app, core.Application)

    def test_isadirectoryerror(self):
        """
        Tests that we can"t create app instance if we pass a directory as
        settings file.
        """
        app = self._create_app(side_effect=IsADirectoryError)

        self.assertIsNone(app)

    def test_registered_processors(self):
        """
        Tests that default processors are registered.
        """
        app = create_app()

        self.assertEqual(set(app._processors), set([
            "source",
            "metadata",
            "pipeline",
            "frontmatter",
            "markdown",
            "restructuredtext",
            "prettyuri",
            "feed",
            "sitemap",
            "archive",
            "commit",
            "jinja2",
            "when",
            "todatetime",
        ]))
