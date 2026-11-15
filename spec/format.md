# Anno 117 exchange format, version 1.0 draft

The draft wire contract consists of this specification and the schema.
Release gates are the planner catalog review (PD4) and the trade derivation decision and measurements (LD9).
The machine-readable contract is
`schema/anno117-exchange.schema.json` (JSON Schema draft 2020-12); the examples are in `fixtures/`.
`R<n>` and `AE<n>` refer to the requirements document of the planning repository
(`anno-117-savegame-exchange-format`, `docs/spec/exchange-format-requirements.md`).

## Principles

- A file is a JSON object. Required keys: `format` (the string `anno117-exchange`), `formatVersion`
  (`"<major>.<minor>"`), `generator.name`, and `islands[].id`. Other top-level areas are optional (R18);
  when present, their records must satisfy the schema, including required nested keys.
- A missing optional key states nothing (absence means unknown). Two exceptions: `disabledNeeds` (a need not listed is on)
  and `fullyUtilize` of construction-material factories and module buildings (absent means on), R43 and R50.
- Readers ignore unknown keys, unknown generators and newer minor versions, keep what they do not understand
  and write it back (R13, R19). The schema defines no closed list of regions, building kinds, effect kinds, source kinds or
  DLC names. Record objects accept additional keys. Typed maps constrain their entries: GUID-keyed maps use decimal
  GUID strings and the value type specified by the schema.
- A reader rejects a file whose major version is higher than it supports, and a file without the marker, and leaves its
  own state unchanged (R4).
- Identifiers are game GUIDs (integers). Island ids are opaque strings, unique in the file.
- Inputs are inputs, measurements are measurements: `computed`, `history`, `live` and `trade.visits` are informational and
  never turn into plan inputs.

## Placements

- **core**: required keys (`format`, `formatVersion`, `generator.name`, `islands[].id`).
- **core-optional**: defined by the format; any tool may produce or consume them without a format change.
- **extension**: `ext.<generator>` at document, island and route-station scope (and per item record). `<generator>` is the
  extension id a tool chooses, independent of `generator.name`. A tool reads and writes only its own id and preserves the others (R11).

Moving a field from extension to core-optional to core (R12): a minor revision defines the field in core-optional and
names the `ext` location writers used before. A reader of the newer revision reads the core location first; when it is absent
it falls back to the `ext.<generator>` location it knows, and writes the core location on export. The old `ext` content
stays untouched for tools that still read it. A field becomes core (required) only in a major revision, because a new required
key makes older files invalid.

## Catalog: document scope

