# LLM Eval Harness Lite

> A lightweight, local-first framework for evaluating LLM outputs with custom scorers, prompt templates, and a CLI dashboard.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![CI](https://github.com/rk-vashista/llm-eval-harness-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/rk-vashista/llm-eval-harness-lite/actions/workflows/ci.yml)

<!-- TODO: replace with a 5-10 second demo gif. Record with ScreenToGif on
     Windows or peek on macOS. Save to docs/demo.gif and update path here. -->
![demo](docs/demo.gif)

---

## What it is

`llm-eval-harness-lite` is a self-contained evaluation harness for LLM outputs. You supply a JSONL dataset of `{input, expected_output}` pairs, a Jinja2 prompt template, and a scorer function. The harness sends your prompts to OpenAI or Anthropic models via async batched calls, scores each response, and writes every run, response, and score to a local SQLite database.

Results are surfaced through two interfaces: a Rich CLI with coloured tables and progress bars, and a FastAPI server with JSON endpoints and an HTML summary page. The entire implementation is under 1000 lines of Python — no cloud infrastructure, no proprietary config format, no framework lock-in.

---

## Quickstart

```bash
git clone https://github.com/rk-vashista/llm-eval-harness-lite.git
cd llm-eval-harness-lite
pip install -e .

# Set at least one API key
export OPENAI_API_KEY=sk-...          # for gpt-4o-mini
# export ANTHROPIC_API_KEY=sk-ant-... # for claude-haiku-4-5

# Scaffold a ready-to-run project
eval init my-project
cd my-project

# Run an evaluation
eval run --dataset datasets/sample.jsonl \
         --prompt prompts/qa.j2 \
         --model gpt-4o-mini \
         --scorer exact_match

# Inspect results
eval show --run-id 1
```

---

## Usage

**CLI commands**

| Command | What it does |
|---|---|
| `eval init [DIR]` | Scaffold a project skeleton with a sample dataset, prompt, and scorer stub |
| `eval run` | Run an eval: async API calls, scoring, SQLite persistence |
| `eval show --run-id N` | Print a coloured per-row score table for run N |
| `eval compare --run-ids N,M` | Side-by-side score table for two runs |
| `eval serve` | Start the FastAPI dashboard at `http://127.0.0.1:8000` |

**Custom scorer** — drop a `.py` file in `scorers/` with a function matching the filename stem:

```python
# scorers/my_scorer.py
def my_scorer(output: str, expected: str) -> float:
    return 1.0 if output.strip() == expected.strip() else 0.0
```

Pass `--scorer my_scorer` on the CLI. No registration step needed.

**Web dashboard** — `eval serve` exposes `GET /runs` (JSON list) and `GET /runs/{id}` (JSON detail with per-row results), plus a minimal HTML table at `/`.

```bash
eval serve --port 9000 --db my_run.db
curl http://127.0.0.1:9000/runs
```

---

## Architecture

```
+----------------+    JSONL     +-------------+
|  CLI / Web     |------------->|   Dataset   |
|  (Click +      |              |   Loader    |
|   FastAPI)     |              +------+------+
+------+---------+                     |
       |                               | DatasetRow[]
       | eval run                      v
       |              +--------------------------------+
       |              |   Runner (asyncio +            |
       |              |   Semaphore(5))                |
       |              |  +------------+  +---------+  |
       |              |  |  Adapter   |  | Scorer  |  |
       |              |  | (OAI/ANT)  |  | (plugin)|  |
       |              |  +------------+  +---------+  |
       |              +----------------+---------------+
       |                               |
       v                               v scores
+----------------------------------------------+
|          SQLite  (aiosqlite)                 |
|  runs  |  prompts  |  responses  |  scores   |
+----------------------------------------------+
              |                   |
        +-----+-----+       +-----+-----+
        | Rich CLI  |       | FastAPI   |
        | (show,    |       | /runs     |
        | compare)  |       | /runs/{id}|
        +-----------+       +-----------+
```

---

## Project structure

```
datasets/          JSONL files: {"input": "...", "expected_output": "..."}
prompts/           Jinja2 templates (e.g. qa.j2)
scorers/           Scorer plugins: drop a .py file here, auto-discovered

src/eval/
  __main__.py      Click CLI: init, run, show, compare, serve
  adapters.py      OpenAI + Anthropic adapters behind a ModelAdapter protocol
  runner.py        Async batch runner with semaphore, progress bar, SQLite writes
  scorers.py       Built-in scorers: exact_match, contains, llm_judge
  templates.py     Jinja2 loader and renderer (StrictUndefined)
  dataset.py       JSONL loader with Pydantic validation
  db.py            SQLite schema init and aiosqlite context manager
  models.py        Pydantic v2: DatasetRow, RunRecord, ScoreRecord
  server.py        FastAPI: /runs, /runs/{id}, HTML page

tests/             37 tests; all pass with mocked API calls (no keys needed)
.github/           GitHub Actions CI matrix: Python 3.10 + 3.12
demo.tape          VHS script to record demo.gif (run: vhs demo.tape)
```

---

## Roadmap

- [ ] Local model support via Ollama (no API key required)
- [ ] Export run results to CSV or JSON for downstream analysis
- [ ] Parallel scorer execution for large datasets
- [ ] Basic statistical comparison (mean, std, confidence interval) in `eval compare`
- [ ] Web UI run filtering and score trend charts

---

## License

MIT — see [LICENSE](LICENSE).

---

Built autonomously by [autodev](https://github.com/RitikPatill/autodev),
a multi-agent orchestrator I designed. Each commit in this repo was
authored by me; the implementation work was performed by Sonnet under
the orchestrator's control. Read the orchestrator's README to see how.
