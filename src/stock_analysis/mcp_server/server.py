"""MCP server definition. A thin wrapper: tools delegate to core modules."""

from mcp.server.mcpserver import MCPServer

from stock_analysis.reporting import ChartReference, ReportFormatter


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
        charts: list[ChartReference] | None = None,
    ) -> str:
        """Format raw report content into a styled, print-ready HTML report (PDF saved too).

        Only presentation changes; facts and figures are preserved.

        Args:
            content: The raw report content to format.
            title: Optional report title.
            instructions: Optional extra formatting instructions (e.g. section order).
            charts: Charts produced elsewhere, given as references. The report gets one empty
                slot per chart (identified by the chart id) where the chart is later inserted.
        """
        return await formatter.format_report(
            content, title=title, instructions=instructions, charts=charts or ()
        )

    return server
