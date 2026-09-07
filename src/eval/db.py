from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import aiosqlite


async def init_db(db_path: str | Path) -> None:
    """Create all tables if they don't exist."""
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at       TEXT    NOT NULL,
                model            TEXT    NOT NULL,
                dataset          TEXT    NOT NULL,
                prompt_template  TEXT    NOT NULL,
                scorer           TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prompts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          INTEGER NOT NULL REFERENCES runs(id),
                input           TEXT    NOT NULL,
                rendered        TEXT    NOT NULL,
                expected_output TEXT    NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS responses (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id  INTEGER NOT NULL REFERENCES prompts(id),
                output     TEXT    NOT NULL,
                latency_ms REAL    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scores (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER NOT NULL REFERENCES responses(id),
                scorer      TEXT    NOT NULL,
                score       REAL    NOT NULL,
                metadata    TEXT    NOT NULL DEFAULT '{}'
            );
        """)
        # Safe migration for existing DBs that lack expected_output column
        try:
            await conn.execute(
                "ALTER TABLE prompts ADD COLUMN expected_output TEXT NOT NULL DEFAULT ''"
            )
            await conn.commit()
        except Exception:
            pass  # Column already exists
        await conn.commit()


@asynccontextmanager
async def get_db(db_path: str | Path) -> AsyncIterator[aiosqlite.Connection]:
    """Async context manager yielding an open aiosqlite connection."""
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA foreign_keys = ON")
        yield conn


async def fetch_run_results(run_id: int, db_path: str | Path) -> list[dict]:
    """Return list of dicts with keys: input, expected_output, output, score, latency_ms."""
    async with get_db(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT p.input, p.expected_output, r.output, s.score, r.latency_ms
            FROM prompts p
            JOIN responses r ON r.prompt_id = p.id
            JOIN scores s ON s.response_id = r.id
            WHERE p.run_id = ?
            ORDER BY p.id
            """,
            (run_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def fetch_all_runs(db_path: str | Path) -> list[dict]:
    """Return list of run summaries with aggregate scores."""
    async with get_db(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("""
            SELECT r.id, r.created_at, r.model, r.dataset, r.scorer,
                   COUNT(s.id)  AS row_count,
                   AVG(s.score) AS avg_score
            FROM runs r
            LEFT JOIN prompts p     ON p.run_id      = r.id
            LEFT JOIN responses res ON res.prompt_id = p.id
            LEFT JOIN scores s      ON s.response_id = res.id
            GROUP BY r.id
            ORDER BY r.id DESC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def fetch_run_meta(run_id: int, db_path: str | Path) -> dict | None:
    """Return run metadata dict or None if not found."""
    async with get_db(db_path) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
