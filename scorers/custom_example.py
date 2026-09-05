"""Example custom scorer plugin.

Drop any .py file in scorers/ with a function matching the filename stem.
Usage: python -m eval run ... --scorer custom_example
"""


def custom_example(output: str, expected: str) -> float:
    """Score 1.0 if lengths are within 20% of each other, else 0.0."""
    if not expected:
        return 0.0
    ratio = len(output) / len(expected)
    return 1.0 if 0.8 <= ratio <= 1.2 else 0.0
