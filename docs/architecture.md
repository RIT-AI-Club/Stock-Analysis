# Architecture

> **Status:** Not yet designed. Fill in each section as components are built. Keep it current:
> a PR that changes how components connect updates this file.

## Overview

<!-- One paragraph: what the system does end to end, from user input to output. -->

## System diagram

<!-- A Mermaid diagram renders natively on GitHub. Example:

```mermaid
flowchart LR
    UI[Frontend] -> API[API]
    API ==> Core[Core library]
    Core ==> Data[(Market data)]
    Core ==> LLM[LLM provider]
```
-->

## Components

<!-- For each component: responsibility, location in the repo, and what it depends on. -->

| Component | Location | Responsibility |
|---|---|---|
| MCP client | `src/stock_analysis/backend/mcp_client.py` | Connects to every configured MCP server, merges their tools into one set, and routes tool calls to the owning server. Contains no LLM logic. See [ADR 0003](adr/0003-mcp-client-design.md). |
| MCP config | `src/stock_analysis/backend/mcp_config.py`, `config/mcp_servers.yaml` | Declares and validates the servers to connect to. `${VAR}` references pull secrets from the environment. |

## Data flow

<!-- Walk through one request, for example "user asks for a report on AAPL", step by step. -->

## External services

<!-- Every third-party API: what it's used for, the env var for its key, rate limits, and the
     ToS notes that matter. -->

| Service | Purpose | Config | Notes |
|---|---|---|---|
| | | | |

## Key decisions

See [Architecture Decision Records](adr/).
