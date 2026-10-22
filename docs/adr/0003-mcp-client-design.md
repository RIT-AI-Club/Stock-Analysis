# 0003. Provider-agnostic multi-server MCP client

- **Status:** Accepted
- **Date:** 2026-10-05
- **Deciders:** @knicolosi313

## Context

The system's capabilities (research, charting, report formatting) are exposed as MCP servers,
and an LLM decides which tools to call. In FinRLExtension, `mcp_client.py` combined three jobs:
managing MCP connections, translating tools for Gemini, and running the agent loop. Because they
were tangled together, switching LLM providers meant rewriting the client, and testing required
live API keys.

The official MCP Python SDK (2.x) provides `mcp.Client`, which handles one connection to one
server over stdio, Streamable HTTP, or in-process.

## Decision

`stock_analysis.backend.mcp_client.MCPClient` handles **MCP only**:

- It wraps one `mcp.Client` per configured server and connects them all inside a single
  `async with`.
- It merges every server's tools into one flat set. A tool name provided by two servers is a
  configuration error, not silently shadowed.
- It routes `call_tool` to the owning server. A tool that reports a failure returns a
  `ToolResult` with `is_error=True` so the agent can show the error to the model. Protocol
  failures (timeouts, crashes) raise `ToolCallError`.
- It knows nothing about LLMs. The agent loop is a separate component that uses `MCPClient` and
  converts its `Tool` objects to whichever provider's format it needs.

Servers are declared in `config/mcp_servers.yaml`, loaded with `yaml.safe_load`, and validated
with Pydantic. Secrets are referenced as `${VAR}` and expanded from the environment. A
reference to an unset variable is an error.

## Alternatives considered

- **`mcp.ClientSessionGroup`:** the SDK's own multi-server helper. It is close to what we need,
  and it also rejects duplicate tool names unless given a renaming hook. But it is built on the
  lower-level `ClientSession` rather than `mcp.Client`. That means giving up the high-level
  client's protocol-version negotiation, response caching, and automatic handling of
  input-required tool calls, and it can't connect to in-process servers, which our tests rely on.
  Wrapping `mcp.Client` costs about 100 lines.
- **One combined client plus agent class (as in FinRLExtension):** simpler at first, but it ties
  the code to one LLM provider and makes offline tests impossible.
- **TOML config:** needs no extra dependency (`tomllib` is in the standard library), but
  nested server tables are more awkward to read and write than YAML. YAML is also what
  FinRLExtension used and what most MCP tooling documents. YAML's implicit typing (`yes` is a
  boolean, `8080` is a number) is handled by converting numbers to strings in `env` and
  rejecting other non-string values.

## Consequences

- The LLM provider can change without touching MCP code, and the agent loop can be tested with
  a fake `MCPClient`.
- Tests use in-process `MCPServer` instances plus one real stdio subprocess, with no network
  and no API keys.
- Tool names must be globally unique. Server authors need to pick distinct names (for example
  `research_stock`, not `get`).
- Servers connect one after another at startup. That's fine for a handful of servers; revisit
  if startup becomes slow.
- Only stdio and unauthenticated HTTP are supported. Authenticated remote servers will need
  header or OAuth support added to the config.
