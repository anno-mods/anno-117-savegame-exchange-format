# Calculator config update pipeline

Merges the state of a savegame into a calculator config dump (`Marcia 69.json`, the calculator's `localStorage`
export) and reports every change. Result for Marcia 69: `data/processed/calculator_configs/Marcia 69 updated.json`
with `.changes.json` and `.changes.csv` (1156 report rows, 928 changes, 329 added trade routes, 369 in total).

All Python files take their paths from `common.py`. Environment variables (defaults relative to the repository root):

| Variable | Meaning | Default |
|---|---|---|
| `ANNO_DECODED` | decoded save: `data_raw.xml`, `session_0..2.xml` | `outputs/decoded` |
| `ANNO_CALC_REPO` | anno-117-calculator checkout (`js/params.js`) | `../anno-117-calculator` |
| `ANNO_PLANNER_REPO` | Anno-117-Planner checkout (only needed to rebuild the plan, not by these scripts) | `../Anno-117-Planner` |
| `ANNO_LAYOUT_REPO` | Anno-117-Layout-Tool checkout (provides `savegame_to_planner`) | `../Anno-117-Layout-Tool` |
| `ANNO_OUT` | working and output folder | `outputs` |
| `ANNO_TRADE_VISITS` | `visits.json` of the trade extraction | `data/processed/reports/trade_visits.json` |

## Inputs

| File | Source |
|---|---|
| `data/raw/calculator_configs/Marcia 69.json` | original config exported from the calculator |
| `data/processed/planner_plans/marcia69.v5.plan.json` | plan written by `savegame_to_planner.py` (street rule validated, trade derived) |
| `data/processed/reports/fx_report_v5.json` | `--report` output of the same run (trade imports with weights) |
| `data/processed/reports/trade_visits.json` | recorded visits per island and route, from `docs/analysis/derived-trade-flow-accuracy/scripts/extract_trade.py` (`<work>/visits.json`) |
| `ANNO_OUT/params.json` | calculator game data, written by `dump_params.js` |
| `ANNO_OUT/save_data.pkl` | save tables, written by `extract_save.py` from `ANNO_DECODED` |

Decoding the save into `ANNO_DECODED` is described in `scripts/probes/README.md` (RdaConsole, zlib, FileDBReader) or done by
`savegame_to_planner.py --work-dir`.

## Run order

```
node   scripts/calculator_config/dump_params.js          # -> outputs/params.json
python scripts/calculator_config/extract_save.py         # -> outputs/save_data.pkl   (reads ANNO_DECODED, needs the layout repo)
python scripts/calculator_config/build_config.py         # -> outputs/Marcia 69 updated.json, .changes.json, .changes.csv
python scripts/calculator_config/cm_overview.py          # adds construction_materials_overview to the .changes.json
python scripts/calculator_config/validate_out.py [dir]   # PASS/FAIL checks; dir = folder with the three files (default outputs)
# optional
python scripts/calculator_config/needs_an.py             # -> outputs/needs_rows.json (why needs stay off)
node   scripts/calculator_config/run_calc.js OLD.json NEW.json outputs/runtime.json   # load both configs in the calculator (Playwright)
python scripts/calculator_config/cmp_runtime.py          # table old>new of calculator values per island
```

Without a decoded save, `build_config.py` still needs `save_data.pkl`; it is the only input not in the repository
(`extract_save.py` produces it, about 250 KB).

## Scripts

- `common.py`: paths, `load()` (the five inputs), `island_stores()`, `area_key()` (areaIndex << 13 | islandID << 6 | region code 1/3/4).
- `dump_params.js`: evaluates the calculator's `js/params.js` and writes `params.json` (game data: factories, needs, items, effects, techs ...).
- `extract_save.py`: reads the decoded save with the readers of `savegame_to_planner.py`; keeps empire routes and the per-area tables
  (counts, fertilities, patron, devotion, visits), drops placements and roads.
- `trade_derive.py`: `derive()` re-derives per-route supplier weights (same rule as the planner script) with route diagnostics. Run as a script it compares with `fx_report_v5.json`.
- `build_config.py`: the update itself, per island: `buildings.constructed` (construction-material factories are updated too, their
  `fullyUtilizeConstructed` is kept), patron, devotion, fertilities, items and building effects as `scaling` slots, aqueduct and module
  switches, banned needs; globally: discoveries (researched techs, repeat counts), volcano and Nile season effects; trade routes: derived
  suppliers added (default supplier plus ordinary routes), existing user routes kept; for a good the island produces itself the local
  producer is set fully utilized and the largest supplier is the default import route (R51, no amounts); every change goes to the
  report with source and note.
- `cm_overview.py`: per-island table of construction-material factories (old versus new count) appended to the report.
- `validate_out.py`: keys and order identical to the original, selected keys byte-identical, every new key fits a persist pattern with a GUID known to the
  calculator data, per-island change counts equal the report, trade-route invariants (no duplicates, one default supplier, no cycle), CSV rows equal report rows.
- `needs_an.py`: analysis of the needs that are off in the original config (DLC, public building, no producer, user choice).
- `run_calc.js`, `cmp_runtime.py`: loads old and new config into the calculator (static files of `ANNO_CALC_REPO`, port `ANNO_CALC_PORT`, default 8217)
  and compares computed values (required factories, residents, items on, trade in/out ...). 404 console messages for missing resources are expected.

`trade_block.py` and `splice.py` (a fragment of the trade section and the one-off script that pasted it into `build_config.py`) are in
`scripts/probes/calculator_config/`; the section lives inline in `build_config.py`.

## Reproduction

With the decoded Marcia 69 data, `dump_params.js`, `extract_save.py`, `build_config.py` and `cm_overview.py` reproduce
the three files in `data/processed/calculator_configs/` byte for byte (the report's `output` field holds the file name, not a path).
`validate_out.py` prints ALL OK.
