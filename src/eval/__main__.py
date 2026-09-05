import asyncio

import click
from rich import print as rprint

from eval.runner import execute_run


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
    rprint(f"[stub] show called with run_id={run_id!r}, db={db!r}")


@cli.command()
@click.option("--run-ids", required=True, multiple=True, type=int)
@click.option("--db", default="eval.db", show_default=True)
def compare(run_ids, db):
    """Compare multiple runs side-by-side."""
    rprint(f"[stub] compare called with run_ids={run_ids!r}, db={db!r}")


if __name__ == "__main__":
    cli()
