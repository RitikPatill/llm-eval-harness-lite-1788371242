from click.testing import CliRunner
from eval import __version__
from eval.__main__ import cli


def test_version_string():
    assert __version__ == "0.1.0"


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "LLM Eval Harness Lite" in result.output
