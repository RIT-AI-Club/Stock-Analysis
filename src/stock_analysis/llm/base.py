"""Provider-agnostic LLM interface. Unit tests fake this; they never hit the network."""

from typing import Protocol


class LLMError(RuntimeError):
    """Raised when an LLM call fails or returns unusable output."""


class LLMClient(Protocol):
    """Anything that can turn a prompt into a text completion."""

    async def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        """Generate a completion.

        Args:
            prompt: The user prompt.
            system_prompt: Optional instructions that frame the response.

        Returns:
            The model's text response.

        Raises:
            LLMError: If the provider call fails or the response is empty.
        """
        ...
