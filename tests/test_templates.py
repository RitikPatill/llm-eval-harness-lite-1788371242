from __future__ import annotations

from pathlib import Path

import jinja2
import pytest

from eval.models import DatasetRow
from eval.templates import load_template, render


def test_render_injects_input(tmp_path: Path):
    tmpl_file = tmp_path / "test.j2"
    tmpl_file.write_text("Q: {{ input }}\nA:")
    template = load_template(tmpl_file)
    row = DatasetRow(input="What is 2+2?", expected_output="4")
    result = render(template, row)
    assert "What is 2+2?" in result


def test_render_injects_expected_output(tmp_path: Path):
    tmpl_file = tmp_path / "test.j2"
    tmpl_file.write_text("Expected: {{ expected_output }}")
    template = load_template(tmpl_file)
    row = DatasetRow(input="q", expected_output="42")
    result = render(template, row)
    assert "42" in result


def test_strict_undefined_raises_on_unknown_var(tmp_path: Path):
    tmpl_file = tmp_path / "bad.j2"
    tmpl_file.write_text("{{ nonexistent_variable }}")
    template = load_template(tmpl_file)
    row = DatasetRow(input="q", expected_output="a")
    with pytest.raises(jinja2.UndefinedError):
        render(template, row)
