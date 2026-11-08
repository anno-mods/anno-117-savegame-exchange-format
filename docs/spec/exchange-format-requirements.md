---
title: Anno 117 Exchange Format - Plan
type: feat
date: 2026-11-07
topic: calculator-exchange-format
artifact_contract: ce-unified-plan/v1
artifact_readiness: requirements-only
product_contract_source: ce-brainstorm
execution: code
---

# Anno 117 Exchange Format - Plan

## Goal Capsule

- **Objective:** A tool-neutral exchange format for Anno 117 plans, with import and export in the Taludas Planner (separate repo) and the anno-117-calculator (sibling repo, owned by Nico/DuxVitae), and a savegame writer in the Anno-117-Layout-Tool repo as the first third-party-style implementation.
- **Product authority:** Nico. This document holds the scope decisions of the brainstorm; the key catalog is the first draft of the format and is refined during planning.
- **Open blockers:** none. One question is deferred to planning: the details of mapping game routes to calculator routes (R37).

## Product Contract

### Summary

A standalone, documented exchange format with a JSON Schema, kept in its own repo and writable by any tool. The planner, the calculator and a savegame script (layout repo) implement it. A tool that only knows islands and building counts produces a valid file; every other field is optional. Each tool carries data it does not understand through untouched, so calculator -> planner -> calculator keeps notes and private settings. The file can also carry recorded history (storage, production) and live values.

### Problem Frame

The calculator keeps its state as a flat dump of browser storage. Its export (`exportConfig` in `anno-117-calculator/src/main.ts`) writes that dump, and its import wipes storage and loads the file. The planner has its own plan file (`Plan` in `paxplanner/model/project.py`). `Plan.from_json` rebuilds the plan from the fields it knows and drops the rest, and the planner has no notes. A user who plans in the calculator, continues in the planner and goes back loses every setting only one tool models.

The two tools overlap but differ. The calculator tracks built and planned counts per building GUID, per-product suppliers, notes and the game connector's island references. The planner tracks residences per population level, ship templates, sent passive trades, map positions and a research queue. A savegame holds yet another view: building instances with positions, socketed items, patrons, fertilities and research, and island names only as text ids or hand-typed names, but no planner or calculator settings. All three key their data by game GUIDs and can identify an island by the game's own reference (session, island id, area index), which makes a shared format feasible.

### Key Decisions

- **Neutral format over adapting to the calculator's storage dump.** The format uses the game's vocabulary and has its own repo, so third-party tools depend on a contract and not on either tool. Cost: work in four repos.
- **Smallest possible required core.** A valid file needs the format marker and version, a generator name and island ids. Everything else is optional, so a writer can emit what it knows.
- **Passthrough over skip-and-report.** A tool stores what it does not understand and writes it back on export. Cost: plan files hold data the tool does not interpret.
- **Edits to modelled data win over carried-through copies.**
- **Three placements.** Core fields are defined by the format. Core-optional fields are defined by the format and produced by only some tools, so other tools can implement features on them without a format change. Extension blocks (`ext.<generator>`) are tool-private and preserved verbatim; any tool may use one.
- **Unknown fields are preserved at every level.** Newer writers survive older readers.
- **The game's island reference is the preferred match key.** Island names are display text, not identity.
- **Absence means unknown.** A missing key says nothing; only an explicit value does. This holds for fertilities, residences and every other optional field.
- **Inputs are inputs; measurements are measurements.** Calculated values, recorded history and live values are informational. A tool compares or shows them and never turns them into plan inputs.
- **Old-format calculator configs are read by the calculator only.**
- **Per-level residences are the planner's export form.** The planner sums per-building residence counts into population levels on import, using the level each residence building belongs to in the game data, and exports per-level counts only. Per-building counts stay absent in its files, which the format reads as unknown.
- **The calculator reads and writes discoveries.** `research` carries researched discoveries and repeat counts, and the calculator derives the effect scales of ordinary discoveries from it instead of storing those scales. Some discoveries and settings need special treatment because the two tools model them differently. Known so far: Nile flood and obsidian gathering (linked to the volcanic soil level, which the calculator expresses with two scaling values where the planner has one level) are stored as specific effects in `effects.bySession`; Vercators plough is global, not per session, and is stored as a specific effect in `effects.global`, and the planner derives it from the global devotion. Where the planner has a checkbox or a derivation for one of them (volcano effects and level, season unlocks, devotion), the planner's setting carries it instead. A review of the planner's model against the calculator's configs lists every further case and the specification records each conversion.
- **Later game versions extend the format without changing it.** New regions, buildings, products, effects and discoveries arrive as identifiers the tool does not know. Tools keep them and write them back, and the schema defines no closed lists for them.
- **Calculated values are a small fixed set.** `computed` holds, per island, the residents per population level, the buildings required per factory type (unrounded) and the import amount per good in t/min. A difference counts when it exceeds 1 % of the value or 0.1 units, whichever is larger. A minor revision may extend the set.
- **History in version 1 holds the period snapshots.** Storage-trend buffers are written only by a writer that has verified their time axis. There is no companion file. A writer that finds a file too large drops whole series and never truncates one.
- **Recorded visits include other traders.** Each visit carries a trader id, and the planner and calculator read only the player's.
- **Station markers without a known meaning are kept, not interpreted.** `VanishGoods` and similar markers live in the writer's extension block on the station.
- **The calculator's shared `passiveTrade.userSetAmount` key stays in `ext.calculator`.** It is one key for all products in the current code and maps to nothing per product.
- **The specification repo is named `anno-117-exchange-format`.** Releases are tagged with the format version, and each other repo vendors a copy of the schema and the conformance fixtures at a tag and checks that the copy matches.

### Requirements

**Import and export in the Taludas Planner**

