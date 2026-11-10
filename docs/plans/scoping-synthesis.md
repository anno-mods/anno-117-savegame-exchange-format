# Scoping synthesis

Scope checkpoint for the three implementation plans. The contract is
[`docs/spec/exchange-format-requirements.md`](../spec/exchange-format-requirements.md); this document states what the
plans cover, which decisions are settled, and which still need a decision.

## What the plans build

A tool-neutral exchange format with a JSON Schema, kept in its own specification repo, and three implementations:

| Plan | Repo | Owner | Status |
| --- | --- | --- | --- |
| [Calculator](calculator-implementation-plan.md) | anno-117-calculator | Nico | decided; open decisions CD3, CD4, CD6, CD7, CD10 carry recommendations (CD8 is a deferred storage change) |
| [Planner](planner-implementation-plan.md) | Taludas Planner | Taludas | proposal for Taludas to decide; open decisions PD1-PD4, PD6-PD9 |
| [Layout tool](layout-tool-implementation-plan.md) | Anno-117-Layout-Tool | Taludas | proposal for Taludas to decide; open decisions LD1-LD10 |

[calculator-plan-decisions.md](calculator-plan-decisions.md) records the reasoning and the status of each calculator decision.

The specification repo (schema, fixtures, specification text, vendoring script) is a shared prerequisite. Its work is unit U0 of
the calculator plan, which Nico owns; the fixtures and the script are used by all three tools. This repository
(`anno-117-savegame-exchange-format`) holds the requirements, the analysis and the config updater; its
`scripts/calculator_config` changes in layout units L2 and L6. Five repos change in total.

## Settled decisions

- The format is neutral, not shaped like the planner's `Plan` or the calculator's storage dump. A valid file needs the
  format marker and version, a generator name and island ids.
- Every tool preserves what it does not understand, at any level, and attaches it to its island (R13, R14, R38).
- Writers record facts and topology; readers compute amounts from their own demand and local supply (R51). The
  calculator sets a local producer fully utilized, unless the file says otherwise, and imports the rest of the demand.
- Amounts the user entered win over derived ones. Derived flows are marked as estimates.
- Suppliers a tool does not model degrade to the nearest supplier it does model, with a report and a preserved
  original (R52).
- History is carried and kept as is. The planner and the calculator do not record it.
- Disabled needs are a list; the calculator reads every other need as on (R43).
- Construction-material end factories map to the planner's end buildings per material (R50).
- The calculator reads and writes discoveries; Nile flood and obsidian gathering are specific effects per session,
  Vervactor's Plough a specific global effect (R39, R44).
- The wonder unlock uses the summed devotion over islands (R45); the planner has to change.
- Ivory Caskets to Cinis does not exist in the sample save; no change.
- The calculator may keep localStorage keys it neither reads nor writes, so every listed disabled need is written (R43).
- The layout writer derives `settings.dlcs` from the save (LD8 locates the field); without it a calculator import relies on `DLC.used`.
- A fractional devotion is truncated by the calculator at load and reported as approximated.
- License: MIT.

## Cross-plan decisions

Decisions that touch more than one plan. Each is applied in the requirements where a requirement is named, and in every plan
it names; CP11, CP15, CP19 and CP20 are plan-level decisions with no requirement.

