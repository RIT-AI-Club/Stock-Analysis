# 0005. The model designs the report; code enforces the contract

- **Status:** Accepted
- **Date:** 2026-11-05
- **Deciders:** @knicolosi313

## Context

Reports are rendered to A4 PDF and should look like a polished equity research note: cover,
numbered sections, KPI tiles, tables, and figure blocks. We want the look to be fully dynamic, so
the model can adapt the design to the company, the content and any branding in the request. Charts
come from another source, so the report needs reserved spots for them.

## Decision

- The model returns one complete HTML document with its own CSS. There is no shared stylesheet.
  The system prompt (`reporting/prompts/format_report.txt`) supplies a design brief, a required
  print baseline (A4 `@page`, `min-height` pages, no clipping), and the page-budget rules.
- Charts are passed as references (`ChartReference`: id, title, description). The model places one
  empty `<div class="chart-slot" data-chart-id="...">` per chart with an explicit fixed height, so
  the layout does not move when a chart is inserted later. It also defines `.chart-slot--filled`,
  which whatever inserts a chart will add to the slot.
- `ReportFormatter` validates the output and fails loudly with `LLMError` if it breaks the
  contract: not a single document, forbidden markup (scripts, links, images, SVG, iframes, event
  handlers, `@import`, non-`data:` `url()`), no A4 `@page` rule, no page sections, or anything
  other than exactly one slot per supplied chart.
- After rendering, the formatter compares the PDF page count with the number of
  `<section class="page">` elements and logs a warning on a mismatch, which means a page
  overflowed. It still saves the files so the result can be inspected.
- `tests/reporting/sample_report.html` is a hand-written, contract-compliant reference. Tests
  check it passes validation and renders to one PDF page per section.

## Alternatives considered

- **Shared stylesheet, model writes only markup:** consistent and cheap, with measured page
  heights, but the look does not vary per report. Tried first and replaced at the request of the
  project owner in favor of fully dynamic styling.
- **Model returns structured JSON that code renders:** most controllable, but a rigid schema for
  every report shape.
- **Client supplies the CSS:** gives callers control, but the model could not size content to it.

## Consequences

- Looks vary from run to run and fitting content to A4 pages depends on the model's own estimates.
  Overflow is detected only after the fact (a log warning), not prevented. If it is common, add a
  retry that feeds the overflow back to the model, or return to a shared stylesheet.
- More output tokens per report, because the model writes the CSS every time.
- Filling the chart slots is a later step and not yet implemented.
- Validation is a guardrail, not a sanitizer. The PDF renderer also disables JavaScript and blocks
  the network.
