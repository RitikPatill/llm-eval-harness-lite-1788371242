from __future__ import annotations

from pathlib import Path

import jinja2

from eval.models import DatasetRow


def load_template(path: str | Path) -> jinja2.Template:
    """Load a Jinja2 template from a file path with strict undefined variables."""
    path = Path(path)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(path.parent)),
        undefined=jinja2.StrictUndefined,
    )
    return env.get_template(path.name)


def render(template: jinja2.Template, row: DatasetRow) -> str:
    """Render the template with dataset row fields as flat context variables."""
    return template.render(
        input=row.input,
        expected_output=row.expected_output,
    )
