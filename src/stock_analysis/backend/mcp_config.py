"""Configuration for the MCP servers the client connects to.

Servers are declared in a YAML file (see ``config/mcp_servers.yaml``). String values may
reference environment variables as ``${VAR}``, which keeps API keys out of the file::

    timeout_seconds: 120

    servers:
      research:
        transport: stdio
        command: uv
        args: [run, python, -m, stock_analysis.servers.research]
        env:
          PERPLEXITY_API_KEY: ${PERPLEXITY_API_KEY}

      remote:
        transport: http
        url: https://example.com/mcp
"""

import os
import re
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, ValidationError

DEFAULT_TIMEOUT_SECONDS = 120.0

_ENV_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

type _ConfigValue = str | int | float | bool | list[_ConfigValue] | dict[str, _ConfigValue] | None


class MCPConfigError(Exception):
    """Raised when the MCP server configuration is missing, malformed, or incomplete."""


class StdioServerConfig(BaseModel):
    """A server launched as a subprocess that speaks MCP over stdin/stdout.

    Attributes:
        command: Executable to launch, e.g. ``"uv"`` or ``"python"``.
        args: Command-line arguments passed to ``command``.
        env: Extra environment variables for the subprocess. Only a minimal safe set is
            inherited from the parent process, so API keys must be listed here explicitly.
        cwd: Working directory for the subprocess. Defaults to the current directory.
    """

    # YAML reads unquoted `PORT: 8080` as a number; treat it as the string the user meant.
    model_config = ConfigDict(extra="forbid", frozen=True, coerce_numbers_to_str=True)

    transport: Literal["stdio"]
    command: str = Field(min_length=1)
    args: list[str] = []
    env: dict[str, str] = {}
    cwd: Path | None = None


class HttpServerConfig(BaseModel):
    """A remote server reached over Streamable HTTP.

    Attributes:
        url: The server's MCP endpoint, e.g. ``"https://example.com/mcp"``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    transport: Literal["http"]
    url: str = Field(pattern=r"^https?://")


type ServerConfig = Annotated[
    StdioServerConfig | HttpServerConfig, Field(discriminator="transport")
]


class MCPConfig(BaseModel):
    """The full set of MCP servers to connect to.

    Attributes:
        servers: Server configurations keyed by a short name used in logs and errors.
        timeout_seconds: How long to wait for any single server response.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    servers: dict[str, ServerConfig] = {}
    timeout_seconds: PositiveFloat = DEFAULT_TIMEOUT_SECONDS


def load_mcp_config(path: Path) -> MCPConfig:
    """Load and validate an MCP server configuration file.

    ``${VAR}`` references in string values are replaced with the matching environment
    variable.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        The validated configuration.

    Raises:
        MCPConfigError: If the file is missing, is not valid YAML, fails validation, or
            references an environment variable that is not set.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MCPConfigError(f"MCP config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise MCPConfigError(f"Invalid YAML in {path}: {exc}") from exc

    # An empty file means "no servers"; anything else must be a mapping at the top level.
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise MCPConfigError(f"Invalid MCP config in {path}: top level must be a mapping.")

    expanded = _expand_env(raw)
    try:
        return MCPConfig.model_validate(expanded)
    except ValidationError as exc:
        raise MCPConfigError(f"Invalid MCP config in {path}:\n{exc}") from exc


def _expand_env(value: _ConfigValue) -> _ConfigValue:
    """Recursively replace ``${VAR}`` references in every string within ``value``."""
    match value:
        case str():
            return _ENV_REFERENCE.sub(_lookup_env, value)
        case list():
            return [_expand_env(item) for item in value]
        case dict():
            return {key: _expand_env(item) for key, item in value.items()}
        case _:
            return value


def _lookup_env(match: re.Match[str]) -> str:
    name = match.group(1)
    try:
        return os.environ[name]
    except KeyError:
        raise MCPConfigError(
            f"MCP config references ${{{name}}}, but the environment variable {name} is not "
            "set. Add it to your .env file (see .env.example)."
        ) from None