- R1. The planner offers Import and Export of the exchange format in its main menu next to the plan commands.
- R2. Import replaces the open plan after a confirmation that names what is replaced.
- R3. After import and export the planner shows a report: what could not be mapped, what was carried through and what was approximated.
- R4. A file that is not in the exchange format, or has a newer major version than the tool supports, is rejected with a message, and the open plan is unchanged.
- R30. The planner links plan islands to game islands by the game island reference. Linking by game island name stays as a fallback for islands without one. The link is part of the plan and travels with an export. Link modes other than one specific game island (automatic by name, whole session) stay in `ext.planner`.

**Import and export in the calculator**

- R5. The calculator exports and imports the exchange format next to its current config dump, which stays unchanged. Before replacing calculator state, import shows a confirmation that names the full replacement scope: island stores, calculator settings, trade data, and preserved exchange data. The existing config dump import and export remain unchanged.
- R6. The calculator reads its current config dump and writes the exchange format from it, so existing configs migrate through the calculator.
- R7. The calculator gives each island a stable opaque id on first export and keeps it, also when two islands share a name.

**Format, schema and third-party writability**

- R8. The format is a standalone specification with a JSON Schema and valid and invalid example files, kept in its own repo. The specification lists every key with its scope, type, writers, and whether it is core, core-optional or extension.
- R9. The file carries a format version with major and minor parts. Minor revisions only add optional fields. A major revision may change meaning.
- R18. A file is valid when it has the format marker, the format version, a generator name and island ids. A third-party tool that writes only islands with building counts produces a valid file.
- R19. Readers ignore unknown fields, unknown generators and newer minor versions. A missing optional field is never an error. The schema defines no closed lists for regions, building kinds, effect kinds, source kinds or DLC names; a value it does not list is valid.
- R10. Core and core-optional fields use game GUIDs as identifiers and use game vocabulary for names, not planner or calculator terms.
- R11. Tool-private data lives in `ext.<generator>` at document and island scope, where `<generator>` is any id a tool chooses.
- R12. The specification describes how a field moves from an extension block to core-optional and then to core in a later revision, including how an old file with the field in `ext` is read.
- R20. Both tools and the layout script pin a copy of the schema and run the same conformance fixtures: valid minimal file, file from an unknown generator, newer minor version, preserved unknown fields, preserved fields after island deletion and rename, identifiers of a later game version (unknown region, building, effect, product and discovery GUIDs) kept and written back in their original core locations, and a construction-material island (4 sawmills on Cinis requiring 8 t/min of wood).

**Identity and provenance**

- R21. Each island has an opaque id, unique in the file. The optional game island reference holds the game's session GUID, island id and area index, plus the derived area key, and is the preferred match key when tools compare files. The specification documents the area key: the area index shifted left by 13 bits, the island id shifted left by 6 bits and the region code in the low bits (1 Latium, 3 Albion, 4 Aegyptus). A game island name is optional display text. The island `name` is optional. A reader shows the id when there is none.
- R22. An optional `source` block records where the data came from: kind (savegame, tool, manual), file name, savegame format version, game version and save time.

**Island data**

