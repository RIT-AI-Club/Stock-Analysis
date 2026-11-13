"""The sample report is the reference for what contract-compliant model output looks like."""

from importlib import resources
from pathlib import Path

from stock_analysis.reporting.document import count_page_sections, validate_document

PROMPT = (
    resources.files("stock_analysis.reporting")
    .joinpath("prompts/format_report.txt")
    .read_text(encoding="utf-8")
)
SAMPLE = (Path(__file__).parent / "sample_report.html").read_text(encoding="utf-8")


def test_sample_report_satisfies_the_output_contract() -> None:
    validate_document(SAMPLE, ["price_history", "annual_revenue", "annual_eps", "gross_margin"])
    assert count_page_sections(SAMPLE) == 4


def test_prompt_states_the_hard_rules() -> None:
    for phrase in (
        "Never invent",
        "Preserve every number exactly",
        "exactly once",
        "<!DOCTYPE html>",
        "@page { size: A4; margin: 0; }",
        "chart-slot--filled",
        "data-chart-id",
    ):
        assert phrase in PROMPT


def test_prompt_baseline_css_is_what_the_sample_uses() -> None:
    # The sample must follow the same print baseline the prompt demands.
    for rule in (
        "@page { size: A4; margin: 0; }",
        "print-color-adjust: exact",
        "break-after: page",
    ):
        assert rule in PROMPT
        assert rule in SAMPLE
