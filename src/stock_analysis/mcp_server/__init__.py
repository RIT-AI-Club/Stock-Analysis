"""MCP server exposing stock-analysis tools."""

from stock_analysis.mcp_server.server import create_server

__all__ = ["create_server"]
