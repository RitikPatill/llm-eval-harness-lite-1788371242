"""Tests for the `eval init` CLI command."""
import json

from click.testing import CliRunner

from eval.__main__ import cli


def test_init_creates_directory(tmp_path):
    target = tmp_path / "new-project"
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(target)])
    assert result.exit_code == 0, result.output
    assert target.is_dir()


def test_init_creates_dataset(tmp_path):
    target = tmp_path / "new-project"
    runner = CliRunner()
    runner.invoke(cli, ["init", str(target)])
    dataset = target / "datasets" / "sample.jsonl"
    assert dataset.exists()
    lines = dataset.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    for line in lines:
        row = json.loads(line)
        assert "input" in row
        assert "expected_output" in row


def test_init_creates_prompt(tmp_path):
    target = tmp_path / "new-project"
    runner = CliRunner()
    runner.invoke(cli, ["init", str(target)])
    prompt = target / "prompts" / "qa.j2"
    assert prompt.exists()
    assert "{{ input }}" in prompt.read_text(encoding="utf-8")


def test_init_creates_scorer_stub(tmp_path):
    target = tmp_path / "new-project"
    runner = CliRunner()
    runner.invoke(cli, ["init", str(target)])
    scorer = target / "scorers" / "my_scorer.py"
    assert scorer.exists()
    content = scorer.read_text(encoding="utf-8")
    assert "def my_scorer" in content
    assert "float" in content


def test_init_creates_env_example(tmp_path):
    target = tmp_path / "new-project"
    runner = CliRunner()
    runner.invoke(cli, ["init", str(target)])
    env_example = target / ".env.example"
    assert env_example.exists()
    assert "OPENAI_API_KEY" in env_example.read_text(encoding="utf-8")


def test_init_refuses_existing_nonempty_dir(tmp_path):
    target = tmp_path / "existing"
    target.mkdir()
    (target / "somefile.txt").write_text("occupied", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(cli, ["init", str(target)])
    assert result.exit_code != 0 or "not empty" in result.output
