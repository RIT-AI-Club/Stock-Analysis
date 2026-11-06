import pytest

from stock_analysis.reporting import ReportFormatter


class FakeLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    async def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        self.calls.append((prompt, system_prompt))
        return "<html></html>"


async def test_format_report_builds_prompt_from_parameters() -> None:
    llm = FakeLLM()
    result = await ReportFormatter(llm).format_report(
        "AAPL revenue $94B", title="Q3 Review", instructions="Put risks first"
    )
    assert result == "<html></html>"
    prompt, system_prompt = llm.calls[0]
    assert "Title: Q3 Review" in prompt
    assert "Additional instructions: Put risks first" in prompt
    assert "AAPL revenue $94B" in prompt
    assert system_prompt is not None
    assert "HTML" in system_prompt
    assert "Never add, remove, or change facts" in system_prompt


async def test_format_report_omits_unset_optional_parameters() -> None:
    llm = FakeLLM()
    await ReportFormatter(llm).format_report("some content")
    prompt = llm.calls[0][0]
    assert "Title:" not in prompt
    assert "Additional instructions:" not in prompt


@pytest.mark.parametrize("content", ["", "   \n"])
async def test_format_report_rejects_empty_content(content: str) -> None:
    llm = FakeLLM()
    with pytest.raises(ValueError, match="content"):
        await ReportFormatter(llm).format_report(content)
    assert llm.calls == []
