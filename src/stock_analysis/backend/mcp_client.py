"""Client that connects to several MCP servers and exposes their tools as one set.

This module only speaks MCP: it connects to servers, discovers their tools, and routes tool
calls to the right server. It knows nothing about LLMs. An orchestrator (the agent loop)
uses it to give a model access to the tools.

Example:
    ```python
    config = load_mcp_config(Path("config/mcp_servers.yaml"))
    async with MCPClient.from_config(config) as client:
        for tool in client.tools:
            logger.info("%s: %s", tool.name, tool.description)
        result = await client.call_tool("research_stock", {"ticker": "AAPL"})
    ```
"""

import logging
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Final, Self

from mcp import Client, MCPError, StdioServerParameters
from mcp import types as mcp_types
from mcp.server.mcpserver import MCPServer
from mcp.types import ContentBlock, TextContent

from stock_analysis.backend.mcp_config import (
    DEFAULT_TIMEOUT_SECONDS,
    HttpServerConfig,
    MCPConfig,
    ServerConfig,
    StdioServerConfig,
)

logger = logging.getLogger(__name__)

# Guards against a server whose pagination never terminates.
_MAX_TOOL_PAGES: Final = 100

type ServerTarget = StdioServerParameters | str | MCPServer[Any]
"""Anything that can be connected to: stdio launch parameters, a Streamable HTTP URL, or an
in-process ``MCPServer`` (used in tests)."""


class MCPClientError(Exception):
    """Base class for errors raised by `MCPClient`."""


class MCPConnectionError(MCPClientError):
    """Raised when a server cannot be started, reached, or initialized."""


class ToolNotFoundError(MCPClientError):
    """Raised when calling a tool that no connected server provides."""


class ToolCallError(MCPClientError):
    """Raised when a tool call fails at the protocol level (timeout, invalid request, crash).

    A tool that runs but reports a failure does not raise this. It returns a `ToolResult`
    with ``is_error=True`` so the error message can be shown to the model.
    """


@dataclass(frozen=True, slots=True)
class Tool:
    """A tool offered by one of the connected servers.

    Attributes:
        name: The tool's name, unique across all connected servers.
        server: Name of the server that provides the tool.
        description: What the tool does, written for the model.
        input_schema: JSON Schema describing the tool's arguments.
    """

    name: str
    server: str
    description: str
    input_schema: dict[str, Any]  # Arbitrary JSON Schema.


@dataclass(frozen=True, slots=True)
class ToolResult:
    """The outcome of a tool call.

    Attributes:
        content: Content blocks returned by the tool (text, images, resources, ...).
        structured_content: Machine-readable output, if the tool defines an output schema.
        is_error: True if the tool ran but reported a failure.
    """

    content: list[ContentBlock]
    structured_content: dict[str, Any] | None
    is_error: bool

    @property
    def text(self) -> str:
        """All text content blocks joined by newlines. Non-text blocks are skipped."""
        return "\n".join(block.text for block in self.content if isinstance(block, TextContent))


