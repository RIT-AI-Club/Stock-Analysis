"""Core report formatting logic. Independent of MCP; depends only on :class:`LLMClient`."""

from importlib import resources

from stock_analysis.llm import LLMClient


def _load_system_prompt() -> str:
    """Read the formatting system prompt packaged in ``reporting/prompts/``."""
    prompt = resources.files(__package__).joinpath("prompts/format_report.txt")
    return prompt.read_text(encoding="utf-8").strip()


class ReportFormatter:
    """Formats raw report content into a structured, readable HTML report.

    Args:
        llm: LLM backend that performs the formatting.
    """

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self._system_prompt = _load_system_prompt()

    async def format_report(
        self,
        content: str,
        *,
        title: str | None = None,
        instructions: str | None = None,
    ) -> str:
        """Format a report as HTML.

        Args:
            content: The raw report content to format.
            title: Optional title to place at the top of the report.
            instructions: Optional extra formatting instructions (e.g. section order).

        Returns:
            The formatted report as an HTML document.

        Raises:
            ValueError: If ``content`` is empty.
            LLMError: If the LLM call fails.
        """
        if not content.strip():
            raise ValueError("content must not be empty.")
        prompt = self._build_prompt(content, title, instructions)
        return await self._llm.complete(prompt, system_prompt=self._system_prompt)

    @staticmethod
    def _build_prompt(content: str, title: str | None, instructions: str | None) -> str:
        lines: list[str] = []
        if title:
            lines.append(f"Title: {title}")
        if instructions:
            lines.append(f"Additional instructions: {instructions}")
        lines.append(f"Report content:\n{content}")
        return "\n".join(lines)
