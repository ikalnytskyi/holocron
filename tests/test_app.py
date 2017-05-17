"""
    tests.test_app
    ~~~~~~~~~~~~~~

    Tests the Holocron instance.

    :copyright: (c) 2014 by the Holocron Team, see AUTHORS for details.
    :license: 3-clause BSD, see LICENSE for details.
"""

import os
import copy
import textwrap

import mock

import holocron
import holocron.ext
from holocron.app import Holocron, create_app
from holocron.ext import abc

from tests import HolocronTestCase


class TestHolocron(HolocronTestCase):

    def setUp(self):
        self.app = Holocron({
            'ext': {
                'enabled': [],
            },
        })

    def test_user_settings(self):
        """
        Tests creating an instance with custom settings: check for settings
        overriding.
        """
        app = Holocron({
            'sitename': 'Luke Skywalker',
            'paths': {
                'content': 'path/to/content',
            },
        })

        conf = copy.deepcopy(app.default_conf)
        conf['sitename'] = 'Luke Skywalker'
        conf['paths']['content'] = 'path/to/content'

        self.assertEqual(app.conf, conf)

    def test_add_converter(self):
        """
        Tests converter registration process.
        """
        class TestConverter(abc.Converter):
            extensions = ['.tst', '.test']

            def to_html(self, text):
                return {}, text

        # test registration process
        converter = TestConverter()
        self.assertEqual(len(self.app._converters), 0)
        self.app.add_converter(converter)
        self.assertEqual(len(self.app._converters), 2)

        self.assertIn('.tst', self.app._converters)
        self.assertIn('.test', self.app._converters)

        self.assertIs(self.app._converters['.tst'], converter)
        self.assertIs(self.app._converters['.test'], converter)

        # test protection from double registration
        self.app.add_converter(TestConverter())
        self.assertIs(self.app._converters['.tst'], converter)
        self.assertIs(self.app._converters['.test'], converter)

        # test force registration
        new_converter = TestConverter()
        self.app.add_converter(new_converter, _force=True)
        self.assertIs(self.app._converters['.tst'], new_converter)
        self.assertIs(self.app._converters['.test'], new_converter)

    def test_add_generator(self):
        """
        Tests generator registration process.
        """
        class TestGenerator(abc.Generator):
            def generate(self, text):
                pass

        # test registration process
        generator = TestGenerator()
        self.assertEqual(len(self.app._generators), 0)
        self.app.add_generator(generator)
        self.assertEqual(len(self.app._generators), 1)
        self.assertIn(generator, self.app._generators)

        # test double registration is allowed
        new_generator = TestGenerator()
        self.app.add_generator(new_generator)
        self.assertEqual(len(self.app._generators), 2)
        self.assertIn(new_generator, self.app._generators)

    @mock.patch('holocron.app.make_document')
    @mock.patch('holocron.app.mkdir')
    @mock.patch('holocron.app.iterfiles')
    def test_run(self, iterfiles, mkdir, make_document):
        """
        Tests build process.
        """
        iterfiles.return_value = ['doc_a', 'doc_b', 'doc_c']
        self.app.__class__.document_factory = mock.Mock()
        self.app._copy_theme = mock.Mock()
        self.app._generators = {
            mock.Mock(): mock.Mock(),
            mock.Mock(): mock.Mock(),
        }

        self.app.run()

        # check iterfiles call signature
        iterfiles.assert_called_with(
            self.app.conf['paths']['content'], '[!_.]*', True)

        # check mkdir create ourpur dir
        mkdir.assert_called_with(self.app.conf['paths.output'])

        # check that generators was used
        for generator in self.app._generators:
            self.assertEqual(generator.generate.call_count, 1)

        self.app.__class__.document_factory.assert_has_calls([
            # check that document class was used to generate class instances
            mock.call('doc_a', self.app),
            mock.call('doc_b', self.app),
            mock.call('doc_c', self.app),
        ])
        self.assertEqual(self.app.__class__.document_factory.call_count, 3)

        make_document.assert_has_calls([
            mock.call(self.app.document_factory(), self.app),
            mock.call(self.app.document_factory(), self.app),
            mock.call(self.app.document_factory(), self.app),
        ])

        # check that _copy_theme was called
        self.app._copy_theme.assert_called_once_with()

    @mock.patch('holocron.app.copy_tree')
    def test_copy_base_theme(self, mcopytree):
        """
        Tests that Holocron do copy default theme.
        """
        output = os.path.join(self.app.conf['paths.output'], 'static')
        theme = os.path.join(
            os.path.dirname(holocron.__file__), 'theme', 'static')

        self.app._copy_theme()

        mcopytree.assert_called_with(theme, output)

    @mock.patch('holocron.app.os.path.exists', return_value=True)
    @mock.patch('holocron.app.copy_tree')
    def test_copy_user_themes(self, mcopytree, _):
        """
        Tests that Holocron do copy user theme.
        """
        output = os.path.join(self.app.conf['paths.output'], 'static')
        theme = os.path.join(
            os.path.dirname(holocron.__file__), 'theme', 'static')

        self.app.add_theme('theme1')
        self.app.add_theme('theme2')
        self.app._copy_theme()

        self.assertEqual(mcopytree.call_args_list, [
            mock.call(theme, output),
            mock.call(os.path.join('theme1', 'static'), output),
            mock.call(os.path.join('theme2', 'static'), output),
        ])

    @mock.patch('holocron.app.os.path.exists', side_effect=[True, False])
    @mock.patch('holocron.app.copy_tree')
    def test_copy_user_themes_not_exist(self, mcopytree, _):
        """
        Tests that Holocron doesn't copy static if it's not exist.
        """
        output = os.path.join(self.app.conf['paths.output'], 'static')
        theme = os.path.join(
            os.path.dirname(holocron.__file__), 'theme', 'static')

        self.app.add_theme('theme1')
        self.app._copy_theme()

        self.assertEqual(mcopytree.call_args_list, [
            mock.call(theme, output),
        ])


