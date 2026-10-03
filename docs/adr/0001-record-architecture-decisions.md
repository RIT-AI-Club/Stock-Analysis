# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-01
- **Deciders:** @knicolosi313

## Context

This project is a rewrite of FinRLExtension, and several club members will contribute over time.
In the previous project, the reasons behind design choices lived only in people's heads and in
scattered README notes. New contributors couldn't tell which choices were deliberate and which
were accidental.

## Decision

We will record significant technical decisions as Architecture Decision Records in `docs/adr/`,
using the template in `0000-template.md`. A decision is "significant" if it is expensive to
reverse or if someone will later reasonably ask why it was made.

## Alternatives considered

- **Wiki or Google Doc:** lives outside the repo, isn't versioned with the code, and isn't
  reviewed in PRs.
- **README sections only:** the README grows unbounded and loses history when edited.

## Consequences

- Decisions are reviewable in PRs and versioned alongside the code they affect.
- Contributors spend a small amount of time writing ADRs for big changes.
