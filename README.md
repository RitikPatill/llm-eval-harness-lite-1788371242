# llm-eval-harness-lite

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-M3%20async%20runner-yellow.svg)]()

> A minimal, self-contained evaluation harness for LLM outputs. Define datasets, prompt templates, and scorer functions — run against OpenAI or Anthropic models, score results, and inspect everything via a Rich CLI or FastAPI dashboard. Under 1000 lines. No cloud required.

---

## What works now (M3)

- `pip install -e .` installs the package from `src/eval/`
- `python -m eval run --dataset datasets/qa_sample.jsonl --prompt prompts/qa.j2 --model gpt-4o-mini --scorer exact_match` — **fully functional**: loads the dataset, renders Jinja2 prompts, calls the model async with a semaphore-limited concurrency of 5, persists run/prompt/response rows to SQLite, shows a Rich progress bar, and prints the run ID on completion
- `src/eval/adapters.py` — `OpenAIAdapter` and `AnthropicAdapter` behind a `ModelAdapter` protocol; routed by `get_adapter(model)`; latency measured via `time.perf_counter()`
- `src/eval/templates.py` — `load_template()` + `render()` using `jinja2.StrictUndefined` (typos in template vars raise loudly)
- `prompts/qa.j2` — sample Jinja2 prompt template for factual Q&A
- `src/eval/runner.py` — `execute_run()`: async orchestration with `asyncio.Semaphore(5)`, single `aiosqlite` connection shared across tasks, Rich progress bar
- `datasets/qa_sample.jsonl` — 10 factual Q&A pairs
- `src/eval/db.py` — `init_db()` + `get_db()` async context manager
- `src/eval/models.py` — Pydantic v2 models: `DatasetRow`, `RunRecord`, `ScoreRecord`
- `src/eval/dataset.py` — JSONL loader with per-line validation
- `pytest` passes **14 tests** (adapter mocks, template rendering, runner integration, data-layer, smoke)

---

## Why not HELM / lm-evaluation-harness / promptfoo?

| Framework | Problem |
|---|---|
| HELM | Requires cloud infrastructure, heavy setup |
| lm-evaluation-harness | Opinionated benchmarks, hard to add custom tasks |
| promptfoo | YAML-heavy, node.js runtime |
| **this** | Pure Python, one `pip install`, extend with a plain function |

---

## Architecture

```
datasets/          <- .jsonl files: {"input": "...", "expected_output": "..."}  [placeholder]
prompts/           <- Jinja2 templates: qa.j2, cot.j2, ...                      [placeholder]
scorers/           <- Custom scorer functions (plain Python)                     [placeholder]

src/eval/
  __init__.py      <- Package init, version string                               [exists]
  __main__.py      <- Click CLI: run (functional), show/compare (stubs)          [updated M3]
  py.typed         <- PEP 561 marker                                             [exists]
  db.py            <- SQLite init + get_db context manager (aiosqlite)           [exists M2]
  models.py        <- Pydantic v2: DatasetRow, RunRecord, ScoreRecord            [exists M2]
  dataset.py       <- load_dataset(): JSONL loader with validation               [exists M2]
  adapters.py      <- OpenAI + Anthropic adapters behind ModelAdapter protocol    [exists M3]
  templates.py     <- Jinja2 template loader + renderer (StrictUndefined)        [exists M3]
  runner.py        <- Async batch runner: semaphore, progress bar, SQLite writes  [exists M3]
  scorers.py       <- Built-in scorers: exact_match, contains, llm_judge         [planned M4]
  server.py        <- FastAPI dashboard                                          [planned M6]

datasets/
  qa_sample.jsonl  <- 10 factual Q&A pairs for testing                           [exists M2]

tests/
  test_package.py     <- Smoke tests: version string, CLI help                   [exists]
  test_data_layer.py  <- DB init + dataset loader tests                          [exists M2]
  test_adapters.py    <- Adapter unit tests with mocked clients                  [exists M3]
  test_runner.py      <- Runner integration tests with fake adapter              [exists M3]
  test_templates.py   <- Template render + StrictUndefined tests                 [exists M3]

eval.db            <- SQLite database (auto-created on first run)
```

**Flow:**

```
[dataset .jsonl]
      |
      v
[Jinja2 template] --> [rendered prompt]
                              |
                    +---------+---------+
                    |                   |
              [OpenAI adapter]  [Anthropic adapter]   (async, batched)
                    |                   |
                    +---------+---------+
                              |
                         [response]
                              |
                    [scorer function]  <-- exact_match / contains / llm_judge
                              |
                       [SQLite db]
                              |
              +---------------+---------------+
              |                               |
        [Rich CLI]                    [FastAPI /runs]
```

---

## CLI Usage

```bash
# Run an evaluation
python -m eval run \
  --dataset datasets/qa_sample.jsonl \
  --prompt prompts/qa.j2 \
  --model gpt-4o-mini \
  --scorer exact_match

# Show results for a specific run
python -m eval show --run-id 1

# Compare two runs side-by-side
python -m eval compare --run-ids 1 --run-ids 2
```

---

## FastAPI Endpoints (planned — M6)

| Method | Path | Description |
|---|---|---|
| `GET` | `/runs` | List all evaluation runs |
| `GET` | `/runs/{id}` | Full detail for one run |
| `GET` | `/runs/{id}/scores` | Score breakdown per sample |
| `GET` | `/` | HTML dashboard table |

Start the server:
```bash
python -m eval serve --port 8000
```

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as editable package (recommended for development)
pip install -e .

# Verify the install
python -m eval --help   # run is fully functional; show and compare are stubs until M5

# Run the test suite
pytest
```

Run a real eval now:

```bash
# Set API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Run an eval against OpenAI
python -m eval run \
  --dataset datasets/qa_sample.jsonl \
  --prompt prompts/qa.j2 \
  --model gpt-4o-mini \
  --scorer exact_match

# Or run against Anthropic
python -m eval run \
  --dataset datasets/qa_sample.jsonl \
  --prompt prompts/qa.j2 \
  --model claude-haiku-4-5 \
  --scorer exact_match

# Inspect results (M5)
python -m eval show --run-id 1

# Launch web dashboard (M6)
python -m eval serve
```

---

## Adding Your Own Scorer

Drop a Python file in `scorers/`:

```python
# scorers/my_scorer.py
def score(response: str, expected: str) -> float:
    """Return a float between 0.0 and 1.0."""
    return 1.0 if response.strip() == expected.strip() else 0.0
```

Then use `--scorer my_scorer` on the CLI.

---

## Dataset Format

Each line in a `.jsonl` file:

```json
{"input": "What is the capital of France?", "expected_output": "Paris"}
{"input": "2 + 2 = ?", "expected_output": "4"}
```

---

## Prompt Template Format

Jinja2 templates in `prompts/`:

```
{# prompts/qa.j2 #}
Answer the following question concisely.

Question: {{ input }}
Answer:
```

---

## Roadmap

| Milestone | Description | Status |
|---|---|---|
| M1 | Scaffold, README, pyproject.toml, LICENSE | ✅ done |
| M2 | Data layer (SQLite schema, Pydantic models, JSONL loader) + CLI skeleton | ✅ done |
| M3 | Model adapters (OpenAI + Anthropic), async runner | ✅ done |
| M4 | Scorer functions: exact_match, contains, llm_judge | ⏳ planned |
| M5 | Rich CLI output (progress bars, coloured tables) | ⏳ planned |
| M6 | FastAPI dashboard + README demo GIF | ⏳ planned |

---

## License

[MIT](LICENSE) — Copyright 2024 Ritik
