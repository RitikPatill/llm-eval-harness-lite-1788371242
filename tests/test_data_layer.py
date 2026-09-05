import json

import pytest

from eval.dataset import load_dataset
from eval.db import init_db


async def _table_names(db_path) -> set[str]:
    import aiosqlite
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        rows = await cursor.fetchall()
    return {row[0] for row in rows}


@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    await init_db(db_path)
    tables = await _table_names(db_path)
    assert {"runs", "prompts", "responses", "scores"}.issubset(tables)


@pytest.mark.asyncio
async def test_load_dataset_valid(tmp_path):
    jsonl = tmp_path / "data.jsonl"
    jsonl.write_text(
        json.dumps({"input": "Q1", "expected_output": "A1"}) + "\n"
        + json.dumps({"input": "Q2", "expected_output": "A2"}) + "\n"
    )
    rows = load_dataset(jsonl)
    assert len(rows) == 2
    assert rows[0].input == "Q1"
    assert rows[0].expected_output == "A1"
    assert rows[1].input == "Q2"


@pytest.mark.asyncio
async def test_load_dataset_invalid_row(tmp_path):
    jsonl = tmp_path / "bad.jsonl"
    jsonl.write_text(
        json.dumps({"input": "Q1", "expected_output": "A1"}) + "\n"
        + json.dumps({"input": "missing_expected"}) + "\n"
    )
    with pytest.raises(ValueError, match="line 2"):
        load_dataset(jsonl)
