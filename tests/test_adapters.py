from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from eval.adapters import AnthropicAdapter, OpenAIAdapter, get_adapter


async def test_openai_adapter_returns_text_and_latency():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Paris"

    with patch("eval.adapters.openai.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        adapter = OpenAIAdapter("gpt-4o-mini")
        adapter._client = mock_client
        text, latency = await adapter.complete("What is the capital of France?")

    assert text == "Paris"
    assert latency >= 0


async def test_anthropic_adapter_returns_text_and_latency():
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Berlin"

    with patch("eval.adapters.anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        adapter = AnthropicAdapter("claude-haiku-4-5")
        adapter._client = mock_client
        text, latency = await adapter.complete("What is the capital of Germany?")

    assert text == "Berlin"
    assert latency >= 0


async def test_get_adapter_routes_claude_to_anthropic():
    adapter = get_adapter("claude-haiku-4-5")
    assert isinstance(adapter, AnthropicAdapter)


async def test_get_adapter_routes_gpt_to_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    adapter = get_adapter("gpt-4o-mini")
    assert isinstance(adapter, OpenAIAdapter)
