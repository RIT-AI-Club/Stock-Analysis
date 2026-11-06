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
