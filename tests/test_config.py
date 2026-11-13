from pathlib import Path

import pytest

from stock_analysis.config import DEFAULT_OPENAI_MODEL, ConfigError, Settings


def test_from_env_reads_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "custom-model")
    assert Settings.from_env() == Settings("sk-test", "custom-model")


def test_from_env_defaults_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert Settings.from_env().openai_model == DEFAULT_OPENAI_MODEL


def test_from_env_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        Settings.from_env()


def test_from_env_output_dirs_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("HTML_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("PDF_OUTPUT_DIR", raising=False)
    settings = Settings.from_env()
    assert settings.html_output_dir == Path("output/html")
    assert settings.pdf_output_dir == Path("output/pdf")


def test_from_env_output_dirs_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("HTML_OUTPUT_DIR", "out/h")
    monkeypatch.setenv("PDF_OUTPUT_DIR", "out/p")
    settings = Settings.from_env()
    assert settings.html_output_dir == Path("out/h")
    assert settings.pdf_output_dir == Path("out/p")
