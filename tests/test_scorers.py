from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eval.scorers import exact_match, contains, llm_judge, get_scorer


# --- exact_match ---

def test_exact_match_hit():
    assert exact_match("Paris", "Paris") == 1.0


def test_exact_match_miss():
    assert exact_match("London", "Paris") == 0.0


def test_exact_match_case_insensitive():
    assert exact_match("paris", "Paris") == 1.0


def test_exact_match_strips_whitespace():
    assert exact_match("  Paris  ", "Paris") == 1.0


# --- contains ---

def test_contains_hit():
    assert contains("The capital is Paris.", "Paris") == 1.0


def test_contains_miss():
    assert contains("The capital is London.", "Paris") == 0.0


def test_contains_case_insensitive():
    assert contains("PARIS", "paris") == 1.0


# --- llm_judge ---

@pytest.mark.asyncio
async def test_llm_judge_returns_float():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "0.8"

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("eval.scorers.AsyncOpenAI", return_value=mock_client):
        result = await llm_judge("Paris is the capital.", "Paris")

    assert result == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_llm_judge_fallback_on_bad_response():
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "not a number"

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("eval.scorers.AsyncOpenAI", return_value=mock_client):
        result = await llm_judge("Paris is the capital.", "Paris")

    assert result == 0.0


# --- get_scorer ---

def test_get_scorer_builtin():
    assert get_scorer("exact_match") is exact_match


def test_get_scorer_unknown_raises():
    with pytest.raises(ValueError):
        get_scorer("nonexistent_scorer_xyz")


def test_get_scorer_plugin(tmp_path: Path, monkeypatch):
    scorers_dir = tmp_path / "scorers"
    scorers_dir.mkdir()
    plugin = scorers_dir / "my_scorer.py"
    plugin.write_text(
        "def my_scorer(output: str, expected: str) -> float:\n    return 0.5\n"
    )
    monkeypatch.chdir(tmp_path)

    fn = get_scorer("my_scorer")
    assert callable(fn)
    assert fn("a", "b") == 0.5
