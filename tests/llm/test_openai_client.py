from types import SimpleNamespace
from typing import Any, cast

import openai
import pytest
from openai import AsyncOpenAI

from stock_analysis.llm import LLMError, OpenAIClient


class FakeResponses:
    def __init__(self, output_text: str = "hello", error: Exception | None = None) -> None:
        self.output_text = output_text
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=self.output_text)


def make_client(responses: FakeResponses) -> OpenAIClient:
    sdk = cast(AsyncOpenAI, SimpleNamespace(responses=responses))
    return OpenAIClient("sk-test", "test-model", client=sdk)


async def test_complete_passes_prompt_and_returns_text() -> None:
    responses = FakeResponses("an answer")
    result = await make_client(responses).complete("question", system_prompt="be brief")
    assert result == "an answer"
    assert responses.calls == [
        {"model": "test-model", "input": "question", "instructions": "be brief"}
    ]


async def test_complete_wraps_sdk_errors() -> None:
    responses = FakeResponses(error=openai.OpenAIError("boom"))
    with pytest.raises(LLMError, match="OpenAI request failed"):
        await make_client(responses).complete("question")


async def test_complete_rejects_empty_output() -> None:
    with pytest.raises(LLMError, match="empty"):
        await make_client(FakeResponses("")).complete("question")
