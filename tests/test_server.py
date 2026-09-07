from __future__ import annotations

import asyncio

import aiosqlite
import pytest
from starlette.testclient import TestClient

from eval.db import init_db
from eval.server import create_app


# ---------------------------------------------------------------------------
# Seed helper
# ---------------------------------------------------------------------------

def seed_db(db_path: str) -> None:
    asyncio.run(_seed(db_path))


async def _seed(db_path: str) -> None:
    await init_db(db_path)
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(
            """INSERT INTO runs (created_at, model, dataset, prompt_template, scorer)
               VALUES ('2024-01-01T00:00:00', 'gpt-4o-mini', 'qa.jsonl', 'qa.j2', 'exact_match')"""
        )
        await conn.execute(
            "INSERT INTO prompts (run_id, input, rendered, expected_output) VALUES (1, 'Q?', 'Q?', 'A')"
        )
        await conn.execute(
            "INSERT INTO responses (prompt_id, output, latency_ms) VALUES (1, 'A', 123.0)"
        )
        await conn.execute(
            "INSERT INTO scores (response_id, scorer, score) VALUES (1, 'exact_match', 1.0)"
        )
        await conn.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_index_returns_html(tmp_path):
    db = str(tmp_path / "test.db")
    asyncio.run(init_db(db))
    client = TestClient(create_app(db_path=db))
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_runs_empty_db(tmp_path):
    db = str(tmp_path / "test.db")
    asyncio.run(init_db(db))
    client = TestClient(create_app(db_path=db))
    resp = client.get("/runs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_runs_after_seed(tmp_path):
    db = str(tmp_path / "test.db")
    seed_db(db)
    client = TestClient(create_app(db_path=db))
    resp = client.get("/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["model"] == "gpt-4o-mini"
    assert data[0]["row_count"] == 1
    assert data[0]["avg_score"] == pytest.approx(1.0)


def test_run_detail(tmp_path):
    db = str(tmp_path / "test.db")
    seed_db(db)
    client = TestClient(create_app(db_path=db))
    resp = client.get("/runs/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["model"] == "gpt-4o-mini"
    assert len(data["rows"]) == 1
    row = data["rows"][0]
    assert row["input"] == "Q?"
    assert row["expected_output"] == "A"
    assert row["output"] == "A"
    assert row["score"] == pytest.approx(1.0)


def test_run_not_found(tmp_path):
    db = str(tmp_path / "test.db")
    asyncio.run(init_db(db))
    client = TestClient(create_app(db_path=db))
    resp = client.get("/runs/999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Run not found"
