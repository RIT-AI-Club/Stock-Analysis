"""HTML to PDF conversion. The browser engine sits behind :class:`PdfConverter`."""

import logging
import re
from typing import Protocol

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Route, async_playwright

logger = logging.getLogger(__name__)


class PdfConversionError(RuntimeError):
    """Raised when HTML cannot be converted to PDF."""


class PdfConverter(Protocol):
    """Anything that can render an HTML document to PDF bytes."""

    async def html_to_pdf(self, html: str) -> bytes:
        """Convert an HTML document to PDF.

        Args:
            html: A complete HTML document.

        Returns:
            The PDF file contents.

        Raises:
            PdfConversionError: If rendering fails.
        """
        ...


# A page object in a PDF is written "/Type /Page"; the page tree is "/Type /Pages", so the
# character after "Page" must not be "s".
_PDF_PAGE_OBJECT = re.compile(rb"/Type\s*/Page[^s]")


def pdf_page_count(pdf: bytes) -> int | None:
    """Count the pages in a PDF, or return ``None`` if no page objects are recognized.

    This scans for page objects instead of parsing the file, which is enough for the plain PDFs
    that Chromium writes.
    """
    count = len(_PDF_PAGE_OBJECT.findall(pdf))
    return count or None


async def _block_request(route: Route) -> None:
    await route.abort()


class PlaywrightPdfConverter:
    """Renders HTML to PDF with headless Chromium via Playwright.

    The HTML is model-generated, so it is rendered defensively: JavaScript is disabled and all
    network requests are blocked. Remote images, fonts, and stylesheets will not load; inline
    styles and ``data:`` URLs work.

    Requires the browser binary: ``uv run playwright install chromium``.
    """

    async def html_to_pdf(self, html: str) -> bytes:
        """Convert an HTML document to PDF. See :meth:`PdfConverter.html_to_pdf`."""
        logger.info("Converting HTML (%d chars) to PDF", len(html))
        try:
            return await self._render(html)
        except PlaywrightError as exc:
            raise PdfConversionError(f"PDF conversion failed: {exc}") from exc

    @staticmethod
    async def _render(html: str) -> bytes:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                # The HTML is untrusted, so render with no JavaScript and no network.
                context = await browser.new_context(java_script_enabled=False)
                page = await context.new_page()
                await page.route("**/*", _block_request)

                await page.set_content(html, wait_until="load")
                return await page.pdf(format="A4", print_background=True)
            finally:
                await browser.close()
