# Insights

Measured facts and the decisions they led to. All numbers come from `Marcia 69` (22 islands, savegame 0x50) unless
stated; the calculator config for it is older than the save. Requirement IDs refer to
`docs/spec/exchange-format-requirements.md`.

## The three models

| | Calculator | Planner | Savegame |
| --- | --- | --- | --- |
| State | localStorage dump; island stores are JSON strings inside the dump | `Plan` JSON; `Plan.from_json` drops unknown fields | building instances with positions, items, patrons, research, routes |
| Residences | built counts per residence building GUID | counts per population level | residence buildings with resident counts |
| Suppliers | per product a default supplier (`factory`, `extra_good`, `passive_trade`, null) plus `tradeRoutes` (product, from, to, `userSetAmount`, `isDefaultSupplier`); several suppliers via a minimum amount > 0 plus one default | `supplied_by`: product -> ordered supplier -> t/min, -1 = rest; governor harbours; one producer per product | route stations and cargo slots, recorded visits |
| Discoveries | 16 effect-bearing techs as global effect scales; no research tree | tech list, repeat counts, queue | `TechCompleted`, `TechRepeatables` |
| Names | island name is the store key | name + id | `CityName` or `CityNameGuid` |

Identity that all three share: the game island reference (session GUID, island id, area index).

## Savegame facts

- Area key decode matches the calculator's `gameConnector` ids on 22 of 22 islands (`docs/findings/savegame-structure.md`).
- Hand-renamed islands carry `CityName` (UTF-16 hex); default-named islands carry `CityNameGuid`, a LineId in the
  game texts. In `Marcia 69` 22 of 22 resolved names match the calculator's `islandNames`; in `Autosave 3774` all
  31 player islands carry `CityName` (no calculator config exists for that save to compare).
- The extraction works unchanged on SessionFileVersion 0x50 and 0x21.
- Harbours: posts and piers are ordinary objects. Map: Latium and Albion are campaign maps without a planner template
  match (0 of 22 positions), so the planner's `map_slot` stays unset there; Aegyptus slots come from map file names.

## Range-derived effects (R26, R36)

- Circle effects: centre to centre, `distance <= effect radius`; villa 36, officium 24 equal the game data.
- Rule: an effect applies to a production building type when strictly more than half of its buildings are reached.
  Marcia 69: 367 circle decisions, 153 applied, 56 near ties (9 exact halves). Exactly half is not applied.
- Street distance (library 153868 and similar): walked length along the road graph, footprint touch 1.0, diagonal
  1.414, paved/marble 1/1.5, start at 0. The layout tool's one-hop-per-tile model did not reproduce the player's
  observation that the library on Star-of-the-Nile Nome reaches every production building except one vintner (the new
  rule: 48 of 49). 175 street decisions, 70 applied. Validated on one island; bridge/walkway costs untested.
- The calculator export gives only weak validation: items 78 matched, 16 calculator-only, 107 save-only (mostly
  Aegyptus, not entered yet).

## Trade flow accuracy (R32, R37, R51; full analysis in `docs/analysis/`)

- Source/sink roles from slot modes match the recorded flow sign in 293 of 293 pairs.
- Shares are estimates: split among receivers, weight rule (visits x unload amount) mean TV 0.23 against 0.39 for an
  equal split (52 cases). Several suppliers for one island and good: weight 0.21, equal 0.31, calculator style
  (fixed amounts + default supplier) 0.18 with the largest supplier as default, 0.03 with hindsight (12 cases).
  On the planner form of the sample game the weight split was no better than equal (0.27, 8 cases).
- Stops are demand limited and later stops get leftover cargo, so amounts follow demand, not capacity.
- Decision: writers record facts and topology; readers compute amounts from their own demand and local supply
  (R51). The calculator sets a local producer fully utilized and imports the rest.
- Minimum stock is an island attribute per good, not a route property; it reserves stock for loading stops only.

## Calculator semantics worth knowing

- `fullyUtilizeConstructed`: throughput is at least `constructed x boost x 60 / cycle`; always on for
  construction-material factories (stored only when it changes, so the key is absent in the sample config).
- Construction materials: the calculator's constructed count of a material's end factory equals the planner's
  end-building count in `materials` (R50). Sample: 4 sawmills on Cinis need 8 t/min Wood.
- Plan/Master view mode sets all global effects on, volcano effects to 5 and Nile flood on, so stored scales are
  partly an all-on default (R44).
- Area-buff keys (`51796`, `30467`, `38412`, `38411`) are dormant duplicates of discovery effects.
- Volcanic soil level: one level in the planner, the same scale on each unlocked volcano effect in the calculator.
- The planner unlocks a wonder when any single island reaches the devotion threshold; the game uses the sum over
  islands (R45).

## Engine impact in the planner (sample game)

Derived plan v5 against v4: total production buildings 1998.6 -> 1053.7, imports 397.6 -> 612.1 t/min, because routes
and disabled needs now enter the plan. Cinis 757.9 -> 495.5 buildings against 556 built factories. The routes model
matches the save's ship count on 7 of 20 pairs that have map positions and is within 1 on 14.

## Unresolved

See `docs/roadmap.md`. The main open item is the mapping of game routes to calculator routes beyond the reference
derivation (relays, order-dependent routes, the demand value used for "covers everything").
