"""Saving generated reports to disk (HTML and PDF go to separate directories)."""

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_MAX_SLUG_LENGTH = 50


@dataclass(frozen=True, slots=True)
class SavedReport:
    """Where a report was written.

    Attributes:
        html_path: Path of the saved HTML file.
        pdf_path: Path of the saved PDF file.
    """

    html_path: Path
    pdf_path: Path


class ReportStore:
    """Writes each report as ``<html_dir>/<name>.html`` and ``<pdf_dir>/<name>.pdf``.

    Args:
        html_dir: Directory for HTML files. Created if missing.
        pdf_dir: Directory for PDF files. Created if missing.
    """

    def __init__(self, html_dir: Path, pdf_dir: Path) -> None:
        self._html_dir = html_dir
        self._pdf_dir = pdf_dir

    def save(self, html: str, pdf: bytes, *, title: str | None = None) -> SavedReport:
        """Save a report's HTML and PDF under a shared, timestamped name.

        Args:
            html: The HTML report.
            pdf: The PDF rendering of the report.
            title: Optional report title, used in the file name.

        Returns:
            The paths written.
        """
        name = _file_stem(title)
        saved = SavedReport(
            html_path=self._html_dir / f"{name}.html",
            pdf_path=self._pdf_dir / f"{name}.pdf",
        )

        self._html_dir.mkdir(parents=True, exist_ok=True)
        self._pdf_dir.mkdir(parents=True, exist_ok=True)
        saved.html_path.write_text(html, encoding="utf-8")
        saved.pdf_path.write_bytes(pdf)

        logger.info(
            "Saved report to %s and %s", saved.html_path.resolve(), saved.pdf_path.resolve()
        )
        return saved


def _file_stem(title: str | None) -> str:
    """Build a unique, filesystem-safe name like ``20261105T143012123456Z-q3-review``."""
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{timestamp}-{_slugify(title)}"


def _slugify(title: str | None) -> str:
    """Lowercase a title and reduce it to ``a-z``, ``0-9`` and single hyphens (never empty)."""
    hyphenated = re.sub(r"[^a-z0-9]+", "-", (title or "").lower())
    slug = hyphenated.strip("-")[:_MAX_SLUG_LENGTH].strip("-")
    return slug or "report"
