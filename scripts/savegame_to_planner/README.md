# Savegame to Planner plan

`savegame_to_planner.py` reads an Anno 117 savegame (`.a8s`) and writes a plan file for the
Taludas Planner (`Plan.to_json` format, `paxplanner/model/project.py`). It is a command line
script, separate from the layout tool GUI, and it only reads the savegame.

It reuses the decoder helpers of `savegame_parser.py` (archive extraction, zlib, FileDBReader, session blobs, island
template matching) and adds the readers for the data the layout import does not need (patron, devotion, fertilities,
items, techs, names).

## Prerequisites

- Python 3.11+ with the Planner's environment: run the script with the Planner checkout's interpreter
  (`uv run python ...` inside the Planner repo). The Planner repo is found at `../Anno-117-Planner` or via
  `--planner-repo` / `ANNO_PLANNER_REPO`. The Planner repo is only read.
- RdaConsole and FileDBReader (same tools and .NET 6+ runtime as *File -> Import Savegame*). Lookup order:
  `--rda-console` / `--filedb-reader`, environment `ANNO_RDACONSOLE` / `ANNO_FILEDBREADER`, then `tool_manager.get_tool_paths`
  (settings, tools folder, PATH).
- Optional, for island names: the game's `texts_<language>.xml` (`data/base/config/gui/`, extracted from the game's
  data archive with RdaConsole or the Asset Extractor cache), passed with `--texts`.

## Usage

```
cd C:\dev\Anno-117-Planner
uv run python C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner\savegame_to_planner.py ^
    "d:\Dokumente\Anno 117 - Pax Romana\accounts\<account-id>\Marcia\Marcia 69.a8s" ^
    -o C:\temp\marcia69.plan.json --plan-name "Marcia 69" ^
    --texts C:\dev\asset-extractor\.cache-117\data\base\config\gui\texts_english.xml
```

Options: `--work-dir DIR` keeps the decoded XML (default: a temporary folder that is removed), `--reuse` (with
`--work-dir`) skips decoding when `data_raw.xml` and `session_*.xml` are already there, `--report FILE` writes the range
decisions as JSON (range effects, harbours, positions, disabled needs, trade), `--street-mode`, `--plan-name` (default:
file name). Decoding takes a few
minutes for a late-game save (about 230 MB outer XML plus 50-120 MB per session). The output replaces an existing
file; point it somewhere other than the Planner's own `plan.json`. Check the result with `Plan.load(path)`; it
loads in `Engine.solve_island` for every island (checked with the Marcia 69 save: 22 islands).

## How the save is structured

1. `.a8s` is an RDA archive (RdaConsole `extract`) holding `data.a7s`, `header.a7s`, `gamesetup.a7s`, `meta.a7s`.
2. `data.a7s` is zlib compressed FileDB. FileDBReader turns it into the outer XML (one tag or value per line).
3. `MetaGameManager/GameSessions/None/SessionData/BinaryData` hold one hex encoded FileDB blob per session
   (`SessionDesc/SessionGUID`: Latium 3245, Albion 6627, Aegyptus 149679). Each blob is decoded again to a session XML.
   Version marker seen: `SessionFileVersion` = `0x50` (80) in the session XML (Marcia 69).

Where each value lives:

| Value | Location |
|---|---|
| Player areas | session `GameSessionManager/AreaInfo/None[key]` with `OwnerProfile` = 41 |
| Fertilities, deposits | `AreaInfo/None/Fertility/None`, `LimitedLodeComponent/LimitedLodeFertilities` (GUIDs) |
| Island name | `AreaInfo/None/CityNameGuid` (signed 64 bit text id), optional `CityName` (UTF-16, if the player typed one) |
| Buildings | `AreaManagers/AreaManager_<key>/AreaObjectManager/GameObject/objects/None` (`guid`, `ID`, `Position`, component tags such as `Residence7`, `Factory7`) |
| Items on buildings | `.../objects/None/ItemContainer/SocketContainer/SocketItems`, boost flag in `GameSessionManager/ItemSessionManager/ItemMap` |
| Patron, devotion | `AreaManager_<key>/AreaReligionManager/{PatronGuid, Devotion}` |
| Dominant patron | outer XML `MetaReligionManager/ParticipantPatronInfos/Data` (participant 41) |
| Techs | outer XML `MetaGameObjectManager/MetaObjectMap/None/MetaTechHandler` (`TechCompleted`, `TechRepeatables`, `ResearchQueue`) |

Area key (16 bit little endian, also the number in `AreaManager_<key>`):

```
key = (areaIndex << 13) | (islandID << 6) | regionCode      regionCode: 1 Latium, 3 Albion, 4 Aegyptus
```

