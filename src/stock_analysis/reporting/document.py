"""Validating the report document the model returns.

The model is asked for one complete HTML document (see ``prompts/format_report.txt``). These
checks enforce that contract before the document is rendered or saved. They are a guardrail, not
a sanitizer: the PDF renderer also disables JavaScript and blocks the network.
"""

import re
from collections import Counter
from collections.abc import Sequence

from stock_analysis.llm import LLMError

# Anything the contract forbids: elements that load or run outside content, inline event
# handlers, and CSS that pulls in external resources (``data:`` URLs are fine).
_FORBIDDEN_MARKUP = re.compile(
    r"""
    <\s*/?\s*(?:script|link|base|iframe|object|embed|form|canvas|svg|img|video|audio)\b
    | \son[a-z]+\s*=            # inline event handler, e.g. onclick=
    | javascript:
    | http-equiv                # <meta http-equiv="refresh"> redirects
    | @import
    | url\(\s*(?!['"]?data:)    # url(...) that is not a data: URL
    """,
    re.IGNORECASE | re.VERBOSE,
)

# <section class="page ..."> : one printed page.
_PAGE_SECTION = re.compile(r'<section\b[^>]*\bclass\s*=\s*"[^"]*\bpage\b', re.IGNORECASE)

# @page { ... size: A4 ... } : the print rule that fixes the paper size.
_A4_PAGE_RULE = re.compile(r"@page\b[^{}]*\{[^}]*\bsize\s*:\s*A4\b", re.IGNORECASE)

# data-chart-id="price_history" : the marker on a chart slot.
_CHART_SLOT_ID = re.compile(r'data-chart-id\s*=\s*"([^"]*)"')


def count_page_sections(document: str) -> int:
    """Count the ``<section class="page">`` elements in a report document."""
    return len(_PAGE_SECTION.findall(document))


def validate_document(document: str, chart_ids: Sequence[str]) -> None:
    """Check the model's output against the output contract.

    Args:
        document: The HTML document the model returned.
        chart_ids: Ids of the charts the model was given; each must have exactly one slot.

    Raises:
        LLMError: If the output is not one complete HTML document of page sections, uses
            forbidden markup, lacks the A4 print rule, or does not contain exactly one slot per
            chart id.
    """
    text = document.strip()
    _check_is_single_document(text)
    _check_no_forbidden_markup(text)
    _check_has_a4_page_rule(text)
    body = _body_of(text)
    _check_has_page_sections(body)
    _check_chart_slots(body, chart_ids)


def _check_is_single_document(text: str) -> None:
    lowered = text.lower()
    if not (lowered.startswith("<!doctype html") and lowered.endswith("</html>")):
        raise LLMError(
            "Model output must be one HTML document from <!DOCTYPE html> to </html>; "
            f"got {text[:60]!r}."
        )


def _check_no_forbidden_markup(text: str) -> None:
    match = _FORBIDDEN_MARKUP.search(text)
    if match:
        raise LLMError(f"Model output contains forbidden markup: {match.group(0).strip()!r}.")


def _check_has_a4_page_rule(text: str) -> None:
    if not _A4_PAGE_RULE.search(text):
        raise LLMError("Model output must set '@page { size: A4; ... }' in its CSS.")


def _body_of(text: str) -> str:
    """Return everything from ``<body`` on, or an empty string if there is no body."""
    start = text.lower().find("<body")
    return text[start:] if start != -1 else ""


def _check_has_page_sections(body: str) -> None:
    if count_page_sections(body) == 0:
        raise LLMError('Model output needs a <body> containing <section class="page"> elements.')


def _check_chart_slots(body: str, expected_ids: Sequence[str]) -> None:
    """Require exactly one slot per expected chart, and no others.

    Only the body is searched, so CSS selectors that mention ``data-chart-id`` do not count.
    """
    placed = Counter(_CHART_SLOT_ID.findall(body))
    expected = set(expected_ids)

    missing = sorted(expected - placed.keys())
    unknown = sorted(placed.keys() - expected)
    duplicated = sorted(chart_id for chart_id, times in placed.items() if times > 1)

    problems = [f"missing slot for chart {chart_id!r}" for chart_id in missing]
    problems += [f"unknown chart slot {chart_id!r}" for chart_id in unknown]
    problems += [f"chart {chart_id!r} placed {placed[chart_id]} times" for chart_id in duplicated]
    if problems:
        raise LLMError("Model output has chart slot problems: " + "; ".join(problems) + ".")
