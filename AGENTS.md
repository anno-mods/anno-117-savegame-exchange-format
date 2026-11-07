# AGENTS.md

Guidance for coding agents working in this repository.

## What this repo is

Specification and findings for a tool-neutral Anno 117 exchange format. The contract is
`docs/spec/exchange-format-requirements.md`. Read it and `README.md` first.

## Branches

`main` holds the specification, general findings and roadmap. Saves, derived configs, scripts, probes, the accuracy
analysis and the tests are on branch `evidence`, which has its own README and commands. Do not add binary files,
decoded savegame XML or sample-specific evaluations to `main`.

## Rules

- Documents state the current knowledge. No correction history, no "earlier version" notes. Avoid filler intensifiers.
- Source files are ASCII-only. Non-ASCII belongs in data only.
- Numbers in `docs/` are measurements of one sample game; they size errors and are not validated bounds.
- Paths in documents that point to `docs/analysis/`, `docs/findings/calculator-config-update.md`, `data/`, `scripts/`
  or `tests/` exist on `evidence` only.
