import logging
from pathlib import Path

import pytest

from stock_analysis.llm import LLMError
from stock_analysis.reporting import (
    ChartReference,
    PdfConversionError,
    ReportFormatter,
    ReportStore,
)
from tests.fakes import DOC, FakeLLM, FakePdfConverter, make_document

CHART = ChartReference("price_history", "Price history", "Month-end close, USD, 2023-2026")
SLOT = '<div class="chart-slot" data-chart-id="price_history"></div>'


def make_formatter(
    tmp_path: Path, llm: FakeLLM, pdf: FakePdfConverter | None = None
) -> ReportFormatter:
    store = ReportStore(tmp_path / "html", tmp_path / "pdf")
    return ReportFormatter(llm, pdf or FakePdfConverter(), store)


async def test_format_report_builds_prompt_from_parameters(tmp_path: Path) -> None:
    llm = FakeLLM(make_document(SLOT))
    await make_formatter(tmp_path, llm).format_report(
        "AAPL revenue $94B", title="Q3 Review", instructions="Put risks first", charts=[CHART]
    )
    prompt, system_prompt = llm.calls[0]
    assert "Title: Q3 Review" in prompt
    assert "Additional instructions: Put risks first" in prompt
    assert "AAPL revenue $94B" in prompt
    assert "- id: price_history\n  title: Price history\n  description: Month-end" in prompt
    assert system_prompt is not None
    assert "Never invent" in system_prompt
    assert "data-chart-id" in system_prompt


async def test_format_report_omits_unset_optional_parameters(tmp_path: Path) -> None:
    llm = FakeLLM()
    await make_formatter(tmp_path, llm).format_report("some content")
    prompt = llm.calls[0][0]
    assert "Title:" not in prompt
    assert "Additional instructions:" not in prompt
    assert "Charts: none. Do not create any chart slots." in prompt


async def test_format_report_returns_the_models_document_unchanged(tmp_path: Path) -> None:
    result = await make_formatter(tmp_path, FakeLLM(f"\n{DOC}\n")).format_report("content")
    assert result == DOC


async def test_format_report_converts_html_and_saves_both_files(tmp_path: Path) -> None:
    pdf = FakePdfConverter()
    result = await make_formatter(tmp_path, FakeLLM(), pdf).format_report(
        "content", title="Q3 Review"
    )
    assert pdf.inputs == [result]
    (html_file,) = (tmp_path / "html").glob("*.html")
    (pdf_file,) = (tmp_path / "pdf").glob("*.pdf")
    assert html_file.read_text(encoding="utf-8") == result
    assert pdf_file.read_bytes() == b"%PDF-fake"
    assert html_file.stem == pdf_file.stem
    assert html_file.stem.endswith("-q3-review")


async def test_format_report_saves_nothing_when_pdf_conversion_fails(tmp_path: Path) -> None:
    formatter = make_formatter(tmp_path, FakeLLM(), FakePdfConverter(fail=True))
    with pytest.raises(PdfConversionError):
        await formatter.format_report("content")
    assert not (tmp_path / "html").exists()
    assert not (tmp_path / "pdf").exists()


async def test_format_report_rejects_output_that_breaks_the_contract(tmp_path: Path) -> None:
    pdf = FakePdfConverter()
    formatter = make_formatter(tmp_path, FakeLLM(f"```html\n{DOC}\n```"), pdf)
    with pytest.raises(LLMError, match="must be one HTML document"):
        await formatter.format_report("content")
    assert pdf.inputs == []
    assert not (tmp_path / "html").exists()


async def test_format_report_rejects_output_missing_a_chart_slot(tmp_path: Path) -> None:
    formatter = make_formatter(tmp_path, FakeLLM())
    with pytest.raises(LLMError, match="missing slot for chart 'price_history'"):
        await formatter.format_report("content", charts=[CHART])


async def test_format_report_rejects_duplicate_chart_ids(tmp_path: Path) -> None:
    llm = FakeLLM()
    with pytest.raises(ValueError, match="unique"):
        await make_formatter(tmp_path, llm).format_report("content", charts=[CHART, CHART])
    assert llm.calls == []


async def test_format_report_warns_when_pdf_has_more_pages_than_sections(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    two_pages = b"%PDF /Type /Page\n/Type /Page\n"
    formatter = make_formatter(tmp_path, FakeLLM(), FakePdfConverter(pdf=two_pages))
    with caplog.at_level(logging.WARNING):
        await formatter.format_report("content")
    assert "2 pages but the report defines 1" in caplog.text


async def test_format_report_does_not_warn_when_page_counts_match(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    one_page = b"%PDF /Type /Page\n"
    formatter = make_formatter(tmp_path, FakeLLM(), FakePdfConverter(pdf=one_page))
    with caplog.at_level(logging.WARNING):
        await formatter.format_report("content")
    assert caplog.text == ""


@pytest.mark.parametrize("content", ["", "   \n"])
async def test_format_report_rejects_empty_content(tmp_path: Path, content: str) -> None:
    llm = FakeLLM()
    with pytest.raises(ValueError, match="content"):
        await make_formatter(tmp_path, llm).format_report(content)
    assert llm.calls == []
