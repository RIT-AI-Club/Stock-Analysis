# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- MCP server (`python -m stock_analysis.mcp_server`) with a `format_report` tool, backed by the
  OpenAI API behind a provider-agnostic `LLMClient` interface.
- `format_report` also renders the HTML to PDF (Playwright/Chromium) and saves both files to
  gitignored `output/html` and `output/pdf` (configurable with `HTML_OUTPUT_DIR`,
  `PDF_OUTPUT_DIR`).
- `format_report` has the model design each report as a complete HTML document with its own CSS
  (cover, numbered sections, KPI tiles, tables, figure blocks), guided by a detailed system prompt.
  The output is validated, and a warning is logged if the PDF has more pages than the report has
  page sections. It takes optional chart references, and the report gets one empty, identified
  slot per chart for another source to fill.
- Project scaffolding: tooling (uv, ruff, mypy, pytest, pre-commit), CI, contribution
  standards, and documentation structure.
