# Anno 117 savegame exchange format

Research and reference implementation for a tool-neutral exchange format between the **Taludas Planner**, the
**anno-117-calculator** and tools that read Anno 117 savegames (for example the Anno-117-Layout-Tool). This repo
bundles the requirements, the investigations, the scripts, the saves and the tests needed to review the work and to
implement the planner side.

Status: requirements are settled, the format is not implemented yet. The key catalog in the requirements is a first
draft; names are working names.

This is the `evidence` branch. `main` carries the specification, general findings and roadmap only; this branch adds
the saves, derived configs, scripts, probes, accuracy analysis and tests that reproduce and challenge them.

**Contents**

1. [Where to find the facts](#where-to-find-the-facts)
2. [What the work covers](#what-the-work-covers)
3. [Quick start](#quick-start)
4. [Reproducing the investigations](#reproducing-the-investigations)
5. [Folder overview](#folder-overview)
6. [Data and licensing notes](#data-and-licensing-notes)

## Where to find the facts

| Question | Read |
| --- | --- |
| What must the format and the tools do? Requirements R1-R53, key catalog, conversion rules, acceptance examples | [`docs/spec/exchange-format-requirements.md`](docs/spec/exchange-format-requirements.md) |
| What did the investigations find (savegame, calculator, planner, accuracy figures)? | [`docs/insights.md`](docs/insights.md) |
| Where does each value live in the savegame? | [`docs/findings/savegame-structure.md`](docs/findings/savegame-structure.md) |
| How accurate is the derived good flow, and why? | [`docs/analysis/derived-trade-flow-accuracy/analysis.md`](docs/analysis/derived-trade-flow-accuracy/analysis.md) |
| How was the updated calculator config built, what did it change, what needs a human decision? | [`docs/findings/calculator-config-update.md`](docs/findings/calculator-config-update.md) |
| What is left to implement, per repo? | [`docs/roadmap.md`](docs/roadmap.md) |
| Which data files exist and where do they come from? | [`data/README.md`](data/README.md) |

## What the work covers

- A standalone exchange format (JSON plus JSON Schema) that any tool can write, with a minimal valid file of
  islands and building counts. Unknown fields, regions, buildings and effects are preserved by every tool, so
  calculator -> planner -> calculator loses nothing and future DLC content survives.
- Import and export in the planner (Taludas) and the calculator (Nico), and a savegame writer in the layout tool.
- A savegame-to-plan script that derives islands, building counts, patrons and devotion, fertilities, items per
  villa, range-derived effects on production buildings, harbours, map position, fleet, trade routes and disabled
  needs from an `.a8s` file.
- An updated calculator config for the sample game (`Marcia 69`) built from the savegame, with a change report.
- Measurements: how well a good flow derived from route configurations matches the trades the game recorded.

The planner-side items for review are listed in [`docs/roadmap.md`](docs/roadmap.md). Requirements R30, R40-R43,
R45, R47 and R52 touch planner code directly.

## Quick start

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer.

```
uv sync
uv run pytest -q                      # offline tests on the committed data
ANNO_PLANNER_REPO=../Anno-117-Planner uv run pytest -q   # adds the planner load/engine checks
```

Environment variables used by the tests and scripts:

| Variable | Meaning |
| --- | --- |
| `ANNO_PLANNER_REPO` | Path to the Taludas Planner checkout (plans are loaded with its `Plan` and `Engine`) |
| `ANNO_CALC_REPO` | Path to the anno-117-calculator checkout (game data in `js/params.js`, headless checks) |
| `ANNO_DECODED` | Folder with the decoded savegame XML (see below); needed by slow tests and by the extraction scripts |
| `ANNO_OUT` | Output folder of the generator scripts (default: `outputs/`) |

PowerShell: `$env:ANNO_PLANNER_REPO = "C:\dev\Anno-117-Planner"`.

## Reproducing the investigations

A savegame (`.a8s`) is an RDA archive. The decode chain is
`.a8s` -> `data.a7s` -> zlib -> FileDBReader XML (about 230 MB) -> three session blobs -> XML (50-120 MB each).
It needs [RdaConsole](https://github.com/anno-mods/RdaConsole) and
[FileDBReader](https://github.com/anno-mods/FileDBReader); the commands and the layout of the decoded folder are in
[`scripts/probes/README.md`](scripts/probes/README.md) and in
[`scripts/savegame_to_planner/README.md`](scripts/savegame_to_planner/README.md).

| Goal | Run |
| --- | --- |
| Derive a planner plan from a save | `scripts/savegame_to_planner/` (needs the Anno-117-Layout-Tool checkout, see `NOTE.md` there) |
| Rebuild the updated calculator config | `scripts/calculator_config/` (see its README for the run order) |
| Recompute the trade-flow accuracy | `docs/analysis/derived-trade-flow-accuracy/scripts/` (commands at the end of `analysis.md`) |
| Re-ask a question about the save format | `scripts/probes/` (exploratory; paths may need adjusting) |

## Folder overview

```
docs/spec/        requirements and key catalog (the contract to review)
docs/findings/    how the savegame is structured, how the calculator config was updated
docs/analysis/    derived trade-flow accuracy: document, scripts, result tables
docs/insights.md  measured facts and decisions, with pointers
docs/roadmap.md   remaining work per repo
data/raw/         saves (.a8s) and the original calculator config
data/processed/   updated calculator config, derived planner plans, reports
scripts/          savegame_to_planner, calculator_config, probes
tests/            pytest suite (offline, planner-dependent, slow/needs_save)
outputs/          generated files (empty in git)
```

## Data and licensing notes

- The saves and the calculator config are one player's game state (account folder GUID in their original path,
  island names, play history). Remove or replace them before publishing outside the review group.
- Game data, texts and icons are (c) Ubisoft. The scripts read them from local installs and caches; none are
  copied here except the small result tables.
- MIT for the code and documents written for this repo (see `LICENSE`). The saves and configs are excluded from that
  grant: they are one player's game state. The calculator is MIT; the planner and the layout tool carry their own
  licenses.
