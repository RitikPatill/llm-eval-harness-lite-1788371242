from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from eval.models import DatasetRow


def load_dataset(path: str | Path) -> list[DatasetRow]:
    """Read a .jsonl file and validate each line with DatasetRow.

    Raises ValueError with the offending line number on validation failure.
    """
    rows: list[DatasetRow] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                rows.append(DatasetRow.model_validate(raw))
            except (json.JSONDecodeError, ValidationError) as exc:
                raise ValueError(f"Invalid row at line {lineno}: {exc}") from exc
    return rows
