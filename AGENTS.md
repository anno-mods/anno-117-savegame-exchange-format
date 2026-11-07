# AGENTS.md

Guidance for coding agents working in this repository.

## What this repo is

Hand-off bundle for a tool-neutral Anno 117 exchange format: requirements, investigations, scripts, saves and tests.
The contract is `docs/spec/exchange-format-requirements.md`. Read it and `README.md` first.
This is branch `evidence`; `main` holds the specification, general findings and roadmap only.

## Commands

```
uv sync
uv run pytest -q                 # offline tests
uv run ruff check scripts tests
```

Environment variables: `ANNO_PLANNER_REPO`, `ANNO_CALC_REPO`, `ANNO_DECODED`, `ANNO_OUT` (see README).
Tests that need them skip with a reason when they are not set.

## Rules

- Windows is the main platform; scripts must not hard-code user paths. Take paths from arguments or the environment
  variables above.
- Source files are ASCII-only. Non-ASCII belongs in data only (island names, game texts).
- Do not commit decoded savegame XML or other generated intermediates (hundreds of MB). `outputs/` stays empty in git.
- `scripts/probes/` is exploratory and kept as it was; do not refactor it. Cleaned, reproducible scripts live in
  `scripts/savegame_to_planner/`, `scripts/calculator_config/` and `docs/analysis/derived-trade-flow-accuracy/scripts/`.
- The canonical copy of the savegame script is in the Anno-117-Layout-Tool repo (`tools/savegame_to_planner`). Changes
  made here must go back there.
- Treat numbers in `docs/` as measurements of one save (`Marcia 69`, game time about 2 hours of recorded trades);
  they size errors, they are not validated bounds.
- Documents state the current knowledge. No correction history, no "earlier version" notes. Avoid filler intensifiers.
- Saves and configs hold personal game data. Do not copy them elsewhere or publish them.
