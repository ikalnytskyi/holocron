"""Import processors test suite."""

import sys
import textwrap

import pytest

from holocron import core
from holocron.processors import import_processors


@pytest.fixture(scope="function")
def testapp(request):
    return core.Application()


@pytest.fixture(scope="function", params=["process", "invoke"])
def runprocessor(testapp, request):
    """Run the processor directly and as a part of anonymous pipe."""

    if request.param == "process":

        def runner(testapp, items, **options):
            return import_processors.process(testapp, items, **options)

    else:

        def runner(testapp, items, **options):
            options["name"] = "import-processors"
            return testapp.invoke([options], items)

        testapp.add_processor("import-processors", import_processors.process)
    return runner


def test_imports(testapp, tmpdir):
    """Imported processors must be able to be used within the same pipe."""

    testapp.add_processor("import-processors", import_processors.process)

    tmpdir.join("luke.py").write_text(
        textwrap.dedent(
            """\
            def run(app, items):
                app.metadata["master"] = True
                yield from items
        """
        ),
        encoding="UTF-8",
    )

    for _ in testapp.invoke(
        [
            {
                "name": "import-processors",
                "imports": ["luke = luke:run"],
                "from_": tmpdir.strpath,
            },
            {"name": "luke"},
        ]
    ):
        pass

    assert testapp.metadata["master"] is True


@pytest.mark.parametrize(
    ["processors", "imports", "registered"],
    [
        pytest.param([], [], [], id="no-imports"),
        pytest.param(
            ["yoda.py"],
            ["yoda = yoda:process"],
            ["yoda"],
            id="yoda-imports-yoda",
        ),
        pytest.param(
            ["vader.py"],
            ["vader = vader:process"],
            ["vader"],
            id="vader-imports-vader",
        ),
        pytest.param(
            ["yoda.py", "vader.py"],
            ["yoda = yoda:process"],
            ["yoda"],
            id="yoda-vader-imports-yoda",
        ),
        pytest.param(
            ["yoda.py", "vader.py"],
            ["yoda = yoda:process", "vader = vader:process"],
            ["yoda", "vader"],
            id="yoda-vader-imports-yoda-vader",
        ),
    ],
)
def test_imports_param_from(
    testapp, runprocessor, tmpdir, processors, imports, registered
):
    """Imports must work from 3rd party directory."""

    for processor in processors:
        tmpdir.join(processor).write_text(
            textwrap.dedent(
                """\
                def process(app, items):
                    yield from items
            """
            ),
            encoding="UTF-8",
        )

    for _ in runprocessor(testapp, [], imports=imports, from_=tmpdir.strpath):
        pass

    # Test that out of two processors (i.e. 'yoda' and 'vader'), only expected
    # ones are registered in testapp instance.
    assert set(["yoda", "vader"]) & set(testapp._processors) == set(registered)


@pytest.mark.parametrize(
    ["imports", "registered"],
    [
        pytest.param([], [], id="no-imports"),
        pytest.param(
            ["yoda = os.path:join"], ["yoda"], id="yoda-imports-yoda"
        ),
        pytest.param(
            ["vader = subprocess:run"], ["vader"], id="vader-imports-vader"
        ),
        pytest.param(
            ["yoda = os.path:join", "vader = subprocess:run"],
            ["yoda", "vader"],
            id="yoda-vader-imports-yoda-vader",
        ),
    ],
)
def test_imports_system_wide(testapp, runprocessor, imports, registered):
    """Imports must work system wide."""

    for _ in runprocessor(testapp, [], imports=imports):
        pass

    # Test that out of two processors (i.e. 'yoda' and 'vader'), only expected
    # ones are registered in testapp instance.
    assert set(["yoda", "vader"]) & set(testapp._processors) == set(registered)


def test_imports_precedence(testapp, runprocessor, tmpdir, monkeypatch):
    """Imports must prefer packages from local fs."""

    tmpdir.join("subprocess.py").write_text(
        textwrap.dedent(
            """\
            def run(app, items):
                yield from items
        """
        ),
        encoding="UTF-8",
    )

    with monkeypatch.context() as patcher:
        # At this point, 'subprocess' must be already imported by pytest
        # internals or even Holocron. Since python do not re-import modules,
        # we need to ensure it's unloaded.
        patcher.delitem(sys.modules, "subprocess")

        for _ in runprocessor(
            testapp,
            [],
            imports=["yoda = subprocess:run"],
            from_=tmpdir.strpath,
        ):
            pass

    for _ in testapp.invoke([{"name": "yoda"}], []):
        pass