class TestHolocronDefaults(HolocronTestCase):

    def setUp(self):
        self.app = Holocron()

    def test_registered_converters(self):
        """
        Tests that default converters are registered.
        """
        converters_cls = {type(conv) for conv in self.app._converters.values()}

        self.assertCountEqual(converters_cls, [
            holocron.ext.Markdown,
            holocron.ext.ReStructuredText,
        ])

    def test_registered_generators(self):
        """
        Tests that default generators are registered.
        """
        generators_cls = [type(gen) for gen in self.app._generators]

        self.assertCountEqual(generators_cls, [
            holocron.ext.Feed,
            holocron.ext.Index,
            holocron.ext.Sitemap,
            holocron.ext.Tags,
        ])

    def test_registered_themes(self):
        """
        Tests that default theme is registered.
        """
        self.assertCountEqual(self.app._themes, [
            os.path.join(os.path.dirname(holocron.__file__), 'theme'),
        ])


class TestCreateApp(HolocronTestCase):

    def setUp(self):
        # By its design 'warnings.warn' spawn a warning only once, and info
        # whether it's spawned or not keeps in per-module registry. Since
        # it's global by nature, it's shared between test cases and break
        # them. Since Python 3.4 there's a versioned registry, so any
        # changes to filters or calling to 'catch_warnings' context manager
        # will reset it, but Holocron supports Python 3.3 too. So we use
        # manual registry resetting as temporary solution.
        import sys
        getattr(sys.modules['holocron.app'], '__warningregistry__', {}).clear()

    def _create_app(self, conf_raw=None, side_effect=None):
        """
        Creates an application instance with mocked settings file. All
        arguments will be passed into mock_open.
        """
        mopen = mock.mock_open(read_data=conf_raw)
        mopen.side_effect = side_effect if side_effect else None

        with mock.patch('holocron.app.open', mopen, create=True):
            return create_app('_config.yml')

    def test_default(self):
        """
        The create_app with no arguments has to create a Holocron instance
        with default settings.
        """
        app = create_app()

        self.assertIsNotNone(app)
        self.assertIsInstance(app, Holocron)

    def test_custom_conf(self):
        """
        Tests that custom conf overrides default one.
        """
        conf_raw = textwrap.dedent('''\
            site:
                name: MySite
                author: User
        ''')
        app = self._create_app(conf_raw=conf_raw)

        self.assertIsNotNone(app)
        self.assertEqual(app.conf['site.name'], 'MySite')
        self.assertEqual(app.conf['site.author'], 'User')

    def test_illformed_conf(self):
        """
        Tests that in case of ill-formed conf we can't create app instance.
        """
        conf_raw = textwrap.dedent('''\
            error
            site:
                name: MySite
        ''')
        app = self._create_app(conf_raw=conf_raw)

        self.assertIsNone(app)

    def test_filenotfounderror(self):
        """
        Tests that we create application with default settings in case user's
        settings wasn't found.
        """
        app = self._create_app(side_effect=FileNotFoundError)

        self.assertIsNotNone(app)
        self.assertIsInstance(app, Holocron)

    def test_permissionerror(self):
        """
        Tests that we create application with default settings in case we
        don't have permissions to read user settings.
        """
        app = self._create_app(side_effect=PermissionError)

        self.assertIsNotNone(app)
        self.assertIsInstance(app, Holocron)

    def test_isadirectoryerror(self):
        """
        Tests that we can't create app instance if we pass a directory as
        settings file.
        """
        app = self._create_app(side_effect=IsADirectoryError)

        self.assertIsNone(app)