`islandID` and `areaIndex` equal the calculator's `gameConnector.islandID` / `.areaIndex` (22 of 22 islands of Marcia 69).
The plan island id is `a<key>`: stable for one game, unrelated to the name.

## Island names

Order of resolution per player island (`GameSessionManager/AreaInfo/None[<key>]` in the session XML):

1. `CityName`: the name the player typed, UTF-16 little endian stored as hex (e.g. `42006900670067007900` = `Biggy`).
   Present only on islands that were renamed by hand. Checked in `Autosave 3774.a8s` (SessionFileVersion 0x21): all 31
   player islands have `CityName` and no `CityNameGuid`.
2. `CityNameGuid`: the default name. Read as a signed little endian 64 bit integer it is the `LineId` of the name in
   `texts_<language>.xml` (the language of the file given with `--texts`). Default-named islands have this plus a
   `CityNameIterator` (1 or absent, not used) and no `CityName`. Marcia 69 (0x50): no island has `CityName`; all 22
   names equal the calculator's `islandNames`.
3. Placeholder `Latium 5` / `Aegyptus 17.3` (region, island id, area index when not 1) when there is neither a
   `CityName` nor a text for the id (for example without `--texts`).

The Anno 1800 Savegame Visualizer uses the same order (`CityName`, else `CityNameGuid` looked up in a table of the game
texts); in Anno 117 the id is 64 bit and the table is the game's `texts_<language>.xml`.

## Field mapping to the plan

| Plan field | Status | Source |
|---|---|---|
| `name` | derived (needs `--texts`, else placeholder) | `CityNameGuid` -> texts |
| `session` | derived | session GUID |
| `id` | derived | `a<area key>` |
| `residences` | derived | residence building GUID -> population level (game data) |
| `existing` | derived | building GUID counts for factory GUIDs |
| `patron`, `devotion` | derived | `AreaReligionManager` |
| `missing_fertilities` | derived | fertilities of the region (game data) minus those in `AreaInfo` |
| `residence_items` | derived | villa/officium sockets whose item acts on residences, boost from `ItemMap` |
| `island_size` | derived (approximate) | stem of the island file in the session's map template (small, medium, large, extralarge, continental); campaign start islands (`..._campaign_player_..`) have no size word: `Large` |
| `harbour`, `piers`, `harbour_item` | derived, see "Harbours" | trading post and trading pier objects, villa sockets |
| `map_slot`, `map.dlc01` | partly derived, see "Map and position" | `MapTemplate` of the session |
| `disabled_needs` | derived, see "Disabled needs" | `PopulationPauseInfo` |
| `supplied_by`, `routes`, `ship_templates` | derived, see "Trade routes and fleet" | `SessionTradeRouteManager/RouteMap`, ship objects, visit history |
| `ship_effects` | derived, see "Trade routes and fleet" | `MetaEffectManager/Effects` |
| `dominant_patron`, `techs`, `tech_counts`, `research_queue` | derived | outer XML |
| `factories` (`items`, `building_effects`, `effects`, `silo`, `aqueduct`) | range effects, attached modules and distributor coverage; `silo` is a type-level projection | save positions + effect records + asset metadata |
| `producers`, `island_effects`, `island_items`, `extra_demand`, `materials`, `wonders`, `public_coverage(s)`, `villa_coverage`, `residence_effects`, `romanization` | defaulted | not read |
| `difficulty`, `volcano`, `seasons`, `global_effects`, `map.template`, `map.size`, `knowledge_per_minute` | defaulted | not read (the map template of this save is a campaign template) |
| `passive_trade`, `trader_visits`, `governor_sources`, `trade_*`, route `via_*`, `detour`, `manual_minutes` | not available | not derived |

## Harbours

Per island the script counts the objects of the region's trading posts (`gd.ships["harbours"]`: Latium 3402/3403/3406,
Albion 7037/7038/7039, Aegyptus 149683/150642/150645) and trading piers (31608, 31611, 179570). `harbour` is the
trading post's GUID, `None` for the region's basic post (first in the list); `piers` is the number of trading piers
(the trading spots besides the post). `harbour_item` is an item of the game data's harbour items (Julia Publica,
172289) socketed in a villa or officium whose circle (radius of its effect records, else `effectRadius`) covers the
trading post. In Marcia 69 no such item is placed, so it stays unset.

## Map and position

