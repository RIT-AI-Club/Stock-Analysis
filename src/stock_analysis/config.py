"""Application settings, loaded from environment variables (see ``.env.example``)."""

import os
from dataclasses import dataclass

DEFAULT_OPENAI_MODEL = "gpt-5-mini"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration.

    Attributes:
        openai_api_key: API key for OpenAI.
        openai_model: Model used for completions.
    """

    openai_api_key: str
    openai_model: str = DEFAULT_OPENAI_MODEL

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables.

        Raises:
            ConfigError: If ``OPENAI_API_KEY`` is unset or empty.
        """
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ConfigError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        model = os.environ.get("OPENAI_MODEL", "").strip() or DEFAULT_OPENAI_MODEL
        return cls(openai_api_key=api_key, openai_model=model)
