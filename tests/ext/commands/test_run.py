"""Run command test suite."""

import argparse

import pytest

from holocron.app import Holocron
from holocron.ext.commands import run


@pytest.fixture
def testapp():
    app = Holocron({
        'pipelines': {
            'alpha': [{'name': 'set_marker', 'marker': 13}],
            'omega': [{'name': 'set_marker', 'marker': 42}],
        }
    })

    def set_marker(app, documents, marker):
        app.metadata['marker'] = marker
        yield from documents
    app.add_processor('set_marker', set_marker)

    return app


@pytest.fixture
def testcommand():
    return run.Run()


def test_run_missed(testapp, testcommand):
    with pytest.raises(ValueError, match='missed: no such pipeline'):
        testcommand.execute(testapp, argparse.Namespace(pipeline='missed'))


def test_run_alpha(testapp, testcommand):
    testcommand.execute(testapp, argparse.Namespace(pipeline='alpha'))

    assert testapp.metadata['marker'] == 13


def test_run_omega(testapp, testcommand):
    testcommand.execute(testapp, argparse.Namespace(pipeline='omega'))

    assert testapp.metadata['marker'] == 42
