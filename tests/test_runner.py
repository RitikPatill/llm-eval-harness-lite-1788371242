from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiosqlite
import pytest

from eval.runner import execute_run


class _FakeAdapter:
    async def complete(self, prompt: str) -> tuple[str, float]:
        return ("fake answer", 10.0)


async def test_execute_run_persists_to_db(tmp_path: Path, monkeypatch):
    db_path = str(tmp_path / "test.db")

    dataset_path = str(Path("datasets/qa_sample.jsonl").resolve())
    prompt_path = str(Path("prompts/qa.j2").resolve())

    monkeypatch.setattr("eval.runner.get_adapter", lambda model: _FakeAdapter())

    run_id = await execute_run(
        dataset_path=dataset_path,
        prompt_path=prompt_path,
        model="gpt-4o-mini",
        scorer="exact_match",
        db_path=db_path,
    )

    assert run_id == 1

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM runs")
        (run_count,) = await cursor.fetchone()

        cursor = await conn.execute("SELECT COUNT(*) FROM prompts")
        (prompt_count,) = await cursor.fetchone()

        cursor = await conn.execute("SELECT COUNT(*) FROM responses")
        (response_count,) = await cursor.fetchone()

    assert run_count == 1
    assert prompt_count == 10
    assert response_count == 10


async def test_execute_run_stores_scorer(tmp_path: Path, monkeypatch):
    db_path = str(tmp_path / "test2.db")
    dataset_path = str(Path("datasets/qa_sample.jsonl").resolve())
    prompt_path = str(Path("prompts/qa.j2").resolve())

    monkeypatch.setattr("eval.runner.get_adapter", lambda model: _FakeAdapter())

    await execute_run(
        dataset_path=dataset_path,
        prompt_path=prompt_path,
        model="gpt-4o-mini",
        scorer="contains",
        db_path=db_path,
    )

    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("SELECT scorer FROM runs WHERE id = 1")
        (scorer,) = await cursor.fetchone()

    assert scorer == "contains"
