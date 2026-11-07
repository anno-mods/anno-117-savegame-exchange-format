# Scripts for the derived trade flow accuracy analysis

All scripts are read-only on the savegame. They are plain Python 3.11 and import the Planner's game data
(`paxplanner.model.gamedata`) to print English names, so run them with the Planner's interpreter from the repo root
(`uv run python docs/analysis/derived-trade-flow-accuracy/scripts/<script>.py ...`).

Two folders are passed as arguments or environment variables:

| Folder | Argument | Environment variable | Content |
|---|---|---|---|
| decoded save | `--decoded` | `ANNO_DECODED` | `data_raw.xml`, `session_0.xml`, `session_1.xml`, `session_2.xml` (decoded XML, about 230 MB + 50-120 MB each) |
| work | `--work` | `ANNO_TRADE_WORK` | small JSON tables written by `extract_trade.py` (keep it outside the repo) |

Result tables go to `../results/` (compact CSV that `analysis.md` cites).

## Decoding the save (once)

The steps and tools are those of `tools/savegame_to_planner/README.md` in the layout tool repo:

1. `RdaConsole extract` unpacks the `.a8s` archive; `data.a7s` is zlib compressed FileDB.
2. Decompress it (zlib) to `data_raw.bin` and run `FileDBReader decompress -f data_raw.bin -y`; this writes `data_raw.xml`.
3. In `data_raw.xml`, every `MetaGameManager/GameSessions/None/SessionData/BinaryData` value is a hex encoded FileDB
   blob (one per session, in file order: Latium 3245, Albion 6627, Aegyptus 149679). Write each as `session_N.bin` and
   run `FileDBReader decompress -f session_N.bin -y` to get `session_N.xml`.

The layout tool's `savegame_to_planner.py --work-dir DIR` leaves the decoded XML in `DIR`; point `--decoded` there.
The analysis used `Marcia 69.a8s` (`SessionFileVersion` 0x50).

## Order and purpose

| Order | Script | Input | Output | What it does |
|---|---|---|---|---|
| 1 | `extract_trade.py` | decoded XML | `<work>/*.json` | routes (stations, cargo slots), recorded visits, island minimum stock, island sessions, ship objects |
| 2 | `verify_roles.py` | work | `results/role_vs_sign.csv`, `results/slot_amounts.csv` | entry counts, window, sign check of source/sink/relay roles, conservation, missing zero nets, slots with Amount != 50 |
| 3 | `constellations.py` | work | `results/constellations.csv` | classes of routes with counts and one example each |
| 4 | `evaluate_split.py` | work | `results/split_cases.csv` | accuracy of weight rule, equal split, cascade and calculator style against recorded shares (tests A, B, C) |
| 5 | `minstock_effect.py` | work | `results/minstock_effect.csv` | delivered tons per visit with and without an island minimum stock level; the Dates stops |
| 6 | `ship_link.py` | work | `results/ship_types.csv` | route to ship link in both directions, ships per route, ship types |
| any | `route_detail.py ROUTE_ID...` | work | stdout | one route: stations, slot totals, min stock, visits, net tons, visit sequence |

Modules: `common.py` (paths, tables, `roles`, `measured`, `total_variation`) and `xmlstream.py` (streaming reader for
the one-tag-per-line XML). `PLAYER = 41` in `common.py` is the human player's participant id in Marcia 69; change it
for another save.

## Example run (PowerShell)

```
$env:ANNO_DECODED = "D:\work\marcia69_decoded"
$env:ANNO_TRADE_WORK = "D:\work\marcia69_trade"
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/extract_trade.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/verify_roles.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/constellations.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/evaluate_split.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/minstock_effect.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/ship_link.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/route_detail.py 151 72 182 --product Dates
```
