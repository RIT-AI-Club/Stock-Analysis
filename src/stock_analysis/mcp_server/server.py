"""MCP server definition. A thin wrapper: tools delegate to core modules."""

from mcp.server.mcpserver import MCPServer

from stock_analysis.reporting import ReportFormatter


def create_server(formatter: ReportFormatter) -> MCPServer:
    """Build the MCP server.

    Args:
        formatter: Report formatter used by the tool. Injected so tests can fake its LLM.

    Returns:
        A configured server; call ``run()`` to serve it.
    """
    server = MCPServer("stock-analysis")

    @server.tool()
    async def format_report(
        content: str,
        title: str | None = None,
        instructions: str | None = None,
    ) -> str:
        """Format raw report content into a structured, readable HTML report.

        Only presentation changes; facts and figures are preserved.

        Args:
            content: The raw report content to format.
            title: Optional title to place at the top of the report.
            instructions: Optional extra formatting instructions (e.g. section order).
        """
        return await formatter.format_report(content, title=title, instructions=instructions)

    return server
