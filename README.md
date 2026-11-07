# Anno 117 savegame exchange format

A tool-neutral exchange format between the **Taludas Planner**, the **anno-117-calculator** and tools that read
Anno 117 savegames (for example the Anno-117-Layout-Tool). This repo holds the requirements, the findings behind
them and the remaining work, so the planner side can be reviewed and implemented.

Status: requirements are settled, the format is not implemented yet. The key catalog is a first draft; names are
working names.

**Contents**

1. [Where to find the facts](#where-to-find-the-facts)
2. [What the work covers](#what-the-work-covers)
3. [Branches](#branches)
4. [Folder overview](#folder-overview)
5. [Licensing](#licensing)

## Where to find the facts

| Question | Read |
| --- | --- |
| What must the format and the tools do? Requirements R1-R52, key catalog, conversion rules, acceptance examples | [`docs/spec/exchange-format-requirements.md`](docs/spec/exchange-format-requirements.md) |
| What did the investigations find (savegame, calculator, planner, accuracy figures)? | [`docs/insights.md`](docs/insights.md) |
| Where does each value live in the savegame? | [`docs/findings/savegame-structure.md`](docs/findings/savegame-structure.md) |
| What is left to implement, per repo? | [`docs/roadmap.md`](docs/roadmap.md) |

Documents refer to material that lives on the `evidence` branch (saves, derived configs, scripts, tests and the
trade-flow accuracy analysis, for example `docs/analysis/` and `docs/findings/calculator-config-update.md`). Those
paths exist only there.

## What the work covers

- A standalone exchange format (JSON plus JSON Schema) that any tool can write, with a minimal valid file of
  islands and building counts. Unknown fields, regions, buildings and effects are preserved by every tool, so
  calculator -> planner -> calculator loses nothing and future DLC content survives.
- Import and export in the planner (Taludas) and the calculator (Nico), and a savegame writer in the layout tool.
- Derivation from an `.a8s` savegame of islands, building counts, patrons and devotion, fertilities, items per
  villa, range-derived effects on production buildings, harbours, map position, fleet, trade routes and disabled
  needs.
- A measured answer to how well a good flow derived from route configurations matches the recorded trades.

The planner-side items are in [`docs/roadmap.md`](docs/roadmap.md). Requirements R30, R40-R43, R45, R47 and R52
touch planner code directly.

## Branches

| Branch | Content |
| --- | --- |
| `main` | structure, specification, general findings and roadmap |
| `evidence` | everything needed to reproduce and challenge the findings: the saves (binary), the original and updated calculator configs, derived planner plans, the cleaned scripts, probes, the trade-flow accuracy analysis, the calculator-config build notes, and the pytest suite |

`git switch evidence` for the reproducible part; its README has the quick start, the environment variables
(`ANNO_PLANNER_REPO`, `ANNO_CALC_REPO`, `ANNO_DECODED`, `ANNO_OUT`) and the decode procedure.

## Folder overview

```
docs/spec/        requirements and key catalog (the contract to review)
docs/findings/    savegame structure
docs/insights.md  measured facts and decisions
docs/roadmap.md   remaining work per repo
data/ scripts/ tests/ outputs/   placeholders on main, filled on `evidence`
```

## Licensing

MIT, see [`LICENSE`](LICENSE). It covers the documents and code written for this repo. Game data, texts and icons
are (c) Ubisoft. The saves and configs on the `evidence` branch are one player's game state and are not part of the
MIT grant. The calculator is MIT; the planner and the layout tool carry their own licenses.
