from __future__ import annotations

from pydantic import BaseModel


class DatasetRow(BaseModel):
    input: str
    expected_output: str


class RunRecord(BaseModel):
    id: int
    created_at: str
    model: str
    dataset: str
    prompt_template: str
    scorer: str


class ScoreRecord(BaseModel):
    response_id: int
    scorer: str
    score: float
    metadata: dict = {}
