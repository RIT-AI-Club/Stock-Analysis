"""OpenAI implementation of :class:`~stock_analysis.llm.base.LLMClient`."""

import logging

import openai
from openai import AsyncOpenAI

from stock_analysis.config import Settings
from stock_analysis.llm.base import LLMError

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Calls the OpenAI Responses API.

    Args:
        api_key: OpenAI API key.
        model: Model name to use for completions.
        client: Optional preconfigured SDK client (used to inject fakes in tests).
    """

    def __init__(self, api_key: str, model: str, *, client: AsyncOpenAI | None = None) -> None:
        self._model = model
        self._client = client or AsyncOpenAI(api_key=api_key)

    @classmethod
    def from_settings(cls, settings: Settings) -> "OpenAIClient":
        """Create a client from application settings."""
        return cls(settings.openai_api_key, settings.openai_model)

    async def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        """Generate a completion. See :meth:`LLMClient.complete`."""
        logger.info("Calling OpenAI model=%s", self._model)
        try:
            response = await self._client.responses.create(
                model=self._model,
                input=prompt,
                instructions=system_prompt,
            )
        except openai.OpenAIError as exc:
            raise LLMError(f"OpenAI request failed: {exc}") from exc
        text = response.output_text
        if not text:
            raise LLMError("OpenAI returned an empty response.")
        return text
