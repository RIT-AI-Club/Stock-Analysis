from pathlib import Path

import pytest

from stock_analysis.reporting import ReportStore


def test_save_writes_html_and_pdf_to_separate_directories(tmp_path: Path) -> None:
    store = ReportStore(tmp_path / "out" / "html", tmp_path / "out" / "pdf")
    saved = store.save("<p>hi</p>", b"%PDF", title="My Report!")
    assert saved.html_path.parent == tmp_path / "out" / "html"
    assert saved.pdf_path.parent == tmp_path / "out" / "pdf"
    assert saved.html_path.read_text(encoding="utf-8") == "<p>hi</p>"
    assert saved.pdf_path.read_bytes() == b"%PDF"
    assert saved.html_path.stem == saved.pdf_path.stem


@pytest.mark.parametrize(
    ("title", "suffix"),
    [
        (None, "-report"),
        ("", "-report"),
        ("../../etc/passwd", "-etc-passwd"),
        ("AAPL: Q3 / 2026", "-aapl-q3-2026"),
    ],
)
def test_save_builds_safe_file_names(tmp_path: Path, title: str | None, suffix: str) -> None:
    saved = ReportStore(tmp_path / "h", tmp_path / "p").save("x", b"x", title=title)
    assert saved.html_path.stem.endswith(suffix)
    assert saved.html_path.parent == tmp_path / "h"


def test_save_keeps_names_unique_across_calls(tmp_path: Path) -> None:
    store = ReportStore(tmp_path / "h", tmp_path / "p")
    first = store.save("a", b"a")
    second = store.save("b", b"b")
    assert first.html_path != second.html_path
