import asyncio

import click
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from eval.db import fetch_run_results, fetch_run_meta
from eval.runner import execute_run

console = Console()


def _fmt_score(score: float) -> str:
    s = f"{score:.2f}"
    if score >= 0.8:
        return f"[green]{s}[/green]"
    if score >= 0.5:
        return f"[yellow]{s}[/yellow]"
    return f"[red]{s}[/red]"


def _trunc(text: str, n: int = 60) -> str:
    return text[:n] + "…" if len(text) > n else text


@click.group()
def cli():
    """LLM Eval Harness Lite."""
    pass


@cli.command()
@click.option("--dataset", required=True, type=click.Path(exists=True))
@click.option("--prompt", required=True, type=click.Path(exists=True))
@click.option("--model", required=True)
@click.option("--scorer", required=True)
@click.option("--db", default="eval.db", show_default=True)
def run(dataset, prompt, model, scorer, db):
    """Run an evaluation."""
    run_id = asyncio.run(execute_run(dataset, prompt, model, scorer, db))
    rprint(f"[green]Run {run_id} complete.[/green]")


@cli.command()
@click.option("--run-id", required=True, type=int)
@click.option("--db", default="eval.db", show_default=True)
def show(run_id, db):
    """Show results for a specific run."""
    asyncio.run(_show(run_id, db))


async def _show(run_id: int, db_path: str) -> None:
    rows = await fetch_run_results(run_id, db_path)
    meta = await fetch_run_meta(run_id, db_path)

    if not rows:
        rprint(f"[yellow]No results found for run {run_id}.[/yellow]")
        return

    table = Table(title=f"Run {run_id}", show_lines=True)
    table.add_column("Input", style="cyan", no_wrap=False)
    table.add_column("Expected", style="dim")
    table.add_column("Actual", no_wrap=False)
    table.add_column("Score", justify="right")

    for row in rows:
        table.add_row(
            _trunc(row["input"]),
            _trunc(row["expected_output"]),
            _trunc(row["output"]),
            _fmt_score(row["score"]),
        )

    console.print(table)

    avg_score = sum(r["score"] for r in rows) / len(rows)
    model = meta["model"] if meta else "unknown"
    rprint(
        f"Run {run_id} | {model} | {len(rows)} rows | avg score: [bold]{avg_score:.2f}[/bold]"
    )


@cli.command()
@click.option("--run-ids", required=True, help="Comma-separated run IDs, e.g. 1,2")
@click.option("--db", default="eval.db", show_default=True)
def compare(run_ids, db):
    """Compare two runs side-by-side."""
    ids = [int(x.strip()) for x in run_ids.split(",")]
    asyncio.run(_compare(ids, db))


async def _compare(ids: list[int], db_path: str) -> None:
    if len(ids) < 2:
        rprint("[red]Provide at least two run IDs.[/red]")
        return

    id_a, id_b = ids[0], ids[1]
    rows_a = await fetch_run_results(id_a, db_path)
    rows_b = await fetch_run_results(id_b, db_path)
    meta_a = await fetch_run_meta(id_a, db_path)
    meta_b = await fetch_run_meta(id_b, db_path)

    # Index by input text
    index_a = {r["input"]: r for r in rows_a}
    index_b = {r["input"]: r for r in rows_b}
    all_inputs = list(dict.fromkeys(
        [r["input"] for r in rows_a] + [r["input"] for r in rows_b]
    ))

    model_a = meta_a["model"] if meta_a else f"Run {id_a}"
    model_b = meta_b["model"] if meta_b else f"Run {id_b}"

    table = Table(title=f"Compare Run {id_a} vs Run {id_b}", show_lines=True)
    table.add_column("Input", style="cyan")
    table.add_column("Expected", style="dim")
    table.add_column(f"Run {id_a} ({model_a})", no_wrap=False)
    table.add_column(f"Score A", justify="right")
    table.add_column(f"Run {id_b} ({model_b})", no_wrap=False)
    table.add_column(f"Score B", justify="right")

    for inp in all_inputs:
        ra = index_a.get(inp)
        rb = index_b.get(inp)
        expected = (ra or rb)["expected_output"] if (ra or rb) else ""
        table.add_row(
            _trunc(inp),
            _trunc(expected),
            _trunc(ra["output"]) if ra else "—",
            _fmt_score(ra["score"]) if ra else "—",
            _trunc(rb["output"]) if rb else "—",
            _fmt_score(rb["score"]) if rb else "—",
        )

    console.print(table)


if __name__ == "__main__":
    cli()
