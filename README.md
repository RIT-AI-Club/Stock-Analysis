# Stock-Analysis

[![CI](https://github.com/RIT-AI-Club/Stock-Analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/RIT-AI-Club/Stock-Analysis/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

AI-assisted equity research and reporting, built by the RIT AI Club. A ground-up rewrite of
FinRLExtension.

> **Status: early development.** Nothing is runnable yet. See [CHANGELOG.md](CHANGELOG.md).

> [!WARNING]
> This project is for educational and research purposes only. Nothing it produces is
> financial or investment advice. Do your own research and consult a licensed professional
> before making investment decisions.

## Getting started

**Prerequisites:** [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git.
uv installs the correct Python version for you.

```bash
git clone git@github.com:RIT-AI-Club/Stock-Analysis.git
cd Stock-Analysis
uv sync                      # create .venv and install everything from uv.lock
uv run pre-commit install    # enable the git hooks
cp .env.example .env         # then fill in your keys
```

Run the checks CI runs:

```bash
uv run ruff check && uv run ruff format --check && uv run mypy && uv run pytest
```

## Project structure

```
src/stock_analysis/   Application package
tests/                Tests (mirrors src/ layout)
docs/                 Architecture docs and decision records (docs/adr/)
.github/              CI workflows, issue/PR templates, CODEOWNERS
```

## Documentation

- [Architecture](docs/architecture.md): how the system fits together
- [Architecture Decision Records](docs/adr/): why it's built this way
- [Contributing guide](CONTRIBUTING.md): setup, workflow, and coding standards

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR. All participants are expected to
follow the [Code of Conduct](CODE_OF_CONDUCT.md).
