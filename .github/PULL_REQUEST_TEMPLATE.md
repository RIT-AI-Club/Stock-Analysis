## What

<!-- One or two sentences: what does this PR change? -->

## Why

<!-- The problem it solves. Link the issue: "Closes #123". -->

## How to test

<!-- Steps a reviewer can follow to verify it works. -->

## Checklist

- [ ] PR title follows [Conventional Commits](https://www.conventionalcommits.org/) (`feat: ...`, `fix: ...`)
- [ ] Tests added or updated, and `uv run pytest` passes
- [ ] `uv run pre-commit run --all-files` passes
- [ ] Public functions/classes have type hints and Google-style docstrings
- [ ] Docs updated (README, `docs/`, `.env.example`) if behavior or config changed
- [ ] `CHANGELOG.md` updated under **Unreleased** for user-facing changes
- [ ] ADR added in `docs/adr/` if this makes an architectural decision
- [ ] No secrets, API keys, or generated output (reports, data) committed