The session's `MapTemplate` names the template file and lists the island files with their positions
(`Element/Position`, `MapFilePath`). The island id of the area key is the 1-based index into that list (checked on
every Latium and Albion island, centroids of the buildings lie in the island's box). The size word comes from the file
stem. Slots: Aegyptus islands get the Planner's island name from the stem (`..._valley_large_09` is `large_09`; an
island with several areas shares the slot), the Prophecies of Ash continental island is `Cinis`. This save is a campaign
map (`roman_province_campaign_01_dlc01expanded`), which is not one of the Planner's random templates (Archipelago,
Atoll, Corners, IslandChains, Rift: no island position matches), so Latium and Albion slots and `map.template` stay
unset; `map.dlc01` is set from the file name. Reliability: the Aegyptus slot is a name lookup and as reliable as the
index rule; areas with `areaIndex` above 1 lie on the same island file as their island id says, not necessarily on its
main piece.

## Disabled needs

`AreaResidenceConsumptionManager/ProductData` holds per product the `PopulationPauseInfo`: population level and a flag
(`01` = the player stopped supplying that good to that tier). The script writes `disabled_needs[level]` = the needs of
the tier whose product is paused, and nothing for needs that are not paused. `--report` lists them per island with names.
Marcia 69: Cinis has 9 disabled needs (Equites: Fine Glass, Horses, Idols; Patricians: Brooches, Necklaces, Fine
Glass, Idols, Loungers; Plebeians: Soap), Cragmore 1. Against the older calculator export: 2 match (Soap Plebeians,
Brooches Patricians), 1 differs (Necklaces Patricians is supplied there), 7 are savegame-only (not entered), the other
881 unchecked toggles of the calculator are calculator-only (planned or unavailable goods, not bans).

## Trade routes and fleet

- `empire["routes"]`: `MetaGameManager/SessionTradeRouteManager/RouteMap`, the player's routes with stations in file
  (circuit) order, per station the cargo slots (product, load or unload, index, configured amount) and the ship count.
- Ships: the objects with `PropertyTradeRouteVehicle` (type GUID, `TradeRouteID`, `ShipModuleOwner` modules,
  captain item in the item sockets, boost from `ItemMap`). `ship_templates` holds one template per distinct (type, modules,
  captain, boosted); a route's template is the one of its ships.
- Visits: `AreaInfo/PassiveTrade/History/TradeRouteEntries` per island and route (`ExecutionTime`).
- `supplied_by` follows the reference derivation: a station with only load slots for a product is a source, a station
  with unload slots receives (a relay passes nothing on), each receiver is served by the nearest source before it in the
  circuit. An island served by several sources splits by weight = visits at the island x configured unload amount. The
  largest weight is listed last with -1, every other supplier gets its share of the island's demand in t/min (demand from
  the Planner engine without imports; no amount where the demand is 0). A product the island also produces in the save
  is not written (the Planner imports the whole demand of a listed good).
- `routes`: one `RouteSettings` per supplier>receiver pair: the template of the route and its ship count split by the
  pair's share of the route's flow (at least 1).
- `ship_effects`: the optional ship effects of the game data (decisions and quests such as Training for War, Rex Undarum,
  Surf or Turf) that `MetaEffectManager/Effects` applies to the player. The player's Tacking and Quartermastery are
  discovery effects the Planner derives itself. In Marcia 69 the list is empty.
- Estimates: roles are reliable, shares are estimates (mean error 0.23 against recorded flows in the trade analysis).

## Effects and modules configured on production buildings

`residence_items` (above) are the items socketed in villas and officia that act on residences. The planner's
per-factory settings (`FactorySettings`) are type-level choices. The script derives ranged effects from geometry and
module ownership from `ModuleOwner` records, then projects both to one setting per production building type:

