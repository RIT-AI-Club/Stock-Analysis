# 0003. MCP server with a provider-agnostic LLM interface

- **Status:** Accepted
- **Date:** 2026-11-05
- **Deciders:** @knicolosi313

## Context

We want LLM capabilities exposed to MCP clients (Claude Desktop, IDEs, our own agents). The
first tool calls OpenAI. We expect to add more tools and possibly more providers, and unit
tests must never hit the network.

## Decision

- The MCP server (`stock_analysis.mcp_server`) is a thin wrapper built on the official `mcp`
  SDK (`MCPServer`) over the stdio transport. Tools only delegate; they hold no logic. It
  exposes one tool, `format_report`, which delegates to `ReportFormatter`
  (`stock_analysis.reporting`).
- LLM access sits behind an `LLMClient` Protocol (`stock_analysis.llm.base`). `OpenAIClient`
  implements it using the OpenAI Responses API. `ReportFormatter` takes the client by
  injection, and `create_server(formatter)` takes the formatter, so tests pass a fake LLM.
- Configuration comes from env vars via `Settings.from_env()`, which raises `ConfigError` if
  `OPENAI_API_KEY` is missing instead of defaulting.
- SDK failures and empty responses surface as `LLMError`; nothing is swallowed.

## Alternatives considered

- **Call OpenAI directly inside the tool:** simpler, but couples tools to one provider and makes
  faking hard.
- **Chat Completions API:** older; the Responses API is OpenAI's current recommended interface.

## Consequences

- Adding a provider means one new class implementing `LLMClient`.
- Adding a tool means one function in `create_server`, delegating to a core module.
- Formatting is done by an LLM, so the system prompt forbids changing facts or figures. This is
  not enforced in code; review outputs before relying on them.
- The server pins to `mcp` 2.x (`MCPServer`, not the 1.x `FastMCP`).
