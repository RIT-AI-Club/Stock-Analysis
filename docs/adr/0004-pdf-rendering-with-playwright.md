# 0004. PDF rendering with Playwright

- **Status:** Accepted
- **Date:** 2026-11-05
- **Deciders:** @knicolosi313

## Context

`format_report` produces an HTML report. We also want a PDF copy, rendered to look like the HTML,
and both files saved to disk for testing.

## Decision

- HTML to PDF conversion is a separate helper behind a `PdfConverter` Protocol
  (`stock_analysis.reporting.pdf`). `PlaywrightPdfConverter` implements it with headless
  Chromium. Unit tests fake the converter; real rendering is covered by
  `@pytest.mark.integration` tests.
- `ReportFormatter.format_report` converts after the LLM returns and before it returns. If
  conversion fails it raises `PdfConversionError` and saves nothing.
- `ReportStore` writes `<html dir>/<name>.html` and `<pdf dir>/<name>.pdf` with a shared
  timestamped, slugified name. Directories come from `HTML_OUTPUT_DIR` / `PDF_OUTPUT_DIR`
  (defaults `output/html`, `output/pdf`) and are gitignored.
- The HTML is model-generated and untrusted, so Chromium renders it with JavaScript disabled
  and all network requests blocked.

## Alternatives considered

- **WeasyPrint:** pure Python, no browser, but weaker CSS support and needs native GTK libraries,
  which are painful on Windows.
- **Chromium print via another wrapper (e.g. pyppeteer):** less maintained than Playwright.

## Consequences

- Contributors must run `uv run playwright install chromium` once (about 150 MB).
- Each conversion launches a browser (about a second). Reuse one browser if this becomes slow.
- Remote images, fonts, and stylesheets in the report will not render. Inline CSS and `data:`
  URLs work.
- Output files are for testing. Storing reports for real use needs a different design.
