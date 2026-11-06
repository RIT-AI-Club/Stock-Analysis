"""Entry point: ``uv run python -m stock_analysis.mcp_server`` (stdio transport)."""

import logging

from stock_analysis.config import Settings
from stock_analysis.llm import OpenAIClient
from stock_analysis.mcp_server.server import create_server
from stock_analysis.reporting import ReportFormatter


def main() -> None:
    """Load settings, build the server, and serve over stdio."""
    # The stdio transport owns stdout, so logs go to stderr (the logging default).
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    llm = OpenAIClient.from_settings(Settings.from_env())
    server = create_server(ReportFormatter(llm))
    server.run()


if __name__ == "__main__":
    main()
