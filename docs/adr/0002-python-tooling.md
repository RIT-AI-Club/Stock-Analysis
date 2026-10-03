# 0002. Python tooling: uv, ruff, mypy, pytest

- **Status:** Accepted
- **Date:** 2026-10-01
- **Deciders:** @knicolosi313

## Context

FinRLExtension used a hand-maintained `requirements.txt` with no lockfile, no linter or type
checker, and no CI. Contributors' environments drifted, and problems were found late. We want a
setup where "works on my machine" means it works everywhere, and where style is automated
instead of debated.

## Decision

- **uv** for Python versions, virtual environments, and dependencies, with a committed `uv.lock`.
- **ruff** for linting and formatting, including Google-style docstring rules.
- **mypy** in strict mode for type checking.
- **pytest** for tests, with external services faked in unit tests.
- **pre-commit** runs these checks locally, along with gitleaks for secrets and Conventional
  Commit message checks.
- **GitHub Actions** runs the same checks on every PR, and they must pass before merging.

All configuration lives in `pyproject.toml` and `.pre-commit-config.yaml`.

## Alternatives considered

- **pip + requirements.txt:** no lockfile by default, and slow.
- **Poetry:** solid, but slower than uv, and uv also manages Python versions.
- **black + isort + flake8:** three tools where ruff is one, and much faster.
- **pyright instead of mypy:** also good. mypy chosen for its wide familiarity. Revisit if it
  becomes a bottleneck.

## Consequences

- One command (`uv sync`) gives every contributor an identical environment.
- Strict typing and docstring rules slow down the first draft of code, but catch bugs early and
  keep the codebase readable.
- Contributors must install uv.
