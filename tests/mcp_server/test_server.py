from pathlib import Path

from stock_analysis.mcp_server import create_server
from stock_analysis.reporting import ReportFormatter, ReportStore
from tests.fakes import FakeLLM, FakePdfConverter, make_document


async def test_only_format_report_tool_is_registered(tmp_path: Path) -> None:
    server = create_server(
        ReportFormatter(FakeLLM(), FakePdfConverter(), ReportStore(tmp_path, tmp_path))
    )
    tools = await server.list_tools()
    assert [tool.name for tool in tools] == ["format_report"]


async def test_format_report_tool_delegates_to_formatter(tmp_path: Path) -> None:
    llm = FakeLLM()
    store = ReportStore(tmp_path / "html", tmp_path / "pdf")
    server = create_server(ReportFormatter(llm, FakePdfConverter(), store))
    await server.call_tool("format_report", {"content": "raw", "title": "T"})
    prompt = llm.calls[0][0]
    assert "Title: T" in prompt
    assert "raw" in prompt
    assert len(list((tmp_path / "pdf").glob("*.pdf"))) == 1


async def test_format_report_tool_accepts_chart_references(tmp_path: Path) -> None:
    slot = '<div class="chart-slot" data-chart-id="price"></div>'
    llm = FakeLLM(make_document(slot))
    store = ReportStore(tmp_path / "html", tmp_path / "pdf")
    server = create_server(ReportFormatter(llm, FakePdfConverter(), store))
    await server.call_tool(
        "format_report",
        {
            "content": "raw",
            "charts": [{"id": "price", "title": "Price", "description": "Close, USD"}],
        },
    )
    assert "- id: price\n  title: Price\n  description: Close, USD" in llm.calls[0][0]
