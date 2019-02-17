"""Tests Holocron CLI."""

import os
import sys

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
    config_yml = yaml.safe_dump({
        "metadata": {
            "url": "https://yoda.ua",
        },
        "pipes": {
            "test": [
                {"name": "source"},
                {"name": "commit"},
            ],
        },
    }, encoding="UTF-8", default_flow_style=False)

    return create_site([
        (os.path.join("cv.md"), b"yoda"),
        (os.path.join("about", "photo.png"), b""),
        (os.path.join("2019", "02", "12", "skywalker", "index.html"), b"luke"),
        (os.path.join("_config.yml"), config_yml),
    ])


@pytest.fixture(scope="function")
def execute(capsys):
    def execute(args, as_subprocess=True):
        if as_subprocess:
            import subprocess
            return subprocess.check_output(["holocron"] + args)

        from holocron.__main__ import main
        main(args)
        return capsys.readouterr().out
    return execute


def test_progress_info(monkeypatch, tmpdir, execute, example_site):
    """Built items are shown on standard output."""

    monkeypatch.chdir(tmpdir)

    assert set(execute(["run", "test"]).splitlines()) == {
        b"==> _config.yml",
        b"==> cv.md",
        b"==> 2019/02/12/skywalker/index.html",
        b"==> about/photo.png",
    }


def test_progress_info_colored(monkeypatch, tmpdir, execute, example_site):
    """Built items are shown and colorized on standard output."""

    # colorama strips away ANSI escape sequences if a standard output is not
    # connected to a tty; since pytest mocks standard i/o streams, these mocked
    # streams have to be patches to simulate tty connection.
    monkeypatch.setattr(sys.stdout, "isatty", mock.Mock(return_value=True))
    monkeypatch.chdir(tmpdir)

    assert set(execute(["run", "test"], as_subprocess=False).splitlines()) == {
        "\x1b[1m\x1b[32m==>\x1b[0m \x1b[1m_config.yml\x1b[0m",
        "\x1b[1m\x1b[32m==>\x1b[0m \x1b[1mcv.md\x1b[0m",
        "\x1b[1m\x1b[32m==>\x1b[0m "
        "\x1b[1m2019/02/12/skywalker/index.html\x1b[0m",
        "\x1b[1m\x1b[32m==>\x1b[0m \x1b[1mabout/photo.png\x1b[0m",
    }