| ID | Decision | Where it is applied |
| --- | --- | --- |
| CP1 | One residence building exists per population level, so a per-level count maps to that building when the file has no per-building count; with both present, per-building wins. The planner writes per-level counts only. | Key Decision on residences; R24; calculator U5; planner P4, P7 |
| CP2 | Residual-supplier contract (R54): the supplier flagged `default` is residual; with no flag and at least one `share`, the largest share (ties: lexically smallest island id); with neither, there is no residual supplier (planner: remainder to trade; calculator: default supplier left as it is). Calculator: the residual is the default route; planner: `-1`. A governor is residual only when flagged `default` (planner: `-1` on its key; calculator: preserved, not applied, default supplier left as it is). | R37, R54; calculator KTD9, U6; planner P5; layout L6 |
| CP3 | A supplier `amount` is a minimum the user entered. In the calculator it is the floor `userSetAmount`, also on the default route; a zero-minimum ordinary route is exported as a supplier without `amount`. The planner writes `amount` only above 0. A writer never writes a supplier-level `amount` it derived. | Catalog row `trade.imports[]`; calculator U6, U9; planner P7; layout L6 |
| CP4 | Governor harbours are preserved by the calculator and not applied; the planner models them. Non-player islands become passive trade in the calculator and trader purchases in the planner. A preserved degraded supplier is restored only while the product's supplier is unchanged (calculator CD10). | R46, R52; calculator U6, U9; planner P5 |
| CP5 | A reader may derive imports from `trade.routes` when `imports` is absent; the calculator and the planner do not in version 1 and report the routes as preserved. A writer that writes `routes` writes `imports` for every flow it derives. | R49; calculator U6; planner P5; layout L6 |
| CP6 | Materials off in the planner are written as `fullyUtilize: false` on the end factory with `built` equal to `existing`. | R50; planner P4, P7 |
| CP7 | Preserved document-level entries that name a deleted island lose the parts that name it, including supplier references in `trade.imports`. | R14; calculator KTD15; planner PD7 |
| CP8 | Conflicting representations in one file (volcano settings versus the volcano effects, seasons, `research` versus specific effects): each reader uses the representation its model carries and reports differences; conformance fixtures expect only a report. | Calculator CD7; planner P6; conversion rules in the spec repo |
| CP9 | Shared readers and the trade derivation live in the layout repo; `scripts/calculator_config` in `anno-117-savegame-exchange-format` imports them (it already imports the layout repo through `ANNO_LAYOUT_REPO`); the analysis scripts keep their own XML helper unless LD7 moves them. | Layout L2, L6, LD7 |
| CP10 | Device preferences (language, dark mode) survive a calculator import. | R5; calculator U8, U10 |
| CP11 | No writer writes an export timestamp; round trips compare parsed documents, excluding `generator.version`, `source` and `computed`. | Calculator U9; planner P7 |
| CP12 | Five of the eleven patron wonders are effects and are exchanged in `effects.global` at scale 1 when the patron's summed devotion reaches 4000: Ceres effect 43620 (Vervactor's Plough), Cernunnos 50262, Neptune 137876, Minerva 95709, Thoth 153864 (these are effect GUIDs, not devotion values). The other six are unlocks and are not exchanged. The planner strips the five GUIDs on import. | Conversion rules; planner PD1, P6, P7 |
| CP13 | `fullyUtilize` is on by default for construction-material end factories and for module buildings in the calculator; the calculator exporter writes it explicitly for both. | Catalog row `buildings`; R50; calculator KTD13 |
| CP14 | Module attachments (R55) are preserved exactly; type-level `modules` is a majority projection that is reported, and an edited type-level flag drops that type's attachments. | R55, AE25; calculator KTD14; planner KTD10; layout L5 |
| CP15 | One vendoring script (`scripts/vendor.py`) in the specification repo writes and checks the pinned copy in each consumer; each consumer's conformance test validates and imports the manifest in one pass. | Calculator U0, U1; planner P0; layout L1 |
| CP16 | Route stations may carry `ext.<generator>` (R11); the layout writer puts `VanishGoods`, `StationID`, `HasTradeRights` and `TargetStationID` there. The extension id is independent of `generator.name`. | R11; layout KTD7, L6 |
| CP17 | Every writer that models needs writes `disabledNeeds` per island, an empty object when nothing is disabled. | R43; calculator KTD8; planner P7; layout L3 |
| CP18 | With `fertilitiesComplete` true an absent fertility is missing; without the flag the calculator applies its own default and the planner reads it as not missing. | R23; calculator U5; planner P4 |
| CP19 | Fields of the planner's `ext["raw"]` (the preserved record) and `ext["planner"]` (planner-owned bookkeeping) are separate, so a foreign key never collides with a planner key. | Planner KTD2 |
| CP20 | A write to a modelled entry replaces only the modelled fields; sibling fields (`planned`, `fullyUtilize`, `notes`, unknown sub-fields) stay as preserved, except the region's end factory of each material, where the planner writes `built` and `fullyUtilize` (R50, CP6). | Planner KTD3; calculator U9 |

## Spec changes made while planning

For review by Nico; each follows from a conflict found between requirements, between a requirement and a plan, or between a
plan and the code.

