"""Tests Holocron CLI."""

import os
import sys
import textwrap
import subprocess

import mock
import pytest
import yaml


@pytest.fixture(scope="function")
def create_site(tmpdir):
    def create(structure):
        for path, content in structure:
            tmpdir.ensure(path).write_binary(content)

    return create


@pytest.fixture(scope="function")
def example_site(create_site):
    holocron_yml = yaml.safe_dump(
        {
            "metadata": {"url": "https://yoda.ua"},
            "pipes": {"test": [{"name": "source"}, {"name": "save"}]},
        },
        encoding="UTF-8",
        default_flow_style=False,
    )

    return create_site(
        [
            (os.path.join("cv.md"), b"yoda"),
            (os.path.join("about", "photo.png"), b""),
            (
                os.path.join("2019", "02", "12", "skywalker", "index.html"),
                b"luke",
            ),
            (os.path.join(".holocron.yml"), holocron_yml),
        ]
    )


@pytest.fixture(scope="function")
def execute(capsys):
    def execute(args, as_subprocess=True):
        if as_subprocess:
            return subprocess.check_output(
                ["holocron"] + args, stderr=subprocess.PIPE
            )

        from holocron.__main__ import main

        main(args)
        return capsys.readouterr().out

    return execute


def test_run_progress_info(monkeypatch, tmpdir, execute, example_site):
    """Built items are shown on standard output."""

    monkeypatch.chdir(tmpdir)

    assert set(execute(["run", "test"]).splitlines()) == {
        b"==> .holocron.yml",
        b"==> cv.md",
        b"==> 2019/02/12/skywalker/index.html",
        b"==> about/photo.png",
    }


def test_run_progress_info_colored(monkeypatch, tmpdir, execute, example_site):
    """Built items are shown and colorized on standard output."""

    # colorama strips away ANSI escape sequences if a standard output is not
    # connected to a tty; since pytest mocks standard i/o streams, these mocked
    # streams have to be patches to simulate tty connection.
    monkeypatch.setattr(sys.stdout, "isatty", mock.Mock(return_value=True))
    monkeypatch.chdir(tmpdir)

    assert set(execute(["run", "test"], as_subprocess=False).splitlines()) == {
        "\x1b[1m\x1b[32m==>\x1b[0m \x1b[1m.holocron.yml\x1b[0m",
        "\x1b[1m\x1b[32m==>\x1b[0m \x1b[1mcv.md\x1b[0m",
        "\x1b[1m\x1b[32m==>\x1b[0m "
        "\x1b[1m2019/02/12/skywalker/index.html\x1b[0m",
        "\x1b[1m\x1b[32m==>\x1b[0m \x1b[1mabout/photo.png\x1b[0m",
    }


def test_run_conf_yml_not_found(monkeypatch, tmpdir, execute, example_site):
    """Proceed with default settings."""

    monkeypatch.chdir(tmpdir)
    tmpdir.join(".holocron.yml").remove()

    # Because Holocron has no built-in pipes, there's nothing we can run and
    # thus exception is expected.
    with pytest.raises(subprocess.CalledProcessError):
        execute(["run", "test"])


def test_run_conf_yml_malformed(monkeypatch, tmpdir, execute, example_site):
    """Error message is printed."""

    monkeypatch.chdir(tmpdir)
    tmpdir.join(".holocron.yml").write_text(
        textwrap.dedent(
            """\
                metadata:
                  crap
                  key: value
            """
        ),
        encoding="UTF-8",
    )

    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        execute(["run", "test"])

    assert str(excinfo.value.stderr.decode("UTF-8").strip()) == (
        "Cannot parse a configuration file. Context: mapping values are not "
        "allowed here\n"
        '  in ".holocron.yml", line 3, column 6'
    )


def test_run_conf_yml_directory(monkeypatch, tmpdir, execute, example_site):
    """Error message is printed."""

    monkeypatch.chdir(tmpdir)
    tmpdir.join(".holocron.yml").remove()
    tmpdir.mkdir(".holocron.yml")

    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        execute(["run", "test"])

    assert (
        str(excinfo.value.stderr.decode("UTF-8").strip())
        == "[Errno 21] Is a directory: '.holocron.yml'"
    )


def test_run_conf_yml_interpolate(monkeypatch, tmpdir, execute):
    """Values such as '%(here)s' are interpolated."""

    monkeypatch.chdir(tmpdir)
    tmpdir.join(".holocron.yml").write_binary(
        yaml.safe_dump(
            {
                "metadata": {"url": "https://yoda.ua"},
                "pipes": {
                    "test": [
                        {"name": "source"},
                        {
                            "name": "metadata",
                            "metadata": {"content": "%(here)s/secret"},
                        },
                        {"name": "save"},
                    ]
                },
            },
            encoding="UTF-8",
            default_flow_style=False,
        )
    )
    tmpdir.join("test.txt").write_binary(b"")

    execute(["run", "test"])

    assert (
        tmpdir.join("_site", "test.txt").read_text(encoding="UTF-8")
        == tmpdir.join("secret").strpath
    )


def test_run_conf_yml_interpolate_in_path(
    monkeypatch, tmpdir, execute, example_site
):
    """Values such as '%(here)s' are interpolated."""

    tmpdir.join(".holocron.yml").write_binary(
        yaml.safe_dump(
            {
                "metadata": {"url": "https://yoda.ua"},
                "pipes": {
                    "test": [
                        {"name": "source", "path": "%(here)s"},
                        {"name": "save", "to": "%(here)s/_compiled"},
                    ]
                },
            },
            encoding="UTF-8",
            default_flow_style=False,
        )
    )

    execute(["-c", tmpdir.join(".holocron.yml").strpath, "run", "test"])

    assert tmpdir.join("_compiled", "cv.md").read_binary() == b"yoda"
