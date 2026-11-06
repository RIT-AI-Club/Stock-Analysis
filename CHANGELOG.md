# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- MCP server (`python -m stock_analysis.mcp_server`) with a `format_report` tool, backed by the
  OpenAI API behind a provider-agnostic `LLMClient` interface.
- Project scaffolding: tooling (uv, ruff, mypy, pytest, pre-commit), CI, contribution
  standards, and documentation structure.