| Key | Meaning | Placement |
|---|---|---|
| `format`, `formatVersion` | Marker and revision | core, required |
| `generator.name`, `.version` | Writing tool and its version | core, required name |
| `source` | `kind` (savegame, tool, manual; open), `file`, `savegameFormatVersion`, `gameVersion`, `saveTime` | core-optional |
| `name` | Plan name | core-optional |
| `settings.dlcs` | Owned DLC numbers: 1 Prophecies of Ash (calculator key `DLC01_Prophecies_of_Ash`, GUID 67902), 2 The Hippodrome (`DLC02_The_Hippodrome`, 67903), 3 Dawn of the Delta (`DLC03_Dawn_of_Delta`, 67904). A number not in the list is kept. A DLC absent from the list is not owned; absent `settings.dlcs` states nothing | core-optional |
| `settings.difficulty`, `.volcano`, `.seasons`, `.map` | Difficulty options (`needConsumption` option id), eruption cycle, Nile season assumptions, map template/size/expansions | core-optional |
| `fleet.effects`, `fleet.ships` | Effects on all ships that a plan cannot derive; ship configurations | core-optional |
| `effects.global` | Effect GUID -> scale, empire-wide (Vervactor's Plough and other wonder effects) | core-optional |
| `effects.bySession` | Session GUID -> effect GUID -> scale (Nile flood, obsidian gathering, volcano effects) | core-optional |
| `research.researched`, `.counts`, `.queue`, `.knowledgePerMinute` | Researched discoveries, repeat counts per GUID, planned order, research speed | core-optional |
| `research.basis` | `"researched"` (what the player has done) or `"applied"` (what the calculator applies, R44); absent means researched; other values are kept | core-optional |
| `dominantPatron` | Empire-wide dominant patron GUID | core-optional |
| `trade.routes[]` | Route configuration (see Trade) | core-optional |
| `trade.imports[]` | Derived good flow (see Trade) | core-optional |
| `trade.governorHarbours[]` | Governor harbour: `governor`, `region`, `position`, `goods[]` `{product, rate}`, `stockLimits` | core-optional |
| `trade.visits[]` | Recorded visits: `route`, `island`, `trader`, `time`, `clock`, `shipType`, `goods` (product -> net amount, zero nets absent) | core-optional, informational |
| `history[]` | Series: `island`, `product`, `kind` (storage, production, consumption; open), `clock` (game or wall), `unit`, `start` + `step` + `values[]`, or `points[]` of `{t, v}` | core-optional, informational |
| `live` | Latest values: `clock`, `timestamp`, `unit`, `islands` (island id -> product GUID -> `generation`, `consumption`, `delta`, `idealGeneration`, `idealConsumption`, `buildings`, `productivity`, `storage`) | core-optional, informational |
| `account.items[]` | Item records in the account storage (see Item locations) | core-optional |
| `account.transferItems[]` | Item GUIDs of the account transfer list | core-optional |
| `account.racers[]`, `account.race` | Hippodrome racers `{item, appearance, trainings: {attribute id: level}}`; `{wins, losses}` | core-optional |
| `unlocatedItems[]` | Item records the save lists but places nowhere | core-optional, informational |
| `computed` | `computed.islands.<island id>` with `residents` (level -> number), `buildingsRequired` (factory GUID -> unrounded number), `imports` (product -> t/min), written at export time. A difference counts when it exceeds 1 % of the value or 0.1 units, whichever is larger (R17) | core-optional, informational |
| `ext.<generator>` | Private data | extension |

## Catalog: island scope (`islands[]`)

| Key | Meaning | Placement |
|---|---|---|
| `id` | Opaque id, unique in the file | core, required |
| `name` | Display text; never identity. A reader shows the id when there is none | core-optional |
| `session` | Region/session GUID. Any value is valid | core-optional |
| `gameIsland` | `{sessionGuid, islandId, areaIndex, areaKey, name?}`; the preferred match key between files (R21) | core-optional |
| `islandFile`, `islandSize` | Map file stem and size word | core-optional |
| `fertilities`, `fertilitiesComplete` | Fertility/deposit GUID -> boolean (present or missing); with `fertilitiesComplete: true` an absent fertility is missing, otherwise unknown (R23) | core-optional |
| `patron`, `devotion` | Patron GUID, devotion as entered | core-optional |
| `buildings` | Building GUID -> `{built, planned, fullyUtilize}`; residences included. Primary input (R24) | core-optional |
| `residencesByLevel` | Population level GUID -> residence count; derivable. When `buildings` has the per-building count it wins and the reader reports the difference; a reader that models per-building counts maps a per-level count to the level's single residence building when no per-building count exists | core-optional |
| `population` | Population level GUID -> resident count (informational) | core-optional |
| `disabledNeeds` | Population level GUID -> list of disabled need GUIDs; an object (empty when none) for every writer that models needs; unlisted needs are on (R43) | core-optional |
| `needNotes` | Level GUID -> need GUID -> text | core-optional |
| `products` | Product GUID -> `{producer: factory GUID or "none", notes}` | core-optional |
| `factories` | Factory GUID -> `items[]` `{item, boosted}` (off = not listed), `effects[]` (per-target effects switched on), `aqueduct`, `modules` (module GUID -> boolean, type level), `manualProductivity` | core-optional |
| `itemHolders[]`, `itemStorage[]` | See Item locations | core-optional |
| `moduleAttachments[]` | `{building, instance, module, moduleInstance}`: owner building GUID, owner object id, module GUID, module object id (R55) | core-optional |
| `effects` | Island effect GUID -> scale | core-optional |
| `appliedEffects[]` | Range effects per building type `{type, effect, source, share, applied, method, scale}` (R26) | core-optional |
| `rangeBuffs` | Building type GUID -> range bonus in percent | core-optional |
| `residenceItems[]`, `islandItems[]` | `{item, boosted}` lists | core-optional |
| `villaCoverage` | Percent coverage: `default?`, `byLevel?` (level GUID -> percent), `byResidence?` (residence building GUID -> percent) | core-optional |
| `residenceEffects` | `byLevel?` and `byResidence?`: level or residence building GUID -> effect GUID -> percent; no defined default, unlisted effects are not in range | core-optional |
| `publicCoverages` | `default?` percent; `byLevel?` and `byResidence?`: level or residence building GUID -> public building GUID -> percent | core-optional |
| `notes` | Residence building GUID -> text | core-optional |
| `harbour` | `{warehouse, tradingSpots, item}` | core-optional |
| `position` | Slot on the map template, or file element and coordinates | core-optional |
| `materials`, `romanization`, `wonders`, `extraDemand` | Planner-side island inputs | core-optional |
| `minimumStock` | Product GUID -> minimum stock level, an island attribute shared by all routes (R34) | core-optional |
| `layout` | Reserved for building positions, rotations, roads and fields (R31) | reserved |
| `ext.<generator>` | Private island data | extension |

All coverage values are 0 to 100. Lookup order is `byResidence`, `byLevel`, then `default` where defined.
Each history series requires `clock`, `unit`, and either `start`, `step`, `values` or timestamped `points`.
A savegame writer may omit a `kind: storage` history series when every recorded value is zero. This is lossy: an
omitted series remains unknown under the general absence rule; readers must not infer historical zero from its absence.
Other tools preserve a provided series unchanged. A live snapshot requires `clock`, `unit` and `timestamp` (R28), and
keeps `storage: 0` when zero is the known latest value.

## Validation and fixture scope

`fixtures/MANIFEST.json` distinguishes envelope rejection, schema errors and semantic defects. Island-id and
item-instance uniqueness are semantic checks outside JSON Schema. Duplicate item instances are writer defects;
reader recovery preserves the records and reports the defect, as specified in `conversion-rules.md`.
Schema validation proves structure, not consumer behavior. The fixture runner checks validity and manifest coverage;
the pytest suite also checks rename/deletion pairs. Consumer suites must check passthrough, conversion and derived
results. Trade derivation expectations remain candidates until LD9 is settled.

## Area key layout

`areaKey = (areaIndex << 13) | (islandId << 6) | regionCode`

`regionCode` occupies the low 6 bits (1 Latium, 3 Albion, 4 Aegyptus), `islandId` the next 7 bits (bits 6 to 12), `areaIndex`
the bits from 13 up. Example: area index 1, island id 5, Latium: `8192 + 320 + 1 = 8513`. A reader compares games by the
triple `{sessionGuid, islandId, areaIndex}`; `areaKey` is derived and redundant. A region code other than 1, 3 and 4 is valid
(later game versions).

## Coordinate system

Positions are in game tile units: `{x, z}` on the ground plane, optional `height`. `rotation` is in radians and an absent
rotation means 0. A writer states a position only when it knows it.

## Item locations (R25, R56)

An item record is `{item: GUID, instance?, slot?, count?, boosted?, boostConditionMet?, mythicEffect?: effect GUID, ext?}`,
each field only when the writer knows it. A record without `instance` stands for `count` (default 1) items of that GUID.
The place of a record is its location in the file; an instance appears in exactly one place and its id is unique in the
file. The same item GUID may appear in any number of records. Fields of the save that no key names (`EffectID`, `QuestID`)
go to the record's `ext.<generator>`.

| Place in the save | Key |
|---|---|
| Socket container of a building (officium, villa, hippodrome, military camp) | `islands[].itemHolders[].items`; the holder carries `guid`, `instance`, `position`, `rotation`, `enabledSockets`; a camp with free sockets is a holder with no items |
| Socket container of a ship | `itemHolders[]` with `kind: "ship"`, `route` (route id), `items` (captain and equipped items) |
| Item slots (stack kind 2) of a ship | `itemHolders[].carried` |
| `AreaItemManager/AreaSlotContainer` | `islands[].itemStorage`; one stack can hold several instances of one GUID, which share a `slot`; a `count` record stands for a stack without instance ids |
| `MetaItemTransfer/GlobalItemContainer` | `account.items` |
| `MetaItemTransfer/MetaItems` | `account.transferItems` (GUIDs only) |
| `MythicEffectsVector` | `mythicEffect` on the socketed item |
| `MetaParticipant/ItemRacerAttributes` | `account.racers`, `account.race` |
| An item no container or socket references | `unlocatedItems` |

Items of other participants, trader offers and quest rewards are not the player's items and are not recorded.
`UniqueItemExists` is derivable and has no key. Uniqueness of `instance` is checked outside the JSON Schema (class
`semantic` in `fixtures/MANIFEST.json`). Possession is not application: item records say where an item is, the
`factories[].items` choice says what a plan applies. A reader never derives one from the other.

## Trade

`trade.routes[]`: `id`, `name`, `manual`, `stations[]` in circuit order (the file order is the order), `ships[]`
`{type, slots, count, modules}`. A station has `island` (absent on a non-player area), `slots[]`
`{product, mode: load|unload, slot, amount}` (a stop that does both has slots of both modes; `amount` is a stored
quantity, never assumed to be a full slot) and `ext`.

`trade.imports[]`: `{island, product, amount?, basis?, suppliers[]}`. `basis` is planned, measured or entered. A supplier is
`{island}` or `{governor}` with `share?`, `amount?` (a minimum the user entered, t/min) and `default?` (the residual
supplier of R54). When `routes`, `imports` and `visits` disagree, `imports` is the plan input; `routes` is configuration
and a reader may derive imports from it only when `imports` is absent; `visits` never override either (R49). A writer that
writes `routes` also writes `imports` for every flow it derives.

### Residual supplier (R54)

For a receiving island and product: the supplier flagged `default` is the residual supplier; with no flag and at least
one `share`, the island supplier with the largest share (ties: lexically smallest island id); with neither there is none.
More than one flagged default is ambiguous: the reader reports it and keeps the source data. Other suppliers are ordinary
routes with their entered `amount` (zero when none was entered).

### Candidate trade derivation (R37, R51; release gate LD9)

The following candidate describes the synthetic trade fixtures. It is not a settled reference derivation:
R32/R37 call for visit-frequency weights, while this candidate substitutes ship counts and prefers matching slot indices.
LD9 must settle multi-source and relay attribution, the missing-history fallback and accuracy before a release tag.
The calculator and planner consume `imports` and do not implement this derivation in version 1.
The result is an estimate
(`basis: "planned"`); roles are reliable, shares are not. Readers that model imports take the supplier set from the
topology and compute amounts from their own demand and local supply (demand minus the output of fully utilized local
production); they never take an amount from a share.

1. A route without ships (`ships` empty or all counts 0) moves no goods and gets no entry.
2. Per product, a station is a source when it has a load slot of the product and no unload slot of it on the route; a
   station with an unload slot of the product is a sink. A station that loads and unloads the same product is a relay:
   it is a sink and never a supplier (relay stops pass nothing on). When the recorded visits of a relay name no net amount of the product
   (zero nets are absent), the relay is a pure relay and gets no entry. A station without island id (non-player area) is dropped
   as sink and as source; a route with only such stations has no flow.
3. Every unload slot is served by the nearest preceding source in circuit order, wrapping around the circuit. A source that
   loads the same slot index is preferred over one that does not. With no source for the product, the slot is unserved and no entry exists.
   A sink visited twice in one lap is evaluated per visit; several loaders feeding one unload slot are approximated by this nearest-preceding attribution.
4. The weight of a (sink, supplier) pair is the sum of the unload slot amounts it serves, multiplied by the ship count of
   the route (the stand-in for visits per time, which the file does not carry). Across all routes and visits that serve the
   same island and product, the share of a supplier is its weight divided by the sum of weights. One entry per island and product.
5. Roles that cannot be read from slot modes (every stop of a route both loads and unloads a good) come from the signs of the
   recorded net amounts: a station with a positive net of the product is a sink, a station with a negative net is a source.
Tool-specific supplier mappings are in [conversion-rules.md](conversion-rules.md). Measured errors and their
workload belong to [the trade analysis](../docs/analysis/derived-trade-flow-accuracy/analysis.md); they do not validate
this candidate.

The draft cases of R35 are `fixtures/valid/trade-*.json`; each holds routes and candidate `trade.imports` outputs, pending LD9:
point to point, distribution circuit with relays (AE13), relay net zero, manual one-slot route, distribution across
sessions, multi-source collection, non-player station, same sink twice, loaded never unloaded, bidirectional circuit,
shared supply, no ships.

## Construction materials (R50)

The end factory of a construction material is the factory whose `built` count with `fullyUtilize` on is the material's
count. The Sawmill (Timber) has one GUID per region: 3089 Latium, 5945 Albion, 152803 Aegyptus. The full list of the 13
materials and their end factories per region is part of the `materials` convention of the planner and the calculator's
`associatedRegions` data. An absent `fullyUtilize` on a construction-material factory or a module building means on;
writers state it explicitly. Example (AE21): Cinis, 4 sawmills (3089), each 2 t/min from a 30 s cycle, require 8 t/min of
Wood (2077) (`fixtures/valid/cinis-sawmill.json`).

## Versions

`formatVersion` is `major.minor`. Minor revisions only add optional keys and may extend value sets that the schema leaves open. A major revision may change meaning. This document describes 1.0.
