"""Minimal MCP server run as a subprocess by the stdio tests."""

import os

from mcp.server.mcpserver import MCPServer

server = MCPServer("stdio-test")


@server.tool()
def read_env(name: str) -> str:
    """Return an environment variable visible to this server process."""
    return os.environ.get(name, "<unset>")


if __name__ == "__main__":
    server.run("stdio")