class MCPClient:
    """Connects to multiple MCP servers and presents their tools as a single collection.

    Use as an async context manager. Entering connects to every server and discovers its
    tools; exiting shuts all connections down. If any server fails to connect, those
    already connected are closed and the error is raised.

    Tool names must be unique across servers. A duplicate is a configuration error and is
    rejected rather than silently shadowed.

    Args:
        servers: Servers to connect to, keyed by a short name used in logs and errors.
        timeout_seconds: How long to wait for any single server response.
    """

    def __init__(
        self,
        servers: Mapping[str, ServerTarget],
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._servers = dict(servers)
        self._timeout_seconds = timeout_seconds
        self._stack: AsyncExitStack | None = None
        self._sessions: dict[str, Client] = {}
        self._tools: dict[str, Tool] = {}

    @classmethod
    def from_config(cls, config: MCPConfig) -> Self:
        """Create a client for the servers declared in a configuration.

        Args:
            config: A validated configuration, usually from `load_mcp_config`.

        Returns:
            An unconnected client. Enter it with ``async with`` to connect.
        """
        targets = {name: _to_target(server) for name, server in config.servers.items()}
        return cls(targets, timeout_seconds=config.timeout_seconds)

    async def __aenter__(self) -> Self:
        if self._stack is not None:
            raise MCPClientError("MCPClient is already connected.")

        self._stack = stack = AsyncExitStack()
        try:
            for name, target in self._servers.items():
                await self._connect(stack, name, target)
        except BaseException:
            await self.__aexit__(None, None, None)
            raise

        logger.info(
            "Connected to %d MCP server(s) providing %d tool(s).",
            len(self._sessions),
            len(self._tools),
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        stack, self._stack = self._stack, None
        self._sessions.clear()
        self._tools.clear()
        if stack is not None:
            await stack.aclose()

    @property
    def tools(self) -> list[Tool]:
        """Every tool offered by the connected servers, in discovery order."""
        self._require_connected()
        return list(self._tools.values())

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        """Call a tool on whichever server provides it.

        Args:
            name: The tool's name, as listed in `tools`.
            arguments: Arguments matching the tool's input schema.

        Returns:
            The tool's result. Check ``is_error``: a tool that reports a failure returns
            normally so the error can be passed back to the model.

        Raises:
            MCPClientError: If the client is not connected.
            ToolNotFoundError: If no connected server provides ``name``.
            ToolCallError: If the call fails at the protocol level, e.g. a timeout.
        """
        self._require_connected()
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(
                f"No connected MCP server provides a tool named {name!r}. "
                f"Available: {sorted(self._tools)}"
            )

        logger.debug("Calling tool %s on server %s.", name, tool.server)
        try:
            result = await self._sessions[tool.server].call_tool(name, arguments)
        except (MCPError, TimeoutError) as exc:
            raise ToolCallError(f"Tool {name!r} on server {tool.server!r} failed: {exc}") from exc

        if result.is_error:
            logger.warning("Tool %s on server %s reported an error.", name, tool.server)
        return ToolResult(
            content=list(result.content),
            structured_content=result.structured_content,
            is_error=bool(result.is_error),
        )

    async def _connect(self, stack: AsyncExitStack, name: str, target: ServerTarget) -> None:
        session = Client(target, read_timeout_seconds=self._timeout_seconds)
        try:
            await stack.enter_async_context(session)
            tools = await self._list_tools(session)
        # Transport and handshake failures surface as many exception types (OS errors from
        # subprocess launch, HTTP errors, task-group ExceptionGroups). Wrap them all with the
        # server name so the failing server is obvious.
        except Exception as exc:
            raise MCPConnectionError(f"Could not connect to MCP server {name!r}: {exc}") from exc

        self._sessions[name] = session
        for tool in tools:
            existing = self._tools.get(tool.name)
            if existing is not None:
                raise MCPClientError(
                    f"Tool {tool.name!r} is provided by both {existing.server!r} and {name!r}. "
                    "Tool names must be unique across servers."
                )
            self._tools[tool.name] = Tool(
                name=tool.name,
                server=name,
                description=tool.description or "",
                input_schema=tool.input_schema,
            )
        logger.info("Connected to MCP server %s (%d tools).", name, len(tools))

    @staticmethod
    async def _list_tools(session: Client) -> list[mcp_types.Tool]:
        tools: list[mcp_types.Tool] = []
        cursor: str | None = None
        for _ in range(_MAX_TOOL_PAGES):
            page = await session.list_tools(cursor=cursor)
            tools.extend(page.tools)
            cursor = page.next_cursor
            if cursor is None:
                return tools
        raise MCPClientError(f"Tool listing did not finish within {_MAX_TOOL_PAGES} pages.")

    def _require_connected(self) -> None:
        if self._stack is None:
            raise MCPClientError("MCPClient is not connected. Use it with `async with`.")


def _to_target(server: ServerConfig) -> ServerTarget:
    """Translate a configured server into something `mcp.Client` can connect to."""
    match server:
        case StdioServerConfig():
            return StdioServerParameters(
                command=server.command,
                args=server.args,
                env=server.env or None,
                cwd=server.cwd,
            )
        case HttpServerConfig():
            return server.url
