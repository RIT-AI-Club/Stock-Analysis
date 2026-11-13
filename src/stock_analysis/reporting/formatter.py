"""Core report formatting logic. Independent of MCP; depends on interfaces, not services."""

import logging
from collections.abc import Sequence
from importlib import resources

from stock_analysis.llm import LLMClient
from stock_analysis.reporting.charts import ChartReference
from stock_analysis.reporting.document import count_page_sections, validate_document
from stock_analysis.reporting.output import ReportStore
from stock_analysis.reporting.pdf import PdfConverter, pdf_page_count

logger = logging.getLogger(__name__)


def _load_system_prompt() -> str:
    """Read the formatting system prompt packaged in ``reporting/prompts/``."""
    prompt = resources.files(__package__).joinpath("prompts/format_report.txt")
    return prompt.read_text(encoding="utf-8").strip()


class ReportFormatter:
    """Formats raw report content into a styled HTML report, with a saved PDF copy.

    The model designs the report: it returns a complete HTML document with its own CSS.

    Args:
        llm: LLM backend that writes the report document.
        pdf_converter: Renders the HTML report to PDF.
        store: Saves the HTML and PDF files to their output directories.
    """

    def __init__(self, llm: LLMClient, pdf_converter: PdfConverter, store: ReportStore) -> None:
        self._llm = llm
        self._pdf_converter = pdf_converter
        self._store = store
        self._system_prompt = _load_system_prompt()

    async def format_report(
        self,
        content: str,
        *,
        title: str | None = None,
        instructions: str | None = None,
        charts: Sequence[ChartReference] = (),
    ) -> str:
        """Format a report as HTML, convert it to PDF, and save both files.

        Args:
            content: The raw report content to format.
            title: Optional report title.
            instructions: Optional extra formatting instructions (e.g. section order).
            charts: Charts produced elsewhere. The model places one empty, identified slot for
                each; filling the slots is a later step.

        Returns:
            The report as the complete HTML document the model wrote.

        Raises:
            ValueError: If ``content`` is empty or chart ids are not unique.
            LLMError: If the LLM call fails or its output breaks the output contract.
            PdfConversionError: If the PDF cannot be rendered. Nothing is saved in that case.
        """
        _check_inputs(content, charts)

        prompt = _build_prompt(content, title, instructions, charts)
        reply = await self._llm.complete(prompt, system_prompt=self._system_prompt)
        html = reply.strip()
        validate_document(html, [chart.id for chart in charts])

        pdf = await self._pdf_converter.html_to_pdf(html)
        _warn_if_pages_overflowed(html, pdf)

        self._store.save(html, pdf, title=title)
        return html


def _check_inputs(content: str, charts: Sequence[ChartReference]) -> None:
    if not content.strip():
        raise ValueError("content must not be empty.")
    chart_ids = [chart.id for chart in charts]
    if len(set(chart_ids)) != len(chart_ids):
        raise ValueError("chart ids must be unique.")


def _build_prompt(
    content: str,
    title: str | None,
    instructions: str | None,
    charts: Sequence[ChartReference],
) -> str:
    """Assemble the user message: title, instructions, chart references, then the content."""
    sections: list[str] = []
    if title:
        sections.append(f"Title: {title}")
    if instructions:
        sections.append(f"Additional instructions: {instructions}")
    sections.append(_describe_charts(charts))
    sections.append(f"Report content:\n{content}")
    return "\n".join(sections)


def _describe_charts(charts: Sequence[ChartReference]) -> str:
    if not charts:
        return "Charts: none. Do not create any chart slots."
    header = "Charts (place each exactly once; slots only, never draw them):"
    entries = [
        f"- id: {chart.id}\n  title: {chart.title}\n  description: {chart.description}"
        for chart in charts
    ]
    return "\n".join([header, *entries])


def _warn_if_pages_overflowed(html: str, pdf: bytes) -> None:
    """Log a warning if the PDF has a different page count than the report has page sections.

    A mismatch means a page's content overflowed onto an extra printed page.
    """
    sections = count_page_sections(html)
    pages = pdf_page_count(pdf)
    if pages is not None and pages != sections:
        logger.warning(
            "Rendered PDF has %d pages but the report defines %d page sections; "
            "content probably overflowed a page.",
            pages,
            sections,
        )
