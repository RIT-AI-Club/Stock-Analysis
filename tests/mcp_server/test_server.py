from stock_analysis.mcp_server import create_server
from stock_analysis.reporting import ReportFormatter


class FakeLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    async def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        self.calls.append((prompt, system_prompt))
        return "formatted"


async def test_only_format_report_tool_is_registered() -> None:
    tools = await create_server(ReportFormatter(FakeLLM())).list_tools()
    assert [tool.name for tool in tools] == ["format_report"]


async def test_format_report_tool_delegates_to_formatter() -> None:
    llm = FakeLLM()
    server = create_server(ReportFormatter(llm))
    await server.call_tool("format_report", {"content": "raw", "title": "T"})
    prompt = llm.calls[0][0]
    assert "Title: T" in prompt
    assert "raw" in prompt
