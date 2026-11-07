# Exploratory probes

Throw-away scripts that produced the findings behind the exchange format. They are kept as they were written, to make
the investigations reproducible, not as maintained tools: no tests, little error handling, output goes to stdout.
`ruff` reports findings for most of them (star imports, unused imports); they are not part of the lint gate.

The only edit made for this repository: absolute paths of the author's machine were replaced.

- `_SCRATCH` / `SCRATCH` = environment variable `ANNO_SCRATCH` (default: current folder). It is the working folder that
  holds the decoded saves as `x/` (Marcia 69: `data_raw.xml`, `session_0..2.xml`), `auto3774/` (Autosave 3774) and
  the intermediate files named below (`x/extract.json`, `x/lt_parse.pkl`, `fx_report.json`, `marcia69.v4.plan.json`).
- `_CONFIG` = `data/raw/calculator_configs/Marcia 69.json` of this repository.
- `C:\dev\Anno-117-Layout-Tool`, `C:\dev\Anno-117-Planner`, `C:\dev\FileDBReader\...` and `C:\dev\asset-extractor\...`
  are left as written (edit them to your checkout locations). Scripts using `from tree import ...` need
  `scripts/probes/savegame` on `PYTHONPATH`.

## Decode procedure (savegame to XML)

A savegame (`.a8s`) is an RDA archive; `data.a7s` inside is zlib-compressed FileDB. Three steps give the XML the probes
read (needs RdaConsole and FileDBReader, .NET 6+; see `scripts/savegame_to_planner/NOTE.md` for tool lookup):

```
RdaConsole extract -f "data/raw/saves/Marcia 69.a8s" -o outputs/decoded/outer        # -> outer/data.a7s (+ header, meta)
python scripts/probes/savegame/decode.py      # edit S and FDB at its top; it does the following:
#   1. zlib.decompress(outer/data.a7s) -> data_raw.bin
#   2. FileDBReader decompress -f data_raw.bin -y -> data_raw.xml            (outer XML, one tag or value per line)
#   3. every <GameSessions>/.../<BinaryData>hex</BinaryData> -> session_0.bin, session_1.bin, session_2.bin
#      and FileDBReader decompress on each -> session_0.xml ... session_2.xml
```

The sessions are in file order Latium (3245), Albion (6627), Aegyptus (149679). Without hand work the same result comes
from `python savegame_to_planner.py <save> --work-dir outputs/decoded` of the layout repo (add `--reuse` to skip decoding
the second time); `scripts/calculator_config/extract_save.py` reads that folder via `ANNO_DECODED`. Decoded Marcia 69
is about 230 MB outer XML plus 50-120 MB per session, Autosave 3774 about 390 MB plus 380 MB; do not commit them.

## savegame/ (decoding, game data lookups, derivation rules for the plan)

Decoding and tree browsing
- `decode.py`: the three decode steps above for Marcia 69.
- `tree.py`: streaming FileDB-XML reader (`stream(file, want)` yields subtrees, `show` prints them); imported by the peek and research scripts.
- `outline.py FILE DEPTH [LINES]`: tag outline of a decoded XML up to a depth, repeated siblings collapsed.
- `paths.py FILE DEPTH [PATTERN]`: counts tag paths with an example, to find where a value lives.
- `sect.py FILE TAG [LINES] [N]`: prints the first (or N-th) `<TAG>` section verbatim.
- `peek.py`: which AreaInfo entries exist, who owns them, name fields, first AreaManager children (session 0).
- `peek2.py SESSION AREA MANAGER`: children of one AreaManager sub-manager.
- `peek3.py TAG DEPTH`: subtree of a tag in the outer XML.
- `peek4.py`: tag histogram of one AreaObjectManager (which components buildings carry).
- `peek5.py SESSION AREA COMPONENT`: raw object records that carry one component.
- `peek6.py TAG`: subtree of a tag at any depth in the outer XML.
- `extract.py`: reduces the session XML to `x/extract.json` (areas, counts, fertilities, devotion, paused goods, sockets); input of `build_plan.py`.
- `lt_parse.py`: runs the layout tool's `savegame_parser` on each session, writes `x/lt_parse.pkl` (island templates, sizes); input of `build_plan.py`.
- `load_all.py`: reads the three session XMLs with the `savegame_to_planner` reader into `x/areas_all.pkl` (list of area lists per session).
- `build_plan.py`: first version of the plan builder (extract.json + lt_parse.pkl to a Planner plan); superseded by `savegame_to_planner.py`.

