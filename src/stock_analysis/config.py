"""Application settings, loaded from environment variables (see ``.env.example``)."""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_OPENAI_MODEL = "gpt-5-mini"
DEFAULT_HTML_OUTPUT_DIR = Path("output/html")
DEFAULT_PDF_OUTPUT_DIR = Path("output/pdf")


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime configuration.

    Attributes:
        openai_api_key: API key for OpenAI.
        openai_model: Model used for completions.
        html_output_dir: Where generated HTML reports are saved (relative to the working dir).
        pdf_output_dir: Where generated PDF reports are saved (relative to the working dir).
    """

    openai_api_key: str
    openai_model: str = DEFAULT_OPENAI_MODEL
    html_output_dir: Path = DEFAULT_HTML_OUTPUT_DIR
    pdf_output_dir: Path = DEFAULT_PDF_OUTPUT_DIR

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables.

        Raises:
            ConfigError: If ``OPENAI_API_KEY`` is unset or empty.
        """
        api_key = _env("OPENAI_API_KEY")
        if not api_key:
            raise ConfigError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        return cls(
            openai_api_key=api_key,
            openai_model=_env("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL,
            html_output_dir=Path(_env("HTML_OUTPUT_DIR") or DEFAULT_HTML_OUTPUT_DIR),
            pdf_output_dir=Path(_env("PDF_OUTPUT_DIR") or DEFAULT_PDF_OUTPUT_DIR),
        )


def _env(name: str) -> str:
    """Read an environment variable; unset and blank both come back as an empty string."""
    return os.environ.get(name, "").strip()
