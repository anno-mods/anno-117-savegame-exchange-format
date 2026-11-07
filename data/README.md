# Data

| Path | What it is | Origin |
| --- | --- | --- |
| `raw/saves/Marcia 69.a8s` | Savegame, SessionFileVersion 0x50, 22 player islands (Latium, Albion, Aegyptus), about 2 h of recorded trades | player's game folder, unchanged |
| `raw/saves/Autosave 3774.a8s` | Autosave, SessionFileVersion 0x21, 31 islands (Latium, Albion), hand-named islands (`CityName`) | player's game folder, unchanged |
| `raw/calculator_configs/Marcia 69.json` | anno-117-calculator storage dump for the same game, older than the save | calculator "Export config" |
| `processed/calculator_configs/Marcia 69 updated.json` | the dump with the savegame merged in (see `docs/findings/calculator-config-update.md`) | `scripts/calculator_config/` |
| `processed/calculator_configs/Marcia 69 updated.changes.{json,csv}` | every change with island, key, old and new value, source and category | same |
| `processed/planner_plans/marcia69.v5.plan.json` | planner plan derived from `Marcia 69.a8s`: harbours, map, fleet, routes, disabled needs, range effects | `scripts/savegame_to_planner/` |
| `processed/planner_plans/marcia69.v4.plan.json` | the same before harbours/fleet/routes/needs; used as input of the calculator config build | same |
| `processed/planner_plans/autosave3774.plan.json` | plan derived from `Autosave 3774.a8s` | same |
| `processed/reports/fx_report_v5.json` | decisions of the effect derivation (per building type: share in range, method, near ties) | same, `--report` |

Not in the repo (regenerate, hundreds of MB): the decoded savegame XML. See `scripts/probes/README.md` for the
decode commands and point `ANNO_DECODED` at the result.

The `.a8s` files and the calculator dump contain one player's game state (island names, build history). Do not
publish them without the owner's consent.
