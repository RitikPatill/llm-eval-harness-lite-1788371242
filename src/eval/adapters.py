from __future__ import annotations

import time
from typing import Protocol

import anthropic
import openai


class ModelAdapter(Protocol):
    async def complete(self, prompt: str) -> tuple[str, float]:
        """Return (output_text, latency_ms)."""
        ...


class OpenAIAdapter:
    def __init__(self, model: str) -> None:
        self.model = model
        self._client = openai.AsyncOpenAI()

    async def complete(self, prompt: str) -> tuple[str, float]:
        t0 = time.perf_counter()
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        text = response.choices[0].message.content or ""
        return text, latency_ms


class AnthropicAdapter:
    def __init__(self, model: str) -> None:
        self.model = model
        self._client = anthropic.AsyncAnthropic()

    async def complete(self, prompt: str) -> tuple[str, float]:
        t0 = time.perf_counter()
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        text = response.content[0].text
        return text, latency_ms


def get_adapter(model: str) -> ModelAdapter:
    """Route by prefix: 'claude-*' -> Anthropic, else -> OpenAI."""
    if model.startswith("claude-"):
        return AnthropicAdapter(model)
    return OpenAIAdapter(model)
