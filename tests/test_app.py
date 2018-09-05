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

import pytest
import mock

import holocron
import holocron.content
from holocron.app import Holocron, create_app
from holocron.ext.processors import commit

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

    def test_add_processor(self):
        """
        Tests processor registration process.
        """
        def process(documents, **options):
            return documents

        self.assertEqual(len(self.app._processors), 0)
        self.app.add_processor('test', process)
        self.assertEqual(len(self.app._processors), 1)
        self.assertIs(self.app._processors['test'], process)

        # registration under the same name is not allowed
        self.app.add_processor('test', lambda: 0)
        self.assertEqual(len(self.app._processors), 1)
        self.assertIs(self.app._processors['test'], process)

    def test_run(self):
        """
        Tests build process.
        """
        self.app.conf['pipelines.build'] = []
        self.app.run()


class TestHolocronDefaults(HolocronTestCase):

    def setUp(self):
        self.app = Holocron()

    def test_registered_processors(self):
        """
        Tests that default processors are registered.
        """
        app = create_app()

        self.assertEqual(set(app._processors), set([
            'source',
            'metadata',
            'pipeline',
            'frontmatter',
            'markdown',
            'restructuredtext',
            'prettyuri',
            'atom',
            'sitemap',
            'index',
            'tags',
            'commit',
        ]))

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
            metadata:
                skywalker: jedi
                yoda:
                    rank: master
            site:
                name: MySite
                author: User
        ''')
        app = self._create_app(conf_raw=conf_raw)

        self.assertIsNotNone(app)
        self.assertEqual(app.conf['site.name'], 'MySite')
        self.assertEqual(app.conf['site.author'], 'User')

        self.assertEqual(app.metadata['skywalker'], 'jedi')
        self.assertEqual(app.metadata['yoda'], {'rank': 'master'})

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

    def test_registered_processors(self):
        """
        Tests that default processors are registered.
        """
        app = create_app()

        self.assertEqual(set(app._processors), set([
            'source',
            'metadata',
            'pipeline',
            'frontmatter',
            'markdown',
            'restructuredtext',
            'prettyuri',
            'atom',
            'sitemap',
            'index',
            'tags',
            'commit',
        ]))


@pytest.fixture(scope='function')
def testapp():
    return Holocron({})


def test_metadata_empty(testapp):
    with pytest.raises(KeyError, match='skywalker'):
        testapp.metadata['skywalker']
    assert testapp.metadata.get('skywalker', 'yoda') == 'yoda'

    testapp.metadata['skywalker'] = 'jedi'
    assert testapp.metadata['skywalker'] == 'jedi'


def test_metadata():
    testapp = Holocron({}, {'skywalker': 'jedi', 'yoda': 'master'})
    assert testapp.metadata['skywalker'] == 'jedi'
    assert testapp.metadata['yoda'] == 'master'

    testapp.metadata['skywalker'] = 'luke'
    assert testapp.metadata['skywalker'] == 'luke'
    assert testapp.metadata['yoda'] == 'master'


def test_theme_static(testapp, monkeypatch, tmpdir):
    """Default theme's static has to be copied."""

    monkeypatch.chdir(tmpdir)

    testapp.add_processor('commit', commit.process)
    testapp.conf['pipelines.build'] = [{'name': 'commit'}]

    testapp.run()

    assert set(tmpdir.join('_site').listdir()) == set([
        tmpdir.join('_site', 'static'),
    ])

    assert set(tmpdir.join('_site', 'static').listdir()) == set([
        tmpdir.join('_site', 'static', 'logo.svg'),
        tmpdir.join('_site', 'static', 'pygments.css'),
        tmpdir.join('_site', 'static', 'style.css'),
    ])


def test_user_theme_static(testapp, monkeypatch, tmpdir):
    """User theme's static has to be copied overwriting default theme."""

    monkeypatch.chdir(tmpdir)

    tmpdir.ensure('_theme', 'templates', 'some.txt').write('yoda')
    tmpdir.ensure('_theme', 'static', 'marker.txt').write('skywalker')
    tmpdir.ensure('_theme', 'static', 'style.css').write('overwritten')

    testapp.add_theme(tmpdir.join('_theme').strpath)
    testapp.add_processor('commit', commit.process)
    testapp.conf['pipelines.build'] = [{'name': 'commit'}]

    testapp.run()

    assert set(tmpdir.join('_site').listdir()) == set([
        tmpdir.join('_site', 'static'),
    ])

    assert set(tmpdir.join('_site', 'static').listdir()) == set([
        tmpdir.join('_site', 'static', 'logo.svg'),
        tmpdir.join('_site', 'static', 'marker.txt'),
        tmpdir.join('_site', 'static', 'pygments.css'),
        tmpdir.join('_site', 'static', 'style.css'),
    ])

    assert tmpdir.join('_site', 'static', 'style.css').read() == 'overwritten'
    assert tmpdir.join('_site', 'static', 'marker.txt').read() == 'skywalker'


@pytest.mark.parametrize('processor_options', [
    {'a': 1},
    {'b': 1.13},
    {'a': 1, 'b': 1.13},
    {'a': {'x': [1, 2]}, 'b': ['1', 2]},
])
def test_invoke_processors_propagates_options(testapp, processor_options):
    def processor(app, documents, **options):
        assert options == processor_options
    testapp.add_processor('processor', processor)
    testapp.invoke_processors([], [dict(processor_options, name='processor')])


@pytest.mark.parametrize('initial_documents', [
    [{'a': 1}],
    [{'a': 1, 'b': 1.13}],
    [{'a': 1}, {'b': 1.13}],
    [{'a': {'x': [1, 2]}, 'b': ['1', 2]}],
])
def test_invoke_processors_initial_documents(testapp, initial_documents):
    def processor(app, documents):
        assert documents == initial_documents
    testapp.add_processor('processor', processor)
    testapp.invoke_processors(initial_documents, [{'name': 'processor'}])


@pytest.mark.parametrize('documents', [
    [{'a': 1}],
    [{'a': 1, 'b': 1.13}],
    [{'a': 1}, {'b': 1.13}],
    [{'a': {'x': [1, 2]}, 'b': ['1', 2]}],
])
def test_invoke_processors_empty_pipeline(testapp, documents):
    assert testapp.invoke_processors(documents, []) == documents


def test_invoke_processors_pipeline(testapp):
    def processor_a(app, documents):
        assert documents == [{'a': 'b'}]
        documents[0]['x'] = 42
        return documents

    def processor_b(app, documents):
        assert documents == [{'a': 'b', 'x': 42}]
        documents.append({'z': 13})
        return documents

    def processor_c(app, documents):
        assert documents == [{'a': 'b', 'x': 42}, {'z': 13}]
        return documents

    testapp.add_processor('processor_a', processor_a)
    testapp.add_processor('processor_b', processor_b)
    testapp.add_processor('processor_c', processor_c)

    pipeline = [{'name': 'processor_a'},
                {'name': 'processor_b'}]
    assert testapp.invoke_processors([{'a': 'b'}], pipeline) \
        == [{'a': 'b', 'x': 42}, {'z': 13}]


def test_invoke_processors_processor_errors(testapp):
    def processor(app, documents):
        raise ValueError('something bad happened')
    testapp.add_processor('processor', processor)

    with pytest.raises(ValueError, match='something bad happened'):
        testapp.invoke_processors([], [{'name': 'processor'}])
