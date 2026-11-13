from pathlib import Path

import pytest

from stock_analysis.reporting import PlaywrightPdfConverter
from stock_analysis.reporting.document import count_page_sections
from stock_analysis.reporting.pdf import pdf_page_count

SAMPLE = Path(__file__).parent / "sample_report.html"


@pytest.mark.integration
async def test_playwright_converter_renders_a_pdf() -> None:
    html = "<html><body><h1>Q3 Review</h1><p>Revenue $94B</p></body></html>"
    pdf = await PlaywrightPdfConverter().html_to_pdf(html)
    assert pdf.startswith(b"%PDF")


@pytest.mark.integration
async def test_playwright_converter_does_not_hit_the_network() -> None:
    # The blocked image must not break rendering or hang waiting on the request.
    html = '<html><body><img src="http://127.0.0.1:9/x.png"><p>text</p></body></html>'
    pdf = await PlaywrightPdfConverter().html_to_pdf(html)
    assert pdf.startswith(b"%PDF")


@pytest.mark.integration
async def test_sample_report_renders_one_pdf_page_per_section() -> None:
    # Guards the print baseline: no overflow onto extra pages and no stray blank page.
    document = SAMPLE.read_text(encoding="utf-8")
    pdf = await PlaywrightPdfConverter().html_to_pdf(document)
    assert pdf_page_count(pdf) == count_page_sections(document)


def test_pdf_page_count_ignores_the_pages_tree_object() -> None:
    assert pdf_page_count(b"/Type /Pages\n/Type /Page\n/Type /Page\n") == 2
    assert pdf_page_count(b"not a pdf") is None
