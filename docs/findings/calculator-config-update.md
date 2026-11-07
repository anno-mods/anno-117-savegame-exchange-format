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
  product, it wins and the derived alternative is reported. Pairs where the island produces the good itself were
  first skipped and then added as ordinary routes with a minimum amount above zero (measured rate from recorded
  visits, else capacity rate). Requirement R51/R52 prefer the other approach for local producers (set the local
  producer fully utilized and import the rest); the config has not been reworked to it yet.

## Result (latest build)

901 changes plus unchanged-reference rows. Per category: trade routes 331 added entries, fertility 147,
building effects 93, items 31, needs 218, devotion 16, aqueduct 12, modules 8, buildings 37, patron 5, construction
materials 2, discoveries 1 (Beneath Bedrock 7 -> 8). 371 trade entries in total, 316 defaults. The file loads in the
calculator's prebuilt bundle in headless Chromium without Knockout binding errors (371 routes load). Cinis factories
required 575 -> 637, Nusquam 570 -> 226, Cinis residents 60,719 -> 62,918.

## What needs a human decision

1. Fertility: 143 new `0` entries and 4 `1` -> `0`. They depend on the savegame script's idea of an island's natural
   fertilities.
2. Building effects: slots on went from 7 to 94, mostly the Thoth library (street distance, validated on one in-game
   observation) and the Hippodrome chariot effect, both by the majority rule.
3. Needs kept off (listed in the report), for example 15 needs the player switched off while the good is available.
4. Four plan items are not in the calculator data (51607, 51635, 44084, 51639) and were skipped.
5. Cinis Resin (31695) stores a `null` default supplier although the save has a route.
6. Routes with only non-player stations (61, 84, 115) have no flow; routes 9, 46, 95 lose their non-player legs.
7. Wonder effects (43620 Vervactor's Plough, 50262 Arboreal Rhizome, 183157 Open Sesame) are unchanged. The planner
   derives wonders from patron devotion; the game rule is the sum over islands.

## Rebuild

Needs the decoded `Marcia 69` data (`ANNO_DECODED`), the calculator checkout (`ANNO_CALC_REPO`, for `js/params.js`)
and the planner plan derived from the save. See `scripts/calculator_config/README.md` for the order. Rerun after the
plan changes: the script reads the plan's disabled needs, items and effects.
