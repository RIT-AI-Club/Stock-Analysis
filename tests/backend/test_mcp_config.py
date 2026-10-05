from pathlib import Path

import pytest

from stock_analysis.backend.mcp_config import (
    DEFAULT_TIMEOUT_SECONDS,
    HttpServerConfig,
    MCPConfigError,
    StdioServerConfig,
    load_mcp_config,
)

REPO_CONFIG = Path(__file__).parents[2] / "config" / "mcp_servers.yaml"


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "mcp_servers.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_stdio_and_http_servers(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
timeout_seconds: 30
servers:
  local:
    transport: stdio
    command: uv
    args: [run, server.py]
  remote:
    transport: http
    url: https://example.com/mcp
""",
    )

    config = load_mcp_config(path)

    assert config.timeout_seconds == 30
    assert config.servers["local"] == StdioServerConfig(
        transport="stdio", command="uv", args=["run", "server.py"]
    )
    assert config.servers["remote"] == HttpServerConfig(
        transport="http", url="https://example.com/mcp"
    )


def test_repo_config_file_is_valid() -> None:
    load_mcp_config(REPO_CONFIG)


@pytest.mark.parametrize("text", ["", "# only comments\n"], ids=["empty", "comments-only"])
def test_empty_file_means_no_servers_and_default_timeout(tmp_path: Path, text: str) -> None:
    config = load_mcp_config(write_config(tmp_path, text))

    assert config.servers == {}
    assert config.timeout_seconds == DEFAULT_TIMEOUT_SECONDS


def test_expands_environment_variables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret-123")
    path = write_config(
        tmp_path,
        """
servers:
  research:
    transport: stdio
    command: python
    env:
      API_KEY: ${TEST_API_KEY}
      LABEL: key=${TEST_API_KEY}
""",
    )

    server = load_mcp_config(path).servers["research"]

    assert isinstance(server, StdioServerConfig)
    assert server.env == {"API_KEY": "secret-123", "LABEL": "key=secret-123"}


def test_unquoted_numbers_in_env_become_strings(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
servers:
  local:
    transport: stdio
    command: python
    env:
      PORT: 8080
""",
    )

    server = load_mcp_config(path).servers["local"]

    assert isinstance(server, StdioServerConfig)
    assert server.env == {"PORT": "8080"}


def test_missing_environment_variable_fails_loudly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("TEST_MISSING_KEY", raising=False)
    path = write_config(
        tmp_path,
        """
servers:
  research:
    transport: stdio
    command: python
    env:
      API_KEY: ${TEST_MISSING_KEY}
""",
    )

    with pytest.raises(MCPConfigError, match="TEST_MISSING_KEY"):
        load_mcp_config(path)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(MCPConfigError, match="not found"):
        load_mcp_config(tmp_path / "nope.yaml")


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    with pytest.raises(MCPConfigError, match="Invalid YAML"):
        load_mcp_config(write_config(tmp_path, "servers: [unclosed"))


def test_non_mapping_top_level_raises(tmp_path: Path) -> None:
    with pytest.raises(MCPConfigError, match="top level must be a mapping"):
        load_mcp_config(write_config(tmp_path, "- just\n- a list\n"))


@pytest.mark.parametrize(
    "server_yaml",
    [
        pytest.param("transport: carrier-pigeon\ncommand: x", id="unknown-transport"),
        pytest.param("transport: stdio", id="stdio-without-command"),
        pytest.param("transport: http\nurl: ftp://example.com", id="non-http-url"),
        pytest.param("transport: stdio\ncommand: x\ncomand: typo", id="unknown-key"),
        pytest.param("transport: stdio\ncommand: x\nenv:\n  DEBUG: yes", id="bool-env-value"),
    ],
)
def test_invalid_server_definitions_raise(tmp_path: Path, server_yaml: str) -> None:
    indented = "\n".join(f"    {line}" for line in server_yaml.splitlines())
    path = write_config(tmp_path, f"servers:\n  bad:\n{indented}\n")

    with pytest.raises(MCPConfigError, match="Invalid MCP config"):
        load_mcp_config(path)