- Geometry: the save has the placed buildings (`Position` x/z in tiles, centre of the building) and, per ranged effect, the
  source building and its radius (`AreaEffectManager/Effects`: `Guid`, `Scope/value/id`, `Source/ObjectID`, `Distance`;
  scope 2 = circle, 6 = street distance). Scope 1 is `ModuleOwner`, an attachment relation handled separately below. A building is affected by a circle
  effect when its centre is within `Distance` of the centre of a source building (Euclidean, the same rule as the
  layout tool's `_compute_in_range_ids`; footprints are not used). The save lists no receivers, so this is computed.
- Street distance (scope 6: Library effect 153868 "Thoth Libraire Area Effect", Aegyptus villa items with street scope):
  the road network is read from `AreaStreetManager/Graph/Edges` (edge ends in half tiles, an edge spans several unit
  tiles; dirt road, paved road, marble road, bridges, walkways). A building touches a road tile when the tile centre
  is within 1.0 tile of its oriented footprint (`Position`, `Direction`, game data width/height; adjacent tiles sit
  at 0.5, rotated footprints up to 0.83). The source's reach is a weighted shortest path over the unit tiles with
  budget `Distance`, starting at 0 on the road tiles touching the source: the walked length in tiles (a diagonal step
  is 1.414), times 1/1.5 on paved and marble roads (the layout tool's `ROAD_STREET_DISTANCE_MULTIPLIER`). A building
  is affected when it touches a reached tile. This differs from the layout tool's `_street_distance_bfs` in two points
  (one hop per tile whatever the orientation, and the first tile already costs); `--street-mode layout` selects that
  model instead. Building types without a footprint in the game data (the four Aegyptus riverbank farms) fall back to
  the circle of the same distance; `--report` lists both counts (`affected`, `circle_affected`).
- Validation of the street rule: the user observed in the game that the library on "Star-of-the-Nile Nome" (Aegyptus,
  effect 153868 from library 152071) reaches all production buildings of the island except one vintner. With touch
  distance 1.0 and the walked-length metric the script reproduces exactly that: 49 targeted production buildings, 48
  reached, the unreached one a Vintner (cost 63.4 against 62). With touch distance 0.75 nine farms and bakeries wrongly
  fall out; with the layout tool's hop model no building falls out. The game's own `StreetConnectionCache` (per source
  building, the objects connected by street) separates the same way: the reached objects end at 59.1 walked length,
  the first unreached at 59.4. This is one observation on one island; the layout tool's model is not confirmed.
- Module attachment: scope 1 records identify the exact farm object that owns the module. The module object GUID must
  match the farm type's `additionalModule` in game data. The planner stores one `silo` boolean per factory type, so this
  writer projects the per-instance attachments by strict majority and records `method: "attached"`, the attached owner and module instance
  ids and `projection: "factory_type_majority"` in the report. `applied` describes that planner projection, not whether
  the game applied the module to every building of the type.
- Rule: an effect is applied to a building type when MORE THAN HALF of the buildings of that type are affected (strict
  majority; exactly half is not applied). `--report FILE` lists every decision with `affected`/`total` and flags near
  ties (within 10 % of half, at least one building).
- Mapping:

| Source | Planner field | How |
|---|---|---|
| Item in a villa / officium (radius from its effect records, else the building's `effectRadius`) | `factories[type].items` = `ItemSlot(item, boosted)` | item effect targets and scope from the game data; `boosted` from `ItemMap` `IsBoosted` |
| Granary-type radius effects (game data `building_boosts`) | `factories[type].building_effects` | effect GUID, circle around the granary |
| Hippodrome splendour area effects (game data `area_boosts`), Thoth Library effect | `factories[type].effects` | circle or street reach around the source |
| Silo, dovecote (`AreaEffectManager` scope 1 / `ModuleOwner`) | `factories[type].silo = True` when the attached share is a strict majority | exact owner and module instance ids are read from `ModuleOwner`; module GUID must match the factory type's `additionalModule`; this is an attachment, not range |
| Aqueduct water (`AqueductConsumer/DistributorsInRange` not empty) | `factories[type].aqueduct = True` | for types with an optional water buff |

- Irrigation: `AreaIrrigationManager` stores per irrigation area a pipe grid (`IrrigationAreas`: index, grid origin,
  `FilledPipes` bit grid), a sparse `IndexGrid` and `ObjectToConnectedPipes`; no percentage and no per-farm state.
  Nothing in the game data turns that into production: the only uses are quest conditions
  (`ConditionIrrigationPercentage`), pipe capacity upgrades (`IrrigationUpgrade`) and the farms' optional water buff
  (+50 % productivity, buff 28480), which the aqueduct switch covers. So there is no irrigation field; Aegyptus farm
  types get `aqueduct` from the distributor test above. The grid is not read.
- Not computed (counted in `--report` notes): effects from sources without a position, heroic island-wide effects of
  items that fail the majority test for every type, and per-building differences inside a type (the planner holds one
  setting per type). Techs, patrons and festivals are not read; the planner derives those itself.
- The majority test uses the whole island; the Planner only uses an area effect when its granting buff is active on the
  island (the Thoth effect is listed for every island with a library, the engine ignores it where it is inactive).

## Known limitations

- Items in villas/officia that act on factories: applied only where the range rule above holds (strict majority);
  a type with exactly half affected is left unset, so manual choices in a calculator can differ.
- Counts are all player objects with the building GUID; the save has no per-object blueprint flag in the building list.
- `island_size` comes from the island file stem only.
- Routes with relays, an island at two stops and order-dependent loading are approximated; a good both produced and
  imported is written as produced only; governor harbours and other participants' stations are skipped.
- Fertility universe: fertilities listed with regions in the Planner game data; ones the Planner does not list are ignored.
- Built counts can differ from a calculator config entered earlier; the save is the current state.
- Tested with one save (Marcia 69, `SessionFileVersion` 0x50). Other versions may need adjustments in the readers.