Game data lookups (Planner `GameData`)
- `gd_probe.py`, `gd_probe2.py`: session/region ids, residence building fields, fertility list, religion balancing.
- `gd3.py`: item, effect (51637, 99011), factory and farm records as the planner stores them.
- `gd5.py`: which effects are area/building boosts, with targets (reads `fx_report.json`).
- `gd6.py`: need records, population level 1498, trading post and harbour buildings.
- `gd7.py`: `gd.ships` structure: harbours, harbour items, ship records.
- `stats.py`: how many residences/items map to planner fields, calculator-only keys (compares with the calculator config).
- `why.py`: why a given item/effect was or was not applied to a factory type (allocation, scope, range).

Names, maps, ownership
- `names_probe.py`: island name decode: `CityNameGuid` (signed 64 bit) against `texts_english.xml` LineIds; 22 of 22 match the calculator names.
- `names3774.py`: island names in Autosave 3774 (SessionFileVersion 0x21): all 31 islands carry `CityName` (UTF-16), no `CityNameGuid`.
- `map1.py`: island position tables of the Planner map profiles versus the session `MapTemplate`.
- `map2.py`: do real Latium/Albion island positions match a Planner profile (they do not; campaign template); Aegyptus names versus slots.
- `map3.py`: island id of the area key is the 1-based index into the template element list: centroid-in-box check.

Bans, fleet, irrigation, ranges
- `ban1.py`: `AreaResidenceConsumptionManager/ProductData` pause flags (disabled needs); compares with the calculator's unchecked needs.
- `ban2.py`: banned needs of the save versus unchecked toggles of the calculator, per island (match, save-only, calculator-only).
- `fleet1.py`: ship effects (optional, no source) in the game data; which ones the human has active (`ActiveEffectRewards3`).
- `fleet2.py`: per-session `SessionEffectManager` effect lists, outer-XML effect holders.
- `fleet3.py`: searches the outer XML for ship effect GUIDs; finds none active in Marcia 69.
- `harb1.py`: trading posts and piers per island (counts per harbour GUID), basis of `harbour` / `piers`.
- `irr.py`: tree of `AreaIrrigationManager` and which farms sit near it.
- `irr2.py`: grep of the planner game data for "irrigation" in buffs, effects, techs, buildings.
- `irr3.py`: irrigation-related buffs, quests, building templates, Egyptian farm types; conclusion: no per-farm irrigation state to import.
- `scc.py`: `StreetConnectionCache` structure; library 152071 lists connected objects.
- `scc2.py`: weighted walking cost of cache members versus non-members (production buildings).
- `scc3.py`: cost metrics compared (hop count, walked length) for members and non-members.
- `scc4.py`: touch distance and sign sweep: false positives/negatives against the cache (basis of the street rule).
- `star.py`: Star-of-the-Nile Nome library effect: targets, source tiles, reached tiles, unreached buildings.
- `star2.py`: distance of buildings to the nearest road tile and angle, counts per touch threshold.
- `star3.py`: distance from a road tile to the oriented footprint of a building (rotation sign, touch offset); tests which footprint model reproduces the observed reach.
- `street1.py`: tree of `AreaStreetManager` in session 2.
- `street2.py`: road edge GUIDs (dirt, paved, marble, bridges), edge lengths in half tiles, coordinate ranges of roads and objects.
- `street3.py`: road tile points and object list; histogram of tile conversion.
- `street_an.py`: street-scope effect decisions per island from the report (affected/total, circle fallback).

## research_save/ (what the save records: items, effects, storage, trade; scripts use `tree.stream`)

- `ai.py`: AreaInfo children of one area.
- `any.py FILE TAG PATHLEN DEPTH MAXKIDS`, `outer.py TAG DEPTH MAXKIDS FILE` (under `MetaGameManager`), `obj.py KEY OBJECTID FILE DEPTH` (one object record),
  `sh.py KEY SUB DEPTH MAXKIDS FILE` (one sub-manager of `AreaManager_<KEY>`): tree dumps of single nodes.
