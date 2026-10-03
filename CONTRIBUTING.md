# Contributing

This guide is the source of truth for how we work. If something here is wrong or missing, fix it
in a PR. These standards change through review like everything else.

## Contents

1. [Setup](#setup)
2. [Workflow](#workflow)
3. [Commit messages](#commit-messages)
4. [Pull requests](#pull-requests)
5. [Code standards](#code-standards)
6. [Testing](#testing)
7. [Documentation standards](#documentation-standards)
8. [Dependencies](#dependencies)
9. [Configuration and secrets](#configuration-and-secrets)
10. [Financial data rules](#financial-data-rules)

---

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone and install:

   ```bash
   git clone git@github.com:RIT-AI-Club/Stock-Analysis.git
   cd Stock-Analysis
   uv sync
   uv run pre-commit install
   cp .env.example .env
   ```

3. In VS Code, install the recommended extensions when prompted (`.vscode/extensions.json`).

Always run tools through `uv run ...` so they use the project's locked environment.

## Workflow

1. **Start from an issue.** Every change of meaningful size has a GitHub issue. Comment on it to
   claim it so two people don't build the same thing.
2. **Branch from `main`.** Name branches `<type>/<short-description>`:

   ```
   feat/12-price-data-loader
   fix/31-timezone-offset
   docs/8-architecture-overview
   ```

   Types match the commit types below.
3. **Keep branches short-lived.** Aim to merge within a few days. Rebase on `main` if you fall
   behind (`git pull --rebase origin main`).
4. **Open a PR** (draft early if you want feedback). CI must pass and one reviewer must approve.
5. **Squash merge.** The PR title becomes the commit on `main`, so it must follow the commit
   format.

Nobody pushes directly to `main`. Branch protection enforces this.

## Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/). A pre-commit hook enforces
the format.

```
<type>(<optional scope>): <summary in imperative mood, lowercase, no period>

<optional body: what and why, not how>

<optional footer: Closes #12, BREAKING CHANGE: ...>
```

| Type | Use for |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or fixing tests |
| `perf` | Performance improvement |
| `build` | Dependencies, packaging |
| `ci` | CI configuration |
| `chore` | Maintenance that doesn't fit elsewhere |

Good: `feat(data): add daily OHLCV loader`. Bad: `updated stuff`, `Fixed bug.`

## Pull requests

- **Small and focused.** One logical change per PR. Under ~400 changed lines is a good target.
  Split big features into stacked PRs.
- **Fill in the template.** Especially "Why" and "How to test".
- **Self-review first.** Read your own diff on GitHub before requesting review.
- **Reviewers:** respond within 2 days. Prefix optional suggestions with `nit:`. Approve when
  it's good enough, not when it's how you'd have written it.
- **Authors:** resolve every conversation before merging, either by changing the code or by
  replying with the reason you didn't.

## Code standards

Tooling enforces most of these: ruff (lint and format), mypy (strict types), and pre-commit. If the
tools pass, style debates are over.

### General

- **Python 3.13+.** Use modern syntax (`list[str]`, `X | None`, `match`).
- **Type hints on everything.** mypy runs in strict mode. Avoid `Any`. When you can't, leave a
  comment explaining why.
- **Line length is 100.** The formatter handles it.
- **Naming:** `snake_case` for functions and variables, `PascalCase` for classes,
  `UPPER_SNAKE_CASE` for constants, a leading `_` for private.
- **Use `logging`, never `print`.** Get a module logger with `logger = logging.getLogger(__name__)`.
- **Use `pathlib.Path`, not string paths.**
- **Datetimes must be timezone-aware.** Market data crosses timezones; naive datetimes cause
  silent bugs. Ruff's `DTZ` rules enforce this.

### Design

- **Separate the core from the interfaces.** Business logic (data fetching, analysis, report
  building) lives in plain, testable modules. Interfaces such as the API, CLI, MCP servers and UI
  are thin wrappers that call into the core.
- **Use typed data between components.** Pass Pydantic models or dataclasses, not loose `dict`s.
- **Put external services behind interfaces.** Wrap every third-party API (LLMs, market data) in
  a small class or protocol so it can be swapped or faked in tests.
- **Fail loudly.** Never silently fall back to fake, random, or default data. If a dependency or
  API key is missing, raise a clear error. A wrong chart that looks right is worse than a crash.
- **Catch specific exceptions only.** No bare `except:` or `except Exception: pass`.
- **Don't keep dead code.** Delete it. Git remembers. No `_old` folders or commented-out blocks.

## Testing

- Tests live in `tests/`, mirroring `src/stock_analysis/` (for example `src/stock_analysis/data/loader.py`
  is tested by `tests/data/test_loader.py`).
- **Unit tests must run offline and for free.** Mock or fake every network call, LLM, and paid
  API. CI has no API keys.
- Mark tests that hit real services with `@pytest.mark.integration`. CI skips them; run them
  locally with `uv run pytest -m integration`.
- Every bug fix includes a test that would have caught it.
- Name tests by behavior: `test_loader_raises_when_ticker_unknown`, not `test_loader_2`.
- Coverage target is **80%** for core logic. The CI threshold will be raised once real code
  exists.

## Documentation standards

### Docstrings

Every public module, class, function, and method gets a
[Google-style docstring](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
Ruff enforces this.

```python
def moving_average(prices: Sequence[float], window: int) -> list[float]:
    """Compute the simple moving average of a price series.

    Args:
        prices: Closing prices, oldest first.
        window: Number of periods to average. Must be positive.

    Returns:
        The moving average, with length ``len(prices) - window + 1``.

    Raises:
        ValueError: If ``window`` is not positive or exceeds ``len(prices)``.
    """
```

- The first line is a one-sentence summary in imperative mood ("Compute...", not "Computes...").
- Don't repeat the type hints in prose. Document meaning, units, and constraints instead.

### Comments

Explain **why**, not **what**. If code needs a comment to explain what it does, rename things
or simplify it first. Link the issue in `TODO` comments: `# TODO(#42): handle splits`.

### Where docs go

| Change | Update |
|---|---|
| New setup step, command, or prerequisite | `README.md` |
| New environment variable | `.env.example` (with a comment) |
| New component or change to how parts connect | `docs/architecture.md` |
| A significant technical decision (library, pattern, provider, data source) | New ADR in `docs/adr/` |
| User-facing change | `CHANGELOG.md` under **Unreleased** |

Docs ship in the same PR as the code they describe.

### Architecture Decision Records

Write an ADR when a decision would be expensive to reverse or when someone will later ask "why
did we do it this way?" Copy `docs/adr/0000-template.md`, take the next number, and open it in
a PR for discussion. Don't edit an ADR after it's accepted. Supersede it with a new one.

## Dependencies

- Add with `uv add <package>` (or `uv add --dev <package>` for dev tools). Commit `pyproject.toml`
  and `uv.lock` together.
- Justify every new runtime dependency in the PR description. Prefer the standard library or an
  existing dependency.
- Never edit `uv.lock` by hand.
- Dependabot opens weekly update PRs. Review and merge them promptly.

## Configuration and secrets

- All configuration comes from environment variables, loaded from `.env` locally. Every variable
  is documented in `.env.example`.
- **Never commit secrets.** gitleaks runs in pre-commit and CI. If you commit a key by accident,
  **revoke it immediately** (rewriting history is not enough) and tell a maintainer.
- Generated output (reports, downloaded data, charts) goes in gitignored directories and is
  never committed.

## Financial data rules

- **Cite your sources.** Any figure shown to a user must trace back to a named data source and an
  as-of date.
- **Make reports reproducible.** Record the inputs (tickers, date ranges, data source, model
  versions) used to generate each report.
- **Never present output as investment advice.** User-facing reports carry the disclaimer from
  the README.
- **Respect terms of service.** Check a data provider's ToS and rate limits before integrating
  it.
