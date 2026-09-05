from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import aiosqlite
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from eval.adapters import get_adapter, ModelAdapter
from eval.dataset import load_dataset
from eval.db import init_db, get_db
from eval.scorers import get_scorer
from eval.templates import load_template, render


async def _call_one(
    semaphore: asyncio.Semaphore,
    adapter: ModelAdapter,
    prompt_id: int,
    rendered: str,
    expected_output: str,
    scorer_fn,
    conn: aiosqlite.Connection,
    progress: Progress,
    task_id: int,
) -> None:
    async with semaphore:
        output, latency_ms = await adapter.complete(rendered)
        cur = await conn.execute(
            "INSERT INTO responses (prompt_id, output, latency_ms) VALUES (?, ?, ?)",
            (prompt_id, output, latency_ms),
        )
        response_id = cur.lastrowid
        await conn.commit()

        if asyncio.iscoroutinefunction(scorer_fn):
            score = await scorer_fn(output, expected_output)
        else:
            score = scorer_fn(output, expected_output)

        await conn.execute(
            "INSERT INTO scores (response_id, scorer, score, metadata) VALUES (?, ?, ?, ?)",
            (response_id, scorer_fn.__name__, score, "{}"),
        )
        await conn.commit()
        progress.advance(task_id)


async def execute_run(
    dataset_path: str,
    prompt_path: str,
    model: str,
    scorer: str,
    db_path: str,
) -> int:
    """Orchestrate a full eval run and return the run_id."""
    await init_db(db_path)
    rows = load_dataset(dataset_path)
    template = load_template(prompt_path)
    scorer_fn = get_scorer(scorer)

    async with get_db(db_path) as conn:
        cursor = await conn.execute(
            """
            INSERT INTO runs (created_at, model, dataset, prompt_template, scorer)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                model,
                dataset_path,
                prompt_path,
                scorer,
            ),
        )
        await conn.commit()
        run_id = cursor.lastrowid

        adapter = get_adapter(model)
        semaphore = asyncio.Semaphore(5)

        # Insert all prompts first and collect (prompt_id, rendered, expected_output) tuples
        prompt_entries: list[tuple[int, str, str]] = []
        for row in rows:
            rendered = render(template, row)
            cur = await conn.execute(
                "INSERT INTO prompts (run_id, input, rendered, expected_output) VALUES (?, ?, ?, ?)",
                (run_id, row.input, rendered, row.expected_output),
            )
            await conn.commit()
            prompt_entries.append((cur.lastrowid, rendered, row.expected_output))

        with Progress(
            SpinnerColumn(),
            "[progress.description]{task.description}",
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
        ) as progress:
            task_id = progress.add_task(
                f"[cyan]Running {model}…", total=len(prompt_entries)
            )
            tasks = [
                _call_one(semaphore, adapter, pid, rendered, expected, scorer_fn, conn, progress, task_id)
                for pid, rendered, expected in prompt_entries
            ]
            await asyncio.gather(*tasks)

    return run_id