- `bc.py`: item socket conditions (`cond`) and boost flag in `ItemMap`; counts boosted items without condition.
- `boost.json`: output of the boost survey (item to boost state), read by later scripts.
- `comp.py`, `comp2.py`: object count and component tags per building type; one object record in full.
- `ef2.py`, `eff.py`, `le.py`: `AreaEffectManager/Effects` records: effect GUID, scope id, source object, distance, end time, owner.
- `etag.py`: tag counts under one effect node. `ib.py`: searches `data_raw.xml` for hex-encoded `ItemBoost_...` strings and prints their paths. `ex.py`: examples per building type with position, direction, sockets, items.
- `hist.py`: storage history snapshots (`AreaEconomy` history) per island; writes `hist.json` (not shipped, 0.8 MB).
- `im.py`: item and effect map tags per session. `me.py`: `MetaEffectManager` items with scale.
- `lpt.py`, `st.py`, `st2.py`: storage trends (`StorageTrends`, `LastPointTime`) versus history snapshots.
- `pt.py`: `PassiveTrade` history aggregates (visit entries, time range). `tr.py`: trade routes of the player: owner counts, ships, stations, goods.
- `tmp.json` was dropped (empty). Large generated `hist.json` and the `trade/` work folders are not shipped; the trade tables
  are produced by `docs/analysis/derived-trade-flow-accuracy/scripts/extract_trade.py`.

## research_discoveries/ (techs, discoveries, effects of the calculator versus the planner)

- `analyze.js`: techs and effects of the calculator `params`, all sessions; reads the calculator config (`_CONFIG`).
- `ab.js`: area buffs and fertilities in `params`, effects that add fertility; reads the config.
- `x.js`, `y.js`: effect and buff details for given GUIDs, patron local effects.
- `u.py`: calculator `globalEffects` scaling against the planner's discovery scaling for each tech; prints OK or the mismatch.
- `v.py`: lists effect GUIDs missing from the planner's effects. `w.py`: calculator techs versus the planner plan's techs and global effects.
- `z.py`: planner tech records (e.g. 37870), religion balancing.

## calculator_config/ (probes of the calculator-config pipeline)

These were written against the earlier `common.py` of the pipeline (star import providing `json`, `re`, `collections`, `SP`,
`load`, `island_stores`, `area_key`; `SP` = working folder). The maintained pipeline is in `scripts/calculator_config/`;
to run a probe, copy it there, replace `from common import *` with explicit imports and the `SP` paths with `OUT`.

- `explore1.py`: area table of the save versus plan islands and config island stores (matching by area key).
- `chk1.py`: trade pairs derived by `trade_derive` versus the plan's `supplied_by` (only-mine / only-plan).
- `chk2.py`: diagnostics of routes without flows or with zero ships.
- `chk3.py`: counts of the trade routes in a config (by source, target, default flag, amount > 0).
- `chk4.py`: line endings, non-ASCII characters and JSON round trip of the config file (byte-exact rewrite check).
- `inspect1.py`: change report by category with samples (fertility etc.).
- `inspect2.py`: effects with `Effect.applyBuffs` semantics (per-target keys), library effect 153868 sources, slot keys.
- `inspect3.py`: trade section of the report: approximations, agreement status, skipped.
- `inspect4.py`: building changes, residence versus production, flow pairs and route status.
- `inspect5.py`: ordinary routes added with their amount basis (measured, capacity, placeholder).
- `look1.py`: techs in `params` against researched techs; meta effects. `look2.py`: planner data files `volcano.json`, `seasons.json`, `techs.json` (volcano levels, season unlocks).
- `look3.py`: tech unlock chains in the planner's `techs.json` for the volcano and season effects, with the plan's researched techs.
- `nosrc.py`: goods without a pure source on a route: signed nets from recorded visits per island.
- `route_look.py`, `route_look2.py`: one route in full: stations, slots (L load / U unload with amounts), visits per island.
- `vis_look.py`: structure of `visits.json` (keys, traders, time range and unit, rows per island and product).
- `trade_block.py`, `splice.py`: the fragment that is the trade-route section of `build_config.py` and the one-off script that pasted
  it into `build_config.py`. The section now lives inline in `scripts/calculator_config/build_config.py`; the fragment is not runnable.
