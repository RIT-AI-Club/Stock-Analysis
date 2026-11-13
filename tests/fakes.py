"""Test doubles for external services. Unit tests use these and never touch the network."""

from stock_analysis.reporting import PdfConversionError

_CSS = "@page { size: A4; margin: 0; }"


def make_document(body: str = "") -> str:
    """A minimal, contract-compliant report document whose pages contain ``body``."""
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f'<style>{_CSS}</style></head><body><section class="page">{body}</section></body></html>'
    )


DOC = make_document()


class FakeLLM:
    def __init__(self, reply: str = DOC) -> None:
        self.reply = reply
        self.calls: list[tuple[str, str | None]] = []

    async def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        self.calls.append((prompt, system_prompt))
        return self.reply


class FakePdfConverter:
    def __init__(self, *, fail: bool = False, pdf: bytes = b"%PDF-fake") -> None:
        self.fail = fail
        self.pdf = pdf
        self.inputs: list[str] = []

    async def html_to_pdf(self, html: str) -> bytes:
        self.inputs.append(html)
        if self.fail:
            raise PdfConversionError("boom")
        return self.pdf
