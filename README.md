# llm-eval-harness-lite

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-M1%20scaffold-yellow.svg)]()

> A minimal, self-contained evaluation harness for LLM outputs. Define datasets, prompt templates, and scorer functions — run against OpenAI or Anthropic models, score results, and inspect everything via a Rich CLI or FastAPI dashboard. Under 1000 lines. No cloud required.

---

## What works now (M1)

The repository scaffold is in place. These things work today:

- `pip install -e .` installs the package from `src/eval/`
- `python -m eval --help` prints the CLI group (no sub-commands yet)
- `pytest` passes two smoke tests (version string, CLI help exit code)
- All runtime and dev dependencies are pinned in `requirements.txt` and declared in `pyproject.toml`

The directories `datasets/`, `prompts/`, and `scorers/` exist as empty placeholders. The source modules (`runner.py`, `scorers.py`, `db.py`, `models.py`, `server.py`) are planned but not yet written.

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
  __main__.py      <- Click CLI entry point (stub group, no commands yet)        [exists]
  py.typed         <- PEP 561 marker                                             [exists]
  runner.py        <- Async batch model calls (OpenAI + Anthropic)               [planned M3]
  scorers.py       <- Built-in scorers: exact_match, contains, llm_judge         [planned M3]
  db.py            <- SQLite persistence via aiosqlite                           [planned M4]
  models.py        <- Pydantic data models                                       [planned M4]
  server.py        <- FastAPI dashboard                                          [planned M6]

tests/
  test_package.py  <- Smoke tests: version string, CLI help                      [exists]

eval.db            <- SQLite database (auto-created on first run)                [planned M4]
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

## CLI Usage (planned — M5)

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
python -m eval compare --run-ids 1,2
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
python -m eval --help   # prints CLI group — sub-commands land in M5

# Run the test suite
pytest
```

Once M3–M5 are complete, the full eval workflow will be:

```bash
# Set API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Run your first eval  (planned)
python -m eval run \
  --dataset datasets/qa_sample.jsonl \
  --prompt prompts/qa.j2 \
  --model gpt-4o-mini \
  --scorer exact_match

# Inspect results  (planned)
python -m eval show --run-id 1

# Launch web dashboard  (planned)
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
| M2 | Dataset loader + Jinja2 prompt renderer | ⏳ planned |
| M3 | Model adapters (OpenAI + Anthropic), async runner | ⏳ planned |
| M4 | SQLite persistence, Pydantic models | ⏳ planned |
| M5 | Rich CLI (`run`, `show`, `compare`) | ⏳ planned |
| M6 | FastAPI dashboard + README demo GIF | ⏳ planned |

---

## License

[MIT](LICENSE) — Copyright 2024 Ritik
