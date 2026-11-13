import pytest

from stock_analysis.llm import LLMError
from stock_analysis.reporting.document import count_page_sections, validate_document
from tests.fakes import DOC, make_document


def slot(chart_id: str) -> str:
    return f'<div class="chart-slot" data-chart-id="{chart_id}"></div>'


def test_validate_accepts_a_document_with_exactly_one_slot_per_chart() -> None:
    validate_document(make_document(slot("a") + slot("b")), ["a", "b"])


def test_validate_accepts_a_document_with_no_charts() -> None:
    validate_document(DOC, [])


def test_validate_ignores_chart_id_selectors_in_css() -> None:
    doc = DOC.replace("</style>", '[data-chart-id="a"]{color:red}</style>')
    validate_document(doc.replace("</section>", slot("a") + "</section>"), ["a"])


@pytest.mark.parametrize(
    "document",
    [
        "Here is your report: " + DOC,
        "```html\n" + DOC + "\n```",
        '<section class="page"></section>',
        DOC + "\nThanks!",
        "",
    ],
)
def test_validate_rejects_anything_but_one_complete_document(document: str) -> None:
    with pytest.raises(LLMError, match="must be one HTML document"):
        validate_document(document, [])


@pytest.mark.parametrize(
    "markup",
    [
        "<script>alert(1)</script>",
        '<img src="x.png">',
        '<iframe src="https://example.com"></iframe>',
        '<link rel="stylesheet" href="x.css">',
        '<svg><circle r="1"/></svg>',
        '<p onclick="x()">hi</p>',
        '<a href="javascript:alert(1)">x</a>',
        "<SCRIPT>x</SCRIPT>",
        '<meta http-equiv="refresh" content="0;url=https://example.com">',
    ],
)
def test_validate_rejects_forbidden_markup(markup: str) -> None:
    with pytest.raises(LLMError, match="forbidden markup"):
        validate_document(make_document(markup), [])


@pytest.mark.parametrize(
    "css",
    [
        '@import url("https://example.com/x.css");',
        '.a{background:url("https://example.com/x.png")}',
        ".a{background:url(//example.com/x.png)}",
    ],
)
def test_validate_rejects_external_resources_in_css(css: str) -> None:
    with pytest.raises(LLMError, match="forbidden markup"):
        validate_document(DOC.replace("</style>", css + "</style>"), [])


def test_validate_allows_data_urls_in_css() -> None:
    css = '.a{background:url("data:image/png;base64,AAAA")}'
    validate_document(DOC.replace("</style>", css + "</style>"), [])


def test_validate_requires_the_a4_page_rule() -> None:
    with pytest.raises(LLMError, match="@page"):
        validate_document(DOC.replace("size: A4", "size: Letter"), [])


def test_validate_requires_page_sections_in_the_body() -> None:
    with pytest.raises(LLMError, match="<section"):
        validate_document(DOC.replace('class="page"', 'class="slide"'), [])


def test_validate_reports_every_chart_slot_problem() -> None:
    document = make_document(slot("a") + slot("a") + slot("rogue"))
    with pytest.raises(LLMError) as exc:
        validate_document(document, ["a", "missing"])
    message = str(exc.value)
    assert "missing slot for chart 'missing'" in message
    assert "unknown chart slot 'rogue'" in message
    assert "chart 'a' placed 2 times" in message


def test_count_page_sections() -> None:
    document = DOC.replace("</body>", '<section class="page extra"></section></body>')
    assert count_page_sections(document) == 2
