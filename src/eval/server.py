from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from eval.db import fetch_all_runs, fetch_run_meta, fetch_run_results

_HTML: str = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>LLM Eval Harness</title>
<style>
  body { font-family: monospace; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
  h1 { font-size: 1.4rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
  th { background: #f4f4f4; }
  tr:hover { background: #fafafa; cursor: pointer; }
  #detail { margin-top: 2rem; white-space: pre-wrap; background: #f9f9f9;
            border: 1px solid #ddd; padding: 1rem; display: none; }
</style>
</head>
<body>
<h1>LLM Eval Harness — Runs</h1>
<table id="runs-table">
  <thead><tr>
    <th>ID</th><th>Created</th><th>Model</th><th>Scorer</th>
    <th>Rows</th><th>Avg Score</th>
  </tr></thead>
  <tbody id="runs-body"></tbody>
</table>
<div id="detail"></div>
<script>
async function loadRuns() {
  const resp = await fetch('/runs');
  const runs = await resp.json();
  const tbody = document.getElementById('runs-body');
  if (runs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">No runs yet.</td></tr>';
    return;
  }
  runs.forEach(r => {
    const tr = document.createElement('tr');
    const avg = r.avg_score != null ? r.avg_score.toFixed(3) : 'N/A';
    tr.innerHTML = `<td>${r.id}</td><td>${r.created_at}</td><td>${r.model}</td>`
      + `<td>${r.scorer}</td><td>${r.row_count}</td><td>${avg}</td>`;
    tr.onclick = () => loadDetail(r.id);
    tbody.appendChild(tr);
  });
}
async function loadDetail(id) {
  const resp = await fetch('/runs/' + id);
  const data = await resp.json();
  const box = document.getElementById('detail');
  box.style.display = 'block';
  box.textContent = JSON.stringify(data, null, 2);
}
loadRuns();
</script>
</body>
</html>"""


class RunSummary(BaseModel):
    id: int
    created_at: str
    model: str
    scorer: str
    row_count: int
    avg_score: float | None


class RowResult(BaseModel):
    input: str
    expected_output: str
    output: str
    score: float
    latency_ms: float


class RunDetail(BaseModel):
    id: int
    created_at: str
    model: str
    dataset: str
    prompt_template: str
    scorer: str
    rows: list[RowResult]


def create_app(db_path: str = "eval.db") -> FastAPI:
    app = FastAPI(title="LLM Eval Harness")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return _HTML

    @app.get("/runs", response_model=list[RunSummary])
    async def list_runs() -> list[RunSummary]:
        rows = await fetch_all_runs(db_path)
        return [RunSummary(**row) for row in rows]

    @app.get("/runs/{run_id}", response_model=RunDetail)
    async def get_run(run_id: int) -> RunDetail:
        meta = await fetch_run_meta(run_id, db_path)
        if meta is None:
            raise HTTPException(status_code=404, detail="Run not found")
        results = await fetch_run_results(run_id, db_path)
        return RunDetail(
            id=meta["id"],
            created_at=meta["created_at"],
            model=meta["model"],
            dataset=meta["dataset"],
            prompt_template=meta["prompt_template"],
            scorer=meta["scorer"],
            rows=[RowResult(**r) for r in results],
        )

    return app
