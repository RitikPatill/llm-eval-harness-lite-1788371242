from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable

from openai import AsyncOpenAI


def exact_match(output: str, expected: str) -> float:
    """1.0 if output.strip() == expected.strip() (case-insensitive), else 0.0."""
    return 1.0 if output.strip().lower() == expected.strip().lower() else 0.0


def contains(output: str, expected: str) -> float:
    """1.0 if expected.strip().lower() in output.strip().lower(), else 0.0."""
    return 1.0 if expected.strip().lower() in output.strip().lower() else 0.0


async def llm_judge(output: str, expected: str) -> float:
    """Calls gpt-4o-mini with a rating prompt, returns float 0.0–1.0.

    Falls back to 0.0 on parse error.
    """
    client = AsyncOpenAI()
    prompt = (
        "Rate how well this answer matches the expected. "
        "Answer with a float 0-1 only.\n"
        f"Expected: {expected}\n"
        f"Actual: {output}"
    )
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        text = response.choices[0].message.content.strip()
        return float(text)
    except (ValueError, AttributeError, IndexError):
        return 0.0


_BUILTINS: dict[str, Callable] = {
    "exact_match": exact_match,
    "contains": contains,
    "llm_judge": llm_judge,
}


def get_scorer(name: str) -> Callable:
    """Resolve scorer by name.

    Checks built-ins first, then auto-discovers .py files in scorers/ under cwd.
    Raises ValueError if not found.
    """
    if name in _BUILTINS:
        return _BUILTINS[name]

    plugin_path = Path.cwd() / "scorers" / f"{name}.py"
    if plugin_path.exists():
        spec = importlib.util.spec_from_file_location(name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, name):
            return getattr(module, name)
        raise ValueError(
            f"Plugin file {plugin_path} found but has no function named '{name}'"
        )

    raise ValueError(
        f"Scorer '{name}' not found. Built-ins: {list(_BUILTINS)}. "
        f"Or add scorers/{name}.py with a function named '{name}'."
    )
