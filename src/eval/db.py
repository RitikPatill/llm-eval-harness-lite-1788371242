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
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id   INTEGER NOT NULL REFERENCES runs(id),
                input    TEXT    NOT NULL,
                rendered TEXT    NOT NULL
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
        await conn.commit()


@asynccontextmanager
async def get_db(db_path: str | Path) -> AsyncIterator[aiosqlite.Connection]:
    """Async context manager yielding an open aiosqlite connection."""
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute("PRAGMA foreign_keys = ON")
        yield conn
