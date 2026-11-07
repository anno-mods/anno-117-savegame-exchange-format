# Updated calculator config for Marcia 69

`data/processed/calculator_configs/Marcia 69 updated.json` is the original calculator storage dump
(`data/raw/calculator_configs/Marcia 69.json`) with the newer savegame merged in. The change report is next to it
(`.changes.json`, `.changes.csv`). The build scripts are in `scripts/calculator_config/`.

## Why

The calculator export is older than the savegame: residences, patrons, devotion and repeat counts differ, and the
Aegyptus trade routes and buffs were never entered. The calculator's import accepts only its own dump format, so the
update is written in that format.

## Merge rules

- Islands are matched by the game reference (session, island id, area index; 22 of 22). Names, order, notes, UI
  state, `calculatorSettings`, supplier choices, `fullyUtilizeConstructed` flags and planned counts are kept.
- Updated from the save: built counts (`<building>.buildings.constructed`), patron and devotion (no rounding),
  fertilities, item states (`<factory>[<item>].scaling` 0/1/2) and aqueduct/module flags and building effects from the
  range-derived applied effects, disabled needs, and the discoveries whose scale follows from research.
- Needs: a need that the save does not disable is on. DLC 3 needs on Latium and Albion islands were switched on
  (210 explicit `1` values). Toggles that stay off and look like deliberate choices are listed in the report as
  "needs, kept off" with a reason.
- Trade routes: the 40 existing entries stay first and unchanged. Flows derived from the 113 player routes are
  added (rule R37, `docs/spec/exchange-format-requirements.md`). Where a user entry already exists for an island and
  product, it wins and the derived alternative is reported. Routes with no pure source (all stops load and unload) take
  their roles from the signs of the recorded net amounts; routes without ships carry no flow.
- Pairs where the island produces the good itself follow R51: the local producer gets
  `<factoryGuid>.buildings.fullyUtilizeConstructed` = `"1"` in the island store, the largest supplier is the default
  supplier route (`isDefaultSupplier` true, `userSetAmount` 0) and further suppliers are ordinary routes at 0. No
  amount comes from the flow estimate. The mechanics (calculator `src/`):
  - A fully utilized factory runs at its built capacity: throughput is `max(throughputByOutput, constructed * boost *
    60 / cycleTime)` (`factories.ts` 124-134); `utilized = max(constructed, required)` (`util.ts` 479).
  - Every available factory and every import route is a supplier of the product (`production.ts` 198-225), so a
    non-default fully utilized factory adds its built capacity to the supply.
  - The default supplier receives `max(0, demand - supply of all non-default suppliers)` (`production.ts` 286-294);
    a route supplies `max(userSetAmount, amount)` (`trade.ts` 135). The import is therefore the remaining demand.
  - A trade-route default is not written to `<product>.defaultSupplier.type/id` (`world.ts` 1110-1128); the stored
    type stays `factory` and the trade manager overrides it on load (`trade.ts` 316). The keys are not touched.
  - When the built capacity exceeds the demand, the import drops to 0 and the surplus counts as excess production.

## Result (latest build)

928 changes plus unchanged-reference rows (1156 report rows). Per category: trade routes 329 added entries,
fertility 147, building effects 93, items 31, needs 218, devotion 16, aqueduct 12, modules 8, buildings 37,
local producers 29, patron 5, construction materials 2, discoveries 1 (Beneath Bedrock 7 -> 8). 33 local producers are
fully utilized (29 keys written, 4 construction-material factories are on by default). 369 trade entries in total,
349 defaults. The file loads in the calculator's prebuilt bundle in headless Chromium without Knockout binding errors
(369 routes load). Computed values, original config -> updated config:

| Island | Factories required | Residents |
|---|---|---|
| Cinis | 575 -> 610 | 60,719 -> 62,918 |
| Listening Weasel Nome | 62 -> 157 | 2,485 -> 3,043 |
| Juliana | 243 -> 232 | 15,505 -> 16,301 |
| Argantum | 45.0 -> 44.8 | 496 |
| Nusquam | 570 -> 239 | 34,232 -> 36,132 |

On Listening Weasel Nome (Gold, factory 152358, 4 built) the local output is 4.8 t/min against a demand of 1.73, so
the import from Cinis is 0. On Cinis Sandals (14 built) the factory delivers 8.4 and the import 1.17 t/min.

## What needs a human decision

1. Fertility: 143 new `0` entries and 4 `1` -> `0`. They depend on the savegame script's idea of an island's natural
   fertilities.
2. Building effects: slots on went from 7 to 94, mostly the Thoth library (street distance, validated on one in-game
   observation) and the Hippodrome chariot effect, both by the majority rule.
3. Needs kept off (listed in the report), for example 15 needs the player switched off while the good is available.
4. Four plan items are not in the calculator data (51607, 51635, 44084, 51639) and were skipped.
5. Cinis Resin (31695) stores a `null` default supplier although the save has a route and a local producer. The
   `null` is kept as a user choice: no import and no `fullyUtilizeConstructed` flag were added. Juliana Amphorae
   (31700) has a passive-trade default; it is kept and the derived Argantum route is only listed as an alternative.
   A local producer whose `fullyUtilizeConstructed` is already set to 0 by the user would be kept the same way (none
   in this config).
6. Where the built capacity of a local producer exceeds the island's demand (Listening Weasel Nome Gold), the import
   drops to 0; the route stays in the file.
7. Routes with only non-player stations (61, 84, 115) have no flow; routes 9, 46, 95 lose their non-player legs;
   route 107 has no ships and carries no flow.
8. Wonder effects (43620 Vervactor's Plough, 50262 Arboreal Rhizome, 183157 Open Sesame) are unchanged. The planner
   derives wonders from patron devotion; the game rule is the sum over islands.

## Rebuild

Needs the decoded `Marcia 69` data (`ANNO_DECODED`), the calculator checkout (`ANNO_CALC_REPO`, for `js/params.js`)
and the planner plan derived from the save. See `scripts/calculator_config/README.md` for the order. Rerun after the
plan changes: the script reads the plan's disabled needs, items and effects.
