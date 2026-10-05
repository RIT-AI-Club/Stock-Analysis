# AGENTS.md

Guidance for AI coding assistants working in this repo. Human-facing standards live in
[CONTRIBUTING.md](CONTRIBUTING.md). Follow them; this file only summarizes.

## Project

AI-assisted equity research and reporting (RIT AI Club). Ground-up rewrite of FinRLExtension.
Python 3.13, src layout: package in `src/stock_analysis/`, tests in `tests/` mirroring it.

## Commands

```bash
uv sync                                   # install
uv run pytest                             # tests (offline unit tests only by default in CI)
uv run ruff check --fix && uv run ruff format
uv run mypy                               # strict
uv run pre-commit run --all-files         # everything CI checks
uv add <pkg> / uv add --dev <pkg>         # dependencies - never edit uv.lock
```

## Rules

- Type hints everywhere (mypy strict). Google-style docstrings on public APIs.
- `logging`, never `print`. Timezone-aware datetimes only.
- Keep business logic in plain core modules; API/CLI/MCP/UI are thin wrappers.
- Wrap external services (LLMs, market data) behind interfaces; unit tests fake them and never
  hit the network. Real-service tests get `@pytest.mark.integration`.
- Fail loudly. Never fall back silently to fake or default data.
- No secrets in code; config comes from env vars documented in `.env.example`.
- Delete dead code; don't comment it out.
- Conventional Commits (`feat:`, `fix:`, ...). Work on branches, never commit to `main`.
- Update docs in the same change: README, `.env.example`, `docs/architecture.md`, a new ADR in
  `docs/adr/` for significant decisions, and `CHANGELOG.md` under Unreleased.