- R23. Fertilities are explicit: each fertility or deposit GUID is present or missing, and an absent key is unknown. A writer that knows the complete set says so with a completeness flag. The calculator reads an unknown fertility as present, the planner as not missing.
- R24. Building counts per building GUID, residences included, are the primary input. Residences per population level are derivable and optional. Resident counts per level are informational. When per-building and per-level residences are both present and disagree, the per-building counts win and the reader reports the difference.
- R25. Items are recorded per item-bearing building (officium, villa, hippodrome and others): building GUID and instance id, map position and rotation, and per item its slot, whether it is boosted and whether its boost condition is met, each only when the writer knows it. The specification names the coordinate system (game tile units, rotation in radians, absent rotation meaning zero). Items that act on a factory or residence keep their per-factory and per-residence fields next to this.
- R26. Applied radius effects are the effects that reach production buildings by range (item effects, dovecote, granary, silo, irrigation and similar). They are recorded per island and production building type: building type GUID, effect GUID, source kind, the share of the type's buildings in range, whether the effect is applied, how the share was computed (circle, street distance, or circle as the fallback for types without a footprint), and a scale where known. The share carries differences between the buildings of one type, which a model with one setting per type cannot hold; the applied flag is the writer's decision by its stated rule, and a reader may apply its own threshold to the share. The savegame script applies an effect to a type when more than half of its buildings are in range. They are separate from the items socketed in villas and officia, which record where items sit (R25). Range bonuses per source building type are recorded as percentages. Island-wide effect scales stay separate.
- R27. Trade carries three layers, each optional on its own. Route configurations: route id and name, the stations in circuit order, and per station the cargo slots with product, mode (load or unload; a stop that does both has slots of both modes), slot index and slot amount. Derived good flow: per receiving island and good an import amount per minute with its suppliers and their shares. Recorded information: the ships of each route with their type, slot count and modules, and the visits that took place (time, island, ship type, goods and net amounts).
- R34. The minimum stock level is an island attribute per good, shared by every route that serves that island and good. It is recorded as such and never as a property of a route station. The island's production buildings ignore it and consume until the storage is empty. A route that loads there takes only as much as keeps the stock at or above the level; a route that only unloads there is not affected.
- R32. A route configuration is stored as the game has it, so a route with one load-only source, load-and-unload stops and an unload-only last stop keeps that shape. A slot may be configured to carry less than a full slot, so the slot amount is a stored quantity and never assumed. The simplified good flow is derived from the configuration for tools that only model imports. The source role, the sink role and the supplier of each sink follow from the slot modes. When several sources load the same good on one route, the first loader in circuit order serves the stops first. When an island is supplied by several sources, the import is split by weight, which is visits per time times unload slots times slot amount. An amount is derived only where the demand is known; otherwise the flow states that the supplier covers everything. The specification defines the rule and lists the constellations it covers.
- R51. Writers record facts and topology, and readers compute amounts. A writer records route configurations, recorded visits, local production (built counts) and the supplier topology, which follows from the slot modes. Any amount or share in `trade.imports` that a writer derives is an estimate and says so in its basis. A reader that models imports takes the supplier set from the topology and computes the import from its own demand and local supply: demand minus the output of fully utilized local production. It uses the weight shares only to choose the default among several suppliers or where its model needs a split. Amounts the user entered (basis "entered") win over every derived amount. The specification ships the reference derivation and its conformance cases for readers with no better source.
- R52. Suppliers a tool does not model degrade to the nearest supplier type it does model, and the report lists each degradation. The original supplier stays in preserved data and is restored on export. A governor harbour becomes the calculator's passive-trade supplier with its amount as the minimum; non-player islands become passive trade in the calculator and goods bought from traders in the planner. In the planner, a good that several producer types make on one island keeps the type with the most built buildings and the others are preserved and listed; a good that the island produces and also imports keeps local production when its capacity covers the demand, and the rest counts as bought from traders.
- R53. A default supplier of a good that is a factory (the calculator's `defaultSupplier.type` `factory`, not a trade route) names a production building type. When the save has no building of that type on the island and has buildings of another type that produces the same good in the island's region, the writer sets the default supplier to that type. With several candidates it takes the type with the most buildings, and the lower GUID on a tie. A default supplier that is a trade route, passive trade or an extra good is a user choice and stays, and so does a factory default with buildings. The report lists each move with the old and the new type.
- R33. The derived flow states its basis (planned from the configuration, measured from recorded visits, or entered by the user) and that its roles are reliable while its shares are estimates. The minimum stock level does not scale derived amounts; it limits what a loading stop takes from the island's stock.
- R35. The specification ships trade conformance cases for these constellations: point to point, distribution circuit with relays, relay with net zero, manual one-slot route, distribution across sessions, multi-source collection, route with a non-player station, same sink visited twice, good loaded but never unloaded, bidirectional circuit, shared supply of one island and good by two routes, and a route without ships.
- R46. A supplier is an island or a governor's harbour: `{island: id}` or `{governor: GUID}`, in imports and in routes. Governor harbours are recorded once per file with the governor GUID, the region, the map position, the goods the governor produces with their rates, and the stock limits at the harbour. The planner writes and reads them. The calculator keeps governor suppliers and harbours as preserved data, writes no route entry for them and restores them on export.
- R47. Every field of the planner's plan has a destination in the file: a catalog key, or a named field of `ext.planner`. The planner writes all of them, so a plan exported and imported by the planner is unchanged.
- R48. The calculator's per-target choices are kept. An item on a factory has three states: off (not listed), base (listed) and boosted (listed with the boosted flag). An effect that the calculator switches per target is listed on the factory when it is on. The calculator's explicit off equals not listed, so no choice is lost.
- R50. The planner's end buildings per material and the calculator's construction-material factories are the same quantity. The planner's `materials` counts the end factories of a material's chain, and their count times output is the material demand. The calculator enters the number of a construction-material factory by hand and treats it as fully utilized by default, so its count drives the throughput in the same way. The two map directly: the calculator's `built` count of a construction-material end factory with `fullyUtilize` on is the planner's `materials` count for that material, and `materials` is on when any such count is above zero. An absent `fullyUtilize` on a construction-material factory means on, because the calculator only stores the flag when it changes; a calculator export writes it explicitly. The end factory differs per region (the Sawmill has one GUID each for Latium, Albion and Aegyptus), and the specification lists the end factory per material and region. In the other direction the planner writes its `materials` count as that factory's `built` count with `fullyUtilize` on, using the end factory of the island's region. The planner also keeps a built count in `existing`; when only the calculator count is available, the planner sets both from it. The planner preserves `fullyUtilize` on other factories and does not interpret it. The planner's manual extra demand per product has no calculator counterpart and is preserved by the calculator.
- R49. When `trade.routes`, `trade.imports` and `trade.visits` disagree, `imports` is the plan input. `routes` is configuration, and a reader derives imports from it only when `imports` is absent. `visits` are measurements and never override either. The report lists the disagreement.
- R28. The format carries recorded history of storage, production and consumption per island and good as time series, and live values as the latest snapshot including storage where known. Every series and snapshot states its clock (game time or wall clock), its unit and its timestamps. A writer may emit either, both or neither. History comes from savegame readers. The planner and the calculator do not record history; they read it and keep it as it is, so a later feature can derive information from it, such as measured good flow or extra productivity.
- R31. Island map identity is recorded as the map file stem next to the size word. A core-optional layout key is reserved for building positions, rotations, roads and fields; its content stays in a generator's extension block until a revision defines it.
- R40. Harbours are recorded per island: the warehouse type (trading post building GUID), the number of trading spots and the harbour item. The planner maps them to its trading post level and piers.
- R41. The map is recorded as settings (template or map file, size, expansions) and each island's position on it, as a slot on the template, or as the map file element and its coordinates where the map is not one of the planner's random templates. A writer derives them from the save: a campaign map is identified by its file name and each island by its element index in that file. The planner maps what it can to its map settings and island slots and keeps the rest; a campaign map leaves the slot unset and the routes model cannot compute distances for it. The specification states how reliable a derived slot is.
- R42. The fleet is recorded: the effects that apply to all ships and that a plan cannot derive from discoveries, patrons and items (decisions, quests and similar), and the ship configurations in use (ship type, modules, captain item where known) with the number of ships per route.
- R43. Disabled needs (needs the player bans, for example on Cinis) are saved as a list per island and population level. There is no enabled flag, so a need has one state in the file: it is in the list or it is not. A need that is not listed is not disabled; this is the one exception to "absence means unknown", because the game's own ban list is a list of disabled needs. The calculator writes the needs it has switched off and reads every other need as on, including needs unlocked by a DLC that an older config never covered (for example the Dawn of the Delta needs of Roman and Celtic residents). Needs of a DLC the importing tool has switched off are ignored and kept for when it is switched on. A savegame writer derives the list from the save's pause data per population level (the player stopped supplying a good to a tier).

**Passthrough and fidelity**

- R13. A tool preserves every field it does not understand, at any level, and writes it back on export.
- R14. Preserved data stays with its island. Deleting an island deletes its preserved data. Renaming an island keeps it.
- R15. Where a tool modelled and preserved a value, the value the user edited wins.
- R16. Core inputs arrive exactly: islands, patron and devotion, building counts, items, fertilities, chosen suppliers, need toggles, effects and imports.
- R17. The exporting tool writes calculated values per island into an informational block. The importing tool compares them with its own results and shows differences in the report. Differences do not block the import.
- R38. Identifiers a tool does not know are kept and written back wherever they occur, as map keys and as values. When a tool cannot load a core record into its runtime model, it may keep that record internally in an extension store, but export places it back at its original core location. This covers regions (a session GUID the tool cannot display keeps its islands, building counts and everything attached to them), buildings, products, effects, discoveries and DLC names that a later game version or DLC adds. The report lists them as carried through.
- R39. The calculator reads discoveries from `research` and writes the discoveries it knows. Nile flood and obsidian gathering are stored as specific effects in `effects.bySession` and Vercators plough as a specific effect in `effects.global`, unless the planner has a checkbox or a derivation for them (it derives Vercators plough from the global devotion), in which case the planner's setting or derivation carries them. Every other discovery or setting that the two tools model differently has a conversion rule in the specification. A reader that finds the same discovery in `research` and as a specific effect uses the specific effect.
- R45. The planner derives the unlock of a patron's wonder effects from the sum of that patron's devotion over all islands, not from the highest single island. Today it checks each island on its own, so a wonder that the game has unlocked can show as locked after an import.
- R44. The calculator's Plan and Master view modes set all global effects on, and the Master mode also sets the volcano effects to level 5 and Nile flood on, so its stored scales are partly an all-on default. A calculator export therefore states the basis of `research` and of the settings derived from its scales: "applied" (what the calculator applies) or "researched" (what the player has done). A reader treats applied values as settings and not as researched state. The savegame and the planner write "researched".

**Savegame writer**

- R29. The savegame script in the layout repo writes the exchange format from a `.a8s` savegame, is documented there, and resolves island names the way the Anno1800SavegameVisualizer does: the hand-typed `CityName` of a renamed island, else the game text behind `CityNameGuid`, else a placeholder. A name from the save is display text only.
- R36. The savegame script derives applied effects by rules it documents. Circle effects reach a building whose centre lies within the effect radius of a source building's centre. Street-distance effects reach a building whose footprint (touch distance 1.0 tile) meets a road reached within the effect's distance, measured as walked length along the road graph from the save: diagonal steps cost 1.414, paved and marble roads 1/1.5, and the walk starts at zero. The layout tool's own model (one hop per tile, the first tile already costs) did not reproduce the in-game observation, so the script uses the walked-length metric and keeps the layout model as an option. Production building types without a footprint fall back to the circle. An effect applies to a type when more than half of its buildings are reached. The script's README names the in-game observations the rules were validated against and the assumptions that remain (walkway and bridge hop costs).
- R37. Game routes map to calculator routes by a best-effort rule that the specification records as the reference derivation. Per product, source and sink roles follow from the slot modes, and every source feeds every sink and relay of its route. Several sources on one route serve in circuit order. An island served by several sources splits by weight, which is visits per time times unload amount from the configured slot amounts. For the calculator, the supplier with the largest weight becomes the default supplier route with minimum zero and every other supplier an ordinary route with a minimum amount equal to its weight share of the island's demand; where the demand is unknown, every supplier is an ordinary route at zero and the largest is the default. Where the receiving island produces the good itself, the calculator sets the local producer to fully utilized and imports the rest of the demand, so no amount depends on the flow estimate (R51). For the planner, all suppliers but the largest get t/min amounts and are listed first, and the largest comes last with "everything". Where every stop of a route both loads and unloads a good, the roles come from the signs of the recorded net amounts. Legs to stations on non-player areas are dropped, and a route with only such stations has no flow, because the calculator cannot model non-player suppliers. A route without ships moves no goods and gets no entry. Relay stops pass nothing on, and order-dependent constellations (several loaders feeding one unload slot, the same sink visited twice in one lap) are approximated by attributing cargo cyclically. The planner cannot hold a partial import of a good the island also produces, so such pairs are reported and not written there. The result is marked as an estimate. In the planner form on 8 shared-supply cases the weight split has a mean error of 0.27, the same as an equal split, so the shares are weak evidence. Against recorded flows the weight split has a mean error of 0.23 (equal split 0.39), and the calculator form with the largest supplier as default 0.18 on shared supplies.

### Exchange format keys

Envelope shape (illustrative; the specification fixes names):

```json
{
  "format": "anno117-exchange",
  "formatVersion": "1.0",
  "generator": { "name": "anno117-layout-tool", "version": "..." },
  "source": { "kind": "savegame", "file": "...", "gameVersion": "..." },
  "name": "Marcia 69",
  "settings": { }, "effects": { }, "research": { },
  "islands": [ { "id": "...", "gameIsland": { }, "buildings": { }, "ext": { } } ],
  "trade": { "routes": [ ], "imports": [ ] },
  "history": [ ], "live": { }, "computed": { },
  "ext": { "<generator>": { } }
}
```

Required keys are `format`, `formatVersion`, `generator.name` and `islands[].id`. The catalog lists keys new in the format. Names are working names.

**Document scope**

| Key | Meaning | Written today by | Placement |
|---|---|---|---|
| `format`, `formatVersion` | Marker and revision | new | core, required |
| `generator.name`, `.version` | Writing tool and its version (calculator: `versionCalculator`) | calculator (version) | core, required name |
| `source` | Origin: kind, file, savegame format version, game version, save time | new | core-optional |
| `name` | Plan name | planner (`name`) | core-optional |
| `settings.dlcs` | Owned DLCs | calculator, planner | core-optional |
| `settings.difficulty`, `.volcano`, `.seasons` | Difficulty options, eruption cycle, Nile season assumptions | planner | core-optional |
| `settings.map` | Map template, size, expansions | planner (`map`); savegame | core-optional |
| `fleet.effects`, `fleet.ships` | Effects on all ships that a plan cannot derive; ship configurations in use (type, modules, captain) | planner (`ship_effects`, `ship_templates`); savegame | core-optional |
| `effects.global` | Empire-wide effect GUID -> scale (calculator: `globalEffects`); holds Vervactor's Plough and the other wonder effects the calculator stores | calculator, planner (`global_effects`) | core-optional |
| `effects.bySession` | Effect scale per region/session (calculator: `sessionSettings`); holds the discoveries the calculator models as settings (Nile flood, obsidian gathering) | calculator | core-optional |
| `research.researched`, `.counts`, `.queue`, `.knowledgePerMinute` | Researched discoveries, repeat counts, planned order, research speed for the time estimate | calculator (read and written), planner; savegame | core-optional |
| `dominantPatron` | Empire-wide dominant patron | planner; savegame | core-optional |
| `trade.routes[]` | Route configuration: id, name, stations in circuit order (island id; cargo slots with product, mode load/unload, slot index, slot amount), ships `{type, slots, modules}`, manually-saved flag | savegame (`SessionTradeRouteManager`, ship objects); planner (`routes`, `ship_templates`) | core-optional |
| `trade.imports[]` | Derived good flow: receiving island id, product, amount (t/min) or "covers everything", basis (planned or measured), suppliers `{island id or governor GUID, share}`, default-supplier flag (calculator: `tradeRoutes`; planner: `supplied_by`) | calculator, planner; savegame (derived) | core-optional |
| `trade.governorHarbours[]` | Governor harbour: governor GUID, region, map position, goods with rates, stock limits; referenced by `{governor: GUID}` suppliers | planner (`governor_sources`) | core-optional |
| `trade.visits[]` | Recorded visits: route id, island id, trader id, time and clock, ship type, goods with net amounts (unloaded minus reloaded; zero nets are absent) | savegame (`PassiveTrade/History/TradeRouteEntries`) | core-optional, informational |
| `history[]` | Series: island id, product, kind (storage, production, consumption), clock, unit, start, step and values or timestamped points | savegame (period snapshots, storage trends); kept as is by the planner and the calculator | core-optional, informational |
| `live` | Latest values per island and product: generation, consumption, delta, ideal generation and consumption, buildings, productivity, storage where known; clock, timestamp, unit | planner and calculator statistics feed | core-optional, informational |
| `computed` | Per island at export time: residents per population level, buildings required per factory type, import per good (t/min) | new | core-optional, informational |
| `ext.planner.passiveTrade` | Trader budgets and stock (`passive_trade`), visit times (`trader_visits`), detour (`trade_detour`) and island count of the round (`trade_round_islands`) | planner | extension |
| `ext.planner.shipping` | Map detour, per-route detour, channel choices and manual round-trip minutes (`RouteSettings`) | planner | extension |
| `ext.<generator>` | Private data, for example calculator UI state and the "All Islands" aggregate, layout tool geometry | all | extension |

**Island scope** (`islands[]`)

| Key | Meaning | Written today by | Placement |
|---|---|---|---|
| `id` | Opaque id, unique in the file | planner (`id`); calculator uses the name as key | core, required |
| `name` | Display name | calculator, planner | core-optional |
| `session` | Region/session GUID | calculator, planner, savegame | core-optional |
| `gameIsland` | Game reference: session GUID, island id, area index, derived area key, optional game name | calculator (`gameConnector.*`); planner (name only, in app settings); savegame | core-optional, preferred match key |
| `islandFile`, `islandSize` | Map file stem and size word | savegame; planner (`island_size`) | core-optional |
| `fertilities`, `fertilitiesComplete` | Fertility/deposit GUID -> present, and a flag for a complete set | calculator (`island.fertility.N.checked`); planner (missing ones); savegame | core-optional |
| `patron`, `devotion` | Selected patron and devotion | calculator, planner, savegame | core-optional |
| `buildings` | Building GUID -> `built`, `planned`, `fullyUtilize` (residences included); `fullyUtilize` means the built buildings are assumed to run at full capacity even without demand, and it is always on for construction-material factories in the calculator | calculator (`N.buildings.*`); planner (`existing`); savegame | core-optional |
| `residencesByLevel` | Population level GUID -> number of residences, derivable | planner (`residences`) | core-optional |
| `population` | Population level GUID -> resident count, informational | savegame | core-optional, informational |
| `disabledNeeds` | Population level GUID -> list of need GUIDs that are not supplied | calculator (`N[N].checked` = 0); planner (`disabled_needs`); savegame (banned needs) | core-optional |
| `needNotes` | Population level GUID -> need GUID -> free text | calculator (`N[N].notes`) | core-optional |
| `products` | Product GUID -> `producer` (factory GUID or none), `notes` | calculator (`defaultSupplier.*`, `notes`); planner (`producers`) | core-optional |
| `factories` | Factory GUID -> items `{item, boosted}` (off = not listed), `effects` (per-target effects switched on), `aqueduct`, `modules`, `manualProductivity` | calculator (`F[I].scaling`, `aqueductBuff`, `module[M]`); planner (`factories`) | core-optional |
| `itemHolders[]` | Item-bearing building: GUID, instance id, position (x, z, optional height), rotation, items `{item, slot, boosted, boostConditionMet}` | savegame | core-optional |
| `effects` | Island effect GUID -> scale | calculator (`island.effect.N.scaling`); planner (`island_effects`); savegame (ids only) | core-optional |
| `appliedEffects[]` | Radius effects reaching production buildings, per building type: type GUID, effect GUID, source kind, share in range, applied flag, method (circle, street, circle fallback), optional scale | savegame (derived from `AreaEffectManager` and building positions); calculator (`aqueductBuff`, `module`, item states); planner (`factories`) | core-optional |
| `rangeBuffs` | Building type GUID -> range bonus in percent | savegame | core-optional |
| `residenceItems`, `residenceEffects`, `villaCoverage`, `publicCoverages` | Items and area effects on residences and their share in range | planner; calculator (`B.effectCoverage`) | core-optional |
| `notes` | Free text per residence building | calculator | core-optional |
| `harbour` | Trading post: warehouse building GUID, number of trading spots, harbour item `{item, boosted}` | planner (`harbour`, `piers`, `harbour_item`); savegame | core-optional |
| `position` | Island position on the map: slot on the template, or coordinates | planner (`map_slot`); savegame | core-optional |
| `islandItems[]` | Items whose effect covers the whole island `{item, boosted}` | planner (`island_items`) | core-optional |
| `materials` | Building materials produced on the island: switch and end factories per material (the same quantity as the `built` count of the material's factory with `fullyUtilize` on) | planner (`materials_on`, `materials`); calculator (`constructed` of construction-material factories) | core-optional |
| `publicCoverage` | Default share (%) of residences in range of public buildings, used where `publicCoverages` has no value | planner (`public_coverage`) | core-optional |
| `romanization`, `wonders`, `extraDemand` | Planner-side island inputs | planner | core-optional |
| `minimumStock` | Product GUID -> minimum stock fill level the island keeps (shared by all routes serving it) | savegame (`AreaInfo/PassiveTrade/MinimumStock`) | core-optional |
| `layout` | Reserved: building positions, rotations, roads, fields | none yet (layout tool uses `ext`) | reserved core-optional |
| `ext.<generator>` | Private island data | all | extension |

### Conversion rules

The tools model some discoveries and settings differently. The specification records each rule. They come from a review of the planner's model against the calculator's code and `Marcia 69.json`.

| Case | Calculator | Planner | Rule |
|---|---|---|---|
| Plain discoveries (15 with production effects) | global effect scale 0 or 1 | discovery in the tech list | import: a scale above 0 puts the discovery in `research`; export: a researched discovery writes scale 1 for each of its effects |
| Repeatable discovery (Beneath Bedrock) | scale equals the repeat count | discovery plus repeat count | count equals scale; scale 0 when not researched |
| Volcanic soil level and unlocks (Obsidian Gathering, Obsidian Mining, Fertile Soil) | the same scale on each unlocked effect, in the Latium and the Meta session | one level and a list of unlocked effects | level is the largest scale; unlocked effects are those above 0; differing values are reported; export writes the level to each unlocked effect and 0 to the others, in both sessions; eruption phases and durations stay in `settings.volcano` and the calculator preserves them |
| Nile flood harvest effect | scale 1 in the Aegyptus session, with the effect values adjusted to the season average | seasons enabled, phase, unlocks | a scale above 0 enables seasons in average mode; export writes 1 when seasons are enabled in average mode; a planner phase setting (one season only) has no calculator value and is reported; the unlocks stay in `settings.seasons` and the calculator preserves them |
| Wonder effects derived from devotion (Vervactor's Plough, Arboreal Rhizome, other patron wonders) | global effect 1 | derived from the sum of a patron's devotion over all islands reaching the wonder threshold (4000) | exchanged as specific effects in `effects.global`; the planner derives them from the summed devotion and ignores the stored value; the calculator value is informational; a disagreement goes into the report |
| Area buffs (four fertility grants of discoveries: Mackerel Hauling, Vino Veritas, Blood of Terra, Ulex & Agogae) | a 0 or 1 scale `<buff GUID>.scaling` stored next to the global effects, with no control in the interface; the live path is the discovery's own effect | fertility derived from the discovery in the tech list | derived from `research`; the stored area-buff scale is ignored and kept verbatim in `ext.calculator` for the round trip; whether an island has a fertility belongs to `fertilities` |
| Fertility effects of other effects (for example Open Sesame, Mature Trees) | ordinary effect scale | none or derived | specific effects in `effects.global` (R38) |
| Patron local effects | island effect scales, recomputed from patron and devotion | patron and devotion | only patron and devotion are exchanged, as entered and without rounding |
| Wonder splendour rewards (Hippodrome, Colosseum) | island effect 0 or 1 per reward | rank 0 to 10 and coverage | set rewards give a lower bound for the rank; a rank sets the rewards up to it; coverage has no calculator value |
| Building, mythical-item and other calculator-only effects (for example Open Sesame) | island or global effect scale | none | kept as specific effects (R38) |
| Dominant patron | none | dominant patron | `dominantPatron`, preserved by the calculator |
| Need consumption difficulty | option id | difficulty option id | same ids |
| Discoveries without a calculator counterpart (32 with production effects, and research without effects) | none | in the tech list | `research` only, preserved by the calculator |
| "All Islands" aggregate (Meta session) | its own store | none | stays in `ext.calculator`; never imported as an island |

### Key Flows

- F1. Calculator -> planner -> calculator
  - **Trigger:** The user has notes and supplier choices in the calculator and wants to refine the plan in the planner.
  - **Steps:** The user exports from the calculator. The planner imports and replaces the open plan, shows the report, keeps the notes and the calculator's private data. The user edits residences and supplier choices and exports. The calculator imports and shows the edits and the original notes.
  - **Outcome:** Notes and private data are unchanged; edited values are the new ones.
  - **Covered by:** R2, R3, R13, R14, R15

- F2. Savegame -> planner
  - **Trigger:** The user has a `.a8s` savegame and no calculator config.
  - **Steps:** The user runs the savegame script from the layout repo. It writes an exchange file with islands, building counts, patrons, fertilities, items per villa, research and the game island references. The planner imports it and shows what the file did not carry.
  - **Outcome:** The planner shows the savegame's islands with their built counts; suppliers, need toggles and notes are at defaults.
  - **Covered by:** R18, R21, R24, R25, R29

- F3. Existing calculator config
  - **Trigger:** The user has `Marcia 69.json` in the old format.
  - **Steps:** The user opens it in the updated calculator, exports the exchange format and imports that file in the planner.
  - **Outcome:** The planner shows inputs identical to the calculator.
  - **Covered by:** R5, R6, R16

### Acceptance Examples

- AE1. **Covers R13, R14.** Given a calculator export with a note on a need and a collapsed-panel state, when the planner imports and exports it unchanged, the calculator reads back the same note and state.
- AE2. **Covers R14.** Given an imported island with preserved data, when the user deletes it in the planner and exports, the file has no data for it. When the user renames it instead, the preserved data stays attached.
- AE3. **Covers R15.** Given an imported island whose supplier for Bread was Roma, when the user changes it to Tiberia in the planner and exports, the file holds Tiberia and the calculator shows Tiberia.
- AE4. **Covers R4.** Given a file with a newer major version, when the user imports it, the planner shows a message and the open plan is unchanged.
- AE5. **Covers R17.** Given an export with calculated values, when the planner's results differ for an island, the report lists the island and the differing values and the import completes.
- AE6. **Covers R18, R19.** Given a file from an unknown generator with only islands and building counts, when a tool imports it, the import succeeds and the report lists every optional area as not provided.
- AE7. **Covers R21.** Given two islands named "Latium 5" with different game island references, when a file is compared against the open plan, they match by reference and not by name.
- AE8. **Covers R23.** Given an island whose file lists no fertilities, when the calculator imports it, nothing is ticked or unticked and the island keeps its current fertility choices.
- AE9. **Covers R24.** Given a file with 94 Wader residences by building and 129 by level, when a tool imports it, 94 is used and the report names the difference.
- AE10. **Covers R25.** Given a villa with two items where one is boosted and its boost condition is met, when the file is written and read back, the villa's position and rotation, both items, their slots and the boosted and condition states are unchanged.
- AE11. **Covers R28.** Given a file with a storage history for Bread on one island, when a tool imports and exports it, the series and its clock, unit and timestamps are unchanged.
- AE12. **Covers R26.** Given an island where 5 of 8 Bakeries are in range of a granary effect, when the savegame script writes it, the file holds one entry for the Bakery type and that effect with a share of 5/8 and the effect applied. With 4 of 8 in range, the entry is not applied.
- AE13. **Covers R27, R32.** Given a Dates route with a load-only source, three load-and-unload stops and an unload-only last stop, when the file is written, the route keeps its stations in circuit order with each stop's slots and modes, and the derived flow lists a Dates import for each of the four other islands with the source as supplier at a share of 1.
- AE14. **Covers R32.** Given an island supplied with Dates by two source islands whose ships visit it with a 2:1 ratio of visits times unload slots, when the flow is derived, the import is split two thirds and one third between them.
- AE15. **Covers R33.** Given a derived flow built from recorded visits, when a tool reads it, the basis says measured and the amounts match the recorded visits over the stated window.
- AE16. **Covers R34.** Given two routes that serve the same island with the same good, when the file is written, the island records one minimum stock level for that good and neither route carries a level.
- AE17. **Covers R32.** Given a route whose station order in the file differs from ascending station ids, when the file is written and read back, the stations keep the file order.
- AE18. **Covers R38.** Given a file with an island in a region the tool does not know, a building count for an unknown building GUID and an effect scale for an unknown effect GUID, when a tool imports and exports it, the island remains in `islands[]`, the count remains under `buildings`, and the scale remains under `effects`; the report lists them as carried through.
- AE19. **Covers R39.** Given a file whose `research` lists a repeatable discovery researched five times, when the calculator imports it, the calculator applies the effect of five levels, and when it exports, `research` lists the same discovery and count. Given a file with obsidian gathering as a specific effect, the calculator applies that effect and the soil level stays as the file states it.
- AE22. **Covers R43.** Given a file whose disabled needs for a Latium island do not list the needs unlocked by Dawn of the Delta, when the calculator imports it with that DLC on, those needs are on for the island's Roman population levels.
- AE23. **Covers R5.** Given a valid exchange file, when the calculator opens the import confirmation, it names that island stores, calculator settings, trade data and preserved exchange data will be replaced. Cancel leaves storage unchanged; confirm replaces that state and reloads.
- AE24. **Covers R53.** Given Anubis Rest Nome in `Marcia 71.a8s`, whose default supplier for Good Wheat is the Greco-Roman field farm (152143) with no field farms built and 3 riverbank farms (155407) built, when the calculator config is updated, the default supplier of Good Wheat becomes 155407. The same island has no flax or barley farm of either type, so those two defaults stay; on Nilopolis the Barley default moves from the field farm (151993) to the riverbank farm (155404, 10 built).
- AE21. **Covers R50.** Given Cinis as stored in `Marcia 69.json` (the Latium Sawmill with a constructed count of 4 and no `fullyUtilize` key, so 4 sawmills as the fully utilized construction-material end factories, requiring 8 t/min of wood: 2 t/min each from a 30 s cycle), when the planner imports the file, its `materials` count for that material on Cinis is 4 and its wood demand is 8 t/min. When the planner exports a plan with `materials` set to 4 for that material on Cinis, the file holds a `built` count of 4 for the sawmill with `fullyUtilize` on, and the calculator shows the same 8 t/min wood demand.
- AE20. **Covers R34.** Given an island with a minimum stock level for Bread and a route that loads Bread there, when the flow is derived, the loading stop is limited by the level and the island's own bakeries are not.

### Success Criteria

- The savegame script's output for `Marcia 69.a8s` validates against the schema and imports into the planner and the calculator.
- Importing the exchange export of `Marcia 69.json` into the planner brings every core input over exactly, compared island by island against the calculator. Gaps the user has not entered yet in the calculator (for example Aegyptus trade routes and buffs) are reported as not provided, not as differences.
- Comparing the savegame-derived file with the calculator export of the same game state sorts each island's values into matching, differing, savegame-only and calculator-only. The Aegyptus gaps the user has not entered appear as savegame-only.
- The range rules reproduce the user's in-game observation that the library on the island Star-of-the-Nile Nome reaches every production building except one vintner.
- After planner edits and re-export, the calculator shows the edits and keeps every note and private setting.
- A third-party tool can write a valid file from the specification and schema alone.
- A field defined as core-optional can be implemented in either tool without a format revision.

### Scope Boundaries

**Deferred for later**

- Reading old-format calculator configs directly in the planner.
- Merging islands from a file into the open plan, and opening an import as a new plan file.
- Showing imported history and live values in the tools' interfaces beyond the statistics views they already have.
- Deriving information from history in the calculators, such as measured good flow and extra productivity. The format stores the data so these features need no format change.
- Defining the content of `layout` (building positions, roads, fields) as core-optional fields.
- Confirming the savegame script's street-distance rule on more islands. It reproduces one in-game observation (the library on Star-of-the-Nile Nome reaches every production building except one vintner) and agrees with the game's own list of street-connected objects for that library. Latium and Albion, bridge and walkway costs, and the four riverbank farm types that use the circle fallback are untested.

**Outside this work**

- Reading `.a8s` savegames inside the planner or the calculator. The layout repo's script does that.
- An irrigation field. The Aegyptus irrigation grid is stored in the save as a pipe bit grid, and no productivity effect depends on an irrigation percentage. The water bonus of Egyptian field farms is covered by the per-farm-type aqueduct flag, derived from the aqueduct distributors in range.
- Planner settings that live in the app and not in the plan (sandbox setups, goods choices, solved achievements).

### Dependencies and Assumptions

- Four repos change: the new specification repo, the planner, the calculator and the layout tool.
- Both tools and the savegame key data by the same game GUIDs. Items, buildings, discoveries, regions and DLC content missing in one tool's game data version are listed in the report and preserved (R38).
- In `Marcia 69.json` the construction-material end factories (13 materials; for example the Sawmill on Cinis and Juliana, the Mud Stacker on Aegyptus islands) carry a constructed count and no `fullyUtilize` key. Other factories carry an explicit flag where the user set one (on Cinis on for the Gold Washer, Gold Mine, Vintner, Latrunculi Workshop and Tabulus, off for the Marble Quarry), so the flag is in use beyond construction materials.
- The calculator export of the same game is older than the savegame. Differences in residences, patrons, devotion and repeat counts are expected, and the comparison sorts them as differing or savegame-only, not as errors of either tool.
- The calculator's per-island storage holds JSON strings inside its config dump, as in `Marcia 69.json`; the calculator already parses them.
- Residence data has two views: the calculator and the savegame count residence buildings, the planner counts residences per population level.
- A savegame holds no suppliers, no need toggles and no notes. Island names come from the resolution in R29; the same name can occur on several islands (three Albion islands in one save are named "f"), which is why names are never identity.
- The savegame script depends on RdaConsole and FileDBReader, which the layout repo already uses. It ran on two saves, format versions 0x50 (22 islands, with Aegyptus) and 0x21 (31 islands, Latium and Albion only), without changes.
- The savegame holds the hand-typed island name (`CityName`) on renamed islands and a text id (`CityNameGuid`) on default-named ones, so names resolve for both.
- The minimum stock level reserves stock on its island, as stated in R34. The recorded amounts at receiving stops show no cap, which fits: the level acts on loading stops.
- The circle rule of the savegame script is the layout tool's model. The street rule differs from it and is validated against one in-game observation and the game's street-connection list for one library. Both are named in the script's README.
- Both target models can express a split between suppliers. The calculator takes an ordinary route with a minimum amount above zero plus a default supplier route with minimum zero that covers the rest. The planner takes supplier amounts per island, or "everything" for one supplier. The derived flow is shaped so that both mappings work.
- The save keeps trading posts and trading piers as ordinary building objects, with one post GUID per region level; the harbour item is socketed nowhere in `Marcia 69.a8s`, so it is unset.
- The savegame holds a campaign map for Latium and Albion (file `roman_province_campaign_01_dlc01expanded` and a Celtic campaign), not a random template; Aegyptus uses a default map whose file names equal the planner's island names.
- The accuracy of the derived flow is documented in `docs/analysis/derived-trade-flow-accuracy/analysis.md` with the scripts that produced it.

### Outstanding Questions

**Deferred to planning**

- The details of mapping game routes to calculator routes beyond the reference derivation in R37: how relay stops and order-dependent constellations (several loaders feeding one unload slot, the same sink visited twice in one lap) are handled in each target tool, and which demand value the calculators supply for the "covers everything" case. The conformance cases in R35 settle the outcome. The route configuration, the weights and the accuracy figures are in `docs/analysis/derived-trade-flow-accuracy/analysis.md`.

### Sources

- `anno-117-calculator/src/main.ts`: `exportConfig`, `installImportConfigListener`.
- `anno-117-calculator/src/world.ts`: persisted keys per island.
- `anno-117-calculator/src/statistics-feed.ts`: the game's island identity triple.
- `paxplanner/model/project.py`: `Plan`, `IslandPlan`, `Plan.from_json`.
- `paxplanner/ui/progress_view.py`: `live_links` in the app settings.
- `Anno-117-Layout-Tool` savegame parser and the savegame-to-plan script, and `Anno1800SavegameVisualizer` for name resolution.
- Calculator config example `Marcia 69.json` and the savegame `Marcia 69.a8s` (22 islands).