- Goal Capsule: the open blocker is the reference derivation rule (LD9), not the calculator route mapping.
- R3: four report lists (not mapped, carried through, approximated, not provided); the calculator shows them with its confirmation and after an export that dropped preserved data.
- R11: extension blocks at route-station scope; the extension id is independent of `generator.name`.
- R14: supplier references in `trade.imports` and route stations lose the parts that name a deleted island.
- R23: completeness flag semantics (CP18).
- R24: the per-level count maps to the residence building for readers that model per-building counts (CP1).
- R27: a station on a non-player area has no island id.
- R37: calculator and planner sentences follow R54 and R51; non-player legs are dropped from a derived flow and non-player
  suppliers in `imports` degrade by R52; a local producer is fully utilized unless the file says `fullyUtilize: false`; the accuracy
  figures are marked as measured with the analysis rule.
- R43: every writer writes `disabledNeeds` per island (CP17).
- R46: governor suppliers appear in `imports` only; route stations name islands.
- R49: "may derive"; a writer that writes `routes` writes `imports` (CP5).
- R50: off state of materials (CP6); `constructed` (exchange key `built`); module buildings default on (CP13).
- R53: the writer is the config updater in this repository.
- R54: residual-supplier rules (CP2): flag, share fallback, no residual when neither exists; entered `amount` on the default
  route; flag named `default`.
- R55 and AE25: the drop rule after a type-level edit (CP14).
- Key Decisions: absence rule exceptions (R43, R50); Vervactor's Plough spelling; five repos.
- AE8: rewritten for a replacing import.
- Catalog: `trade.imports[]` supplier fields and the meaning of `amount` and `basis`; `trade.routes[]`, `appliedEffects[]`, `live` and
  `materials` writers; `factories[].aqueduct` from the savegame; `research.basis`; `ext.planner` rows; the `gameIsland` field names.
- Outstanding Questions: the derivation rule (LD9); target tools do not derive.
- Edits to R52 (calculator preserves governors) and the new R54 and R55 were made outside this planning round.

## Considered and not adopted

- One import unit per tool instead of three (calculator U5-U7, planner P4-P6): the units are separate to keep each reviewable;
  the planner puts them in one module and the calculator assembles them in `plan.ts`.
- Folding the computed-block units (calculator U11, planner P10) into export and report units: both stay separate because R17 is
  optional for the planner and ships last in the calculator.
- A single conversion table: `spec/conversion-rules.md` in the specification repo is authoritative; the mapping tables in the
  plans are summaries for the implementer of each tool and follow it.
- Shared expected-outcome blocks in the manifest: left as an option for U0; the units keep their own scenarios.

## Not in scope

- Reading old-format calculator configs in the planner; merging islands into an open plan.
- Showing imported history in the tools' interfaces; deriving information from history.
- The content of `layout`; an irrigation field; savegame parsing inside the planner or calculator.

## Trade-offs

- A shared format costs work in five repos and buys a contract that survives changes on either side.
- Passthrough makes plan files hold data a tool does not interpret.
- Derived flow shares are estimates (mean error 0.23 against recorded flows with the analysis rule, equal split 0.39); amounts
  therefore come from the reader's own model, not from the writer.

## Defaults chosen without a decision, for review

1. `computed` holds residents per population level, buildings required per factory type and import per good, with a
   tolerance of 1 % or 0.1 units, whichever is larger.
2. The planner writes its `materials` count as the `built` count of the region's end factory with `fullyUtilize` on and reads
   it back the same way (R50); `planned` is a persisted calculator field that drives no result and is carried one to one.
3. Recorded visits include other traders, each with a trader id.
4. The specification repo is named `anno-117-exchange-format`; the other repos vendor a copy of schema and fixtures at
   a tag with its `vendor.py`.
5. Storage-trend buffers are written only when a writer has verified their time axis (version 1 carries the period
   snapshots).
6. Planner-only fields without a neutral meaning live in `ext.planner` (passive trade, shipping, ship templates, governor
   names, map detour, plan version, live-link modes).
7. The street-distance rule of the savegame script is validated on one island only.

## Open items

- The reference derivation rule (layout decision LD9). R37 and R32 say every source feeds every sink and the first loader
  serves first; the existing code gives each sink one supplier, the nearest preceding source. The rule, the fixtures and the
  accuracy figures in R37 (0.23, 0.27, 0.18) are settled before the specification tag.
- Latium and Albion campaign maps have no planner template; the planner shows no distances for them until Taludas
  decides how to handle them.
- Decisions CD3, CD4, CD6, CD7, CD10, PD1-PD4, PD6-PD9 and LD1-LD10 in the three plans.
