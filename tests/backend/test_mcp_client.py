import sys
from pathlib import Path
from typing import Any

import pytest
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from stock_analysis.backend.mcp_client import (
    MCPClient,
    MCPClientError,
    MCPConnectionError,
    ToolNotFoundError,
)
from stock_analysis.backend.mcp_config import MCPConfig, StdioServerConfig

STDIO_SERVER = Path(__file__).with_name("stdio_server.py")


def make_math_server() -> MCPServer[Any]:
    server: MCPServer[Any] = MCPServer("math")

    @server.tool()
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b

    @server.tool()
    def divide(a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ToolError("cannot divide by zero")
        return a / b

    return server


def make_text_server() -> MCPServer[Any]:
    server: MCPServer[Any] = MCPServer("text")

    @server.tool()
    def shout(text: str) -> str:
        """Upper-case the text."""
        return text.upper()

    return server


async def test_discovers_tools_from_every_server() -> None:
    servers = {"math": make_math_server(), "text": make_text_server()}

    async with MCPClient(servers) as client:
        tools = {tool.name: tool for tool in client.tools}

    assert set(tools) == {"add", "divide", "shout"}
    assert tools["add"].server == "math"
    assert tools["shout"].server == "text"
    assert tools["add"].description == "Add two integers."
    assert set(tools["add"].input_schema["properties"]) == {"a", "b"}


async def test_routes_call_to_the_owning_server() -> None:
    servers = {"math": make_math_server(), "text": make_text_server()}

    async with MCPClient(servers) as client:
        total = await client.call_tool("add", {"a": 2, "b": 3})
        loud = await client.call_tool("shout", {"text": "buy"})

    assert not total.is_error
    assert total.text == "5"
    assert total.structured_content == {"result": 5}
    assert loud.text == "BUY"


async def test_tool_failure_is_returned_not_raised() -> None:
    async with MCPClient({"math": make_math_server()}) as client:
        result = await client.call_tool("divide", {"a": 1, "b": 0})

    assert result.is_error
    assert "cannot divide by zero" in result.text


async def test_unknown_tool_raises() -> None:
    async with MCPClient({"math": make_math_server()}) as client:
        with pytest.raises(ToolNotFoundError, match="nope"):
            await client.call_tool("nope")


async def test_duplicate_tool_names_across_servers_are_rejected() -> None:
    servers = {"first": make_math_server(), "second": make_math_server()}

    with pytest.raises(MCPClientError, match="provided by both 'first' and 'second'"):
        async with MCPClient(servers):
            pass


async def test_using_client_before_connecting_raises() -> None:
    client = MCPClient({"math": make_math_server()})

    with pytest.raises(MCPClientError, match="not connected"):
        _ = client.tools
    with pytest.raises(MCPClientError, match="not connected"):
        await client.call_tool("add", {"a": 1, "b": 2})


async def test_client_is_unusable_after_exit() -> None:
    client = MCPClient({"math": make_math_server()})
    async with client:
        pass

    with pytest.raises(MCPClientError, match="not connected"):
        _ = client.tools


async def test_connects_to_stdio_server_from_config() -> None:
    config = MCPConfig(
        servers={
            "stdio": StdioServerConfig(
                transport="stdio",
                command=sys.executable,
                args=[str(STDIO_SERVER)],
                env={"STOCK_ANALYSIS_TEST_VAR": "passed-through"},
            )
        },
        timeout_seconds=30,
    )

    async with MCPClient.from_config(config) as client:
        result = await client.call_tool("read_env", {"name": "STOCK_ANALYSIS_TEST_VAR"})

    assert result.text == "passed-through"


async def test_failed_server_names_itself_and_closes_the_others() -> None:
    config = MCPConfig(
        servers={
            "good": StdioServerConfig(
                transport="stdio", command=sys.executable, args=[str(STDIO_SERVER)]
            ),
            "broken": StdioServerConfig(
                transport="stdio", command="definitely-not-a-real-command-xyz"
            ),
        },
        timeout_seconds=30,
    )
    client = MCPClient.from_config(config)

    with pytest.raises(MCPConnectionError, match="'broken'"):
        async with client:
            pass

    with pytest.raises(MCPClientError, match="not connected"):
        _ = client.tools
