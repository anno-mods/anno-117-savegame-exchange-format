# Where values live in an Anno 117 savegame

Findings from decoding `Marcia 69.a8s` (SessionFileVersion 0x50, 22 player islands, Latium + Albion + Aegyptus) and
`Autosave 3774.a8s` (0x21, 31 islands, Latium + Albion). Items marked (inferred) were deduced, not read from a
labelled field. The extraction code is `scripts/savegame_to_planner/`; exploratory probes are in `scripts/probes/`.

## Container

`.a8s` is an RDA archive. `data.a7s` inside is zlib-compressed. FileDBReader turns it into XML (about 230 MB). The
XML holds three `BinaryData` session blobs that FileDBReader decodes again to XML (50-120 MB each). Session GUIDs
(from `GameSessions/SessionDesc`): Latium 3245, Albion 6627, Aegyptus 149679. The older save has no Aegyptus session.
Time values are game milliseconds on the meta clock (about 506.1 M to 513.3 M in `Marcia 69`).

## Island identity

Each island has a 16-bit area key (little endian):

```
areaKey = (areaIndex << 13) | (islandID << 6) | regionCode      # region: 1 Latium, 3 Albion, 4 Aegyptus
```

The calculator's `gameConnector.islandID` / `gameConnector.areaIndex` equal these on 22 of 22 islands. A player
island has `OwnerProfile` 41 in `AreaInfo`. Island names are not stored as plain text by default:

| Case | Field in `AreaInfo/None[key]` |
| --- | --- |
| Island renamed by the player | `CityName`, UTF-16 little endian as hex |
| Default name | `CityNameGuid` (signed 64-bit) plus `CityNameIterator`; the id is the LineId in `texts_<language>.xml` under `data/base/config/gui` |

Names can repeat (three Albion islands in `Autosave 3774` are named "f"). Names are display text, never identity.

## Per island (session XML)

| Value | Location |
| --- | --- |
| Buildings, positions | `AreaManagers/AreaManager_<key>/AreaObjectManager/GameObject/objects/None`: `guid`, `ID`, `Position` (3 floats x, height, z in tiles), `Direction` (radians, absent when 0), `Residence7/ResidentCount`, `Factory7` |
| Items in villas/officia | `.../ItemContainer/SocketContainer/SocketItems`, `CurrentlyEnabledItemSocketCount`; boosted flag in the session `ItemSessionManager/ItemMap` (`IsBoosted`); boost condition met in outer `MetaGameManager/ConditionManager/Conditions` (`conditionKey` = `ItemBoost_<itemGUID>_<ItemID>`, `IsResolved`) |
| Patron, devotion | `AreaReligionManager`: `PatronGuid`, `Devotion`, `IslandEffectIDs`, `WonderEffectIDs` |
| Fertilities | `AreaInfo`: `Fertility` list, `LimitedLodeComponent` |
| Radius effects | `AreaEffectManager/Effects/None`: `Guid`, `Id`, `Source/ObjectID`, `Distance`, `Scope/value/id`, optional `SourcePosition`, `ScalingFactor`, `IsBoostedItem`, `ModuleOwner`, `TargetArea`, `EndTimestamp`. The save lists no receiving buildings; targets are computed |
| Range bonuses | `AreaEffectManager/RadiusEffectRangeBuffs`: building GUID -> percent |
| Street graph | `AreaStreetManager/Graph/Edges` (ends in half tiles) |
| Disabled needs | `AreaResidenceConsumptionManager/ProductData/None/PopulationPauseInfo`: population level and a flag (`01` = the player stopped supplying that good to that tier) |
| Trading posts, piers | ordinary objects: posts Latium 3402/3403/3406, Albion 7037/7038/7039, Aegyptus 149683/150642/150645; piers 31608, 31611, 179570 |
| Irrigation (Aegyptus) | `AreaIrrigationManager`: `IrrigationAreas` (grid origin, `FilledPipes` bit grid), `IndexGrid`, `ObjectToConnectedPipes`; no percentage, no per-farm state |

Effect scope ids in `AreaEffectManager`: 1 module owner, 2 circle, 4 objects in area, 6 street distance.

## Empire level (outer XML)

| Value | Location |
| --- | --- |
| Researched discoveries, repeat counts, queue | `MetaTechHandler`: `TechCompleted`, `TechRepeatables`, `ResearchQueue` |
| Dominant patron, cumulative devotion | `MetaReligionManager` |
| Effects on ships | `MetaEffectManager/Effects` (`TargetParticipant` 41), `LocalEffects` keyed by object |
| Map | `GameSessionManager/MapTemplate`: `Filename`, `TemplateElement/Element/{Position, MapFilePath}`; `islandID` is the 1-based index into the element list. Latium and Albion are campaign maps (`roman_province_campaign_01_dlc01expanded`, a Celtic campaign), Aegyptus is `egypt_province_default_01` |

## Trade

| Value | Location |
| --- | --- |
| Route definitions | `MetaGameManager/SessionTradeRouteManager/RouteMap`: 191 routes, 113 owned by participant 41. `Stations` in **file order** (the ship returns from the last to the first; in 28 routes file order differs from ascending `StationID`). A station has `AreaID`, `AreaOwner`, `HasTradeRights`, `GoodInfos` |
| Cargo slots | each `GoodInfos` entry is one slot: `ProductGUID`, `Amount` (configured tons, 50 = full slot; 9 slots below 50 in 5 player routes), `Index`, `IsLoading` (**absent = load, `00` = unload**, verified against recorded signs) |
| Ships | `RouteMap/.../Ships`: packed u64 MetaIDs; ship objects carry `PropertyTradeRouteVehicle` (`TradeRouteID`, `TargetStationID`); type = object `guid`; modules in `ShipModuleOwner/InstalledShipModules`. 135 of 135 route ships link back to their route |
| Recorded visits | `AreaInfo/None/PassiveTrade/History/TradeRouteEntries/None[routeId]`: `Trader`, `TraderShip` (type GUID only), `ExecutionTime`, `TradedGoods` with signed **net** `GoodAmount` (unload minus reload; zero nets are absent). Up to 31 entries per island and route |
| Minimum stock | `AreaInfo/None[key]/PassiveTrade/MinimumStock/None[goodGuid]`: per island and good, shared by all routes. It reserves stock: the island's production ignores it, loading stops take only what keeps stock at or above it (stated by the player) |
| Marker without known meaning | `VanishGoods` on 29 stations (undecoded) |

## History and storage

- `outer MetaGameManager/EconomyStatisticManager/History/areaHistory/None[areaKey]/Snapshots`: 12 snapshots per
  island 600,100 ms apart with `AmountPerProduct` (stock), `GenerationPerProduct`, `ConsumptionPerProduct`.
  Generation and consumption are probably per minute (inferred).
- `AreaInfo/AreaEconomy/StorageTrends/None[good]`: 120-point ring buffer plus `LastPointTime`; spacing and point
  order are not verified.
- The live statistics pipe (planner `paxplanner/live/protocol.py`) has no storage values and uses wall-clock time.

## Not in the save

Island suppliers chosen in a calculator, need notes, planner or calculator settings, the harbour item of the sample
game (socketed nowhere), Latium/Albion random-template slots (campaign maps do not match the planner's templates).
