# Roadmap

What remains, per repo. Requirement IDs refer to `docs/spec/exchange-format-requirements.md`, which holds the
detail and acceptance examples (AE1-AE25). The unit lists are in `docs/plans/calculator-implementation-plan.md` (U0-U12),
`planner-implementation-plan.md` (P0-P11) and `layout-tool-implementation-plan.md` (L1-L10); `docs/plans/scoping-synthesis.md`
holds the decisions that span them.

## Specification repo (new, `anno-117-exchange-format`)

- JSON Schema (draft 2020-12) for the envelope and all catalog keys; no closed lists for regions, building kinds,
  effect kinds, source kinds or DLC names (R19).
- Specification text: key catalog with scope, type, writers and placement (core / core-optional / extension), area key
  layout, coordinate system, conversion rules, the reference trade-flow derivation (R37, R51).
- Conformance fixtures shared by all implementations (R20, R35): minimal file, unknown generator, newer minor
  version, preserved unknown fields, deletion and rename of islands, unknown region/building/effect GUIDs, trade
  constellations, construction materials (4 sawmills on Cinis).
- One vendoring script (`scripts/vendor.py`) and release tags per format version; the other repos vendor schema and
  fixtures at a tag and check the copy.
- Settled before the first tag: the reference derivation rule (layout decision LD9) and the catalog rows the planner needs
  (planner decision PD4).

## Planner (Taludas)

- Import and export of the format in the main menu; report dialog (R1-R4).
- Replace the open plan after a confirmation (R2); reject files with a newer major version (R4).
- Passthrough: keep unknown fields at every level and attach them to their island (R13, R14, R38); `ext.planner` for
  planner-only fields (R47); edits win over carried copies (R15).
- Link plan islands to game islands by game reference (R30); move the link from app settings into the plan.
- Field destinations (R40, R41, R42, R43, R47): harbour (warehouse type, trading spots, item), map settings and
  island position, fleet (ship effects, ship configurations), disabled-needs list, island items, materials,
  public coverage default, research speed.
- Residence mapping: sum per-building counts to population levels on import, export per-level counts (R24).
- Construction materials: `materials` count <-> built count of the material's end factory with `fullyUtilize` (R50).
- Suppliers: `{island}` and `{governor}`; residual supplier contract; degrade unsupported suppliers and report (R46, R52, R54).
- Module attachments projected by majority and preserved (R55).
- Fix: derive wonder unlocks from the summed devotion of a patron over all islands (R45).
- Discoveries and settings conversion per the table in the spec (volcano level and effects, seasons, wonders,
  splendour ranks) and the basis flag "applied" vs "researched" (R39, R44).
- Optional: compare `computed` values and show differences in the report (R17).

## Calculator (Nico)

- Export/import of the format next to the current dump; stable opaque island ids; replace data after a confirmation
  (R5-R7).
- Read and write discoveries (`research`), derive scales from them; special effects Nile flood, obsidian gathering,
  Vervactor's Plough (R39, R44).
- Tri-state items and per-target effects (R48), disabled needs list, game island reference, notes.
- Local producer + import: set the local producer fully utilized and import the rest (R51); default supplier and
  minimum amounts for several suppliers (R54).
- Preserve everything unknown in `ext.calculator` and the document-level unknown fields (R13, R38); module attachments (R55).

## Layout tool / savegame writer

- Make `tools/savegame_to_planner` write the exchange format instead of the planner's plan file (R29, R36).
- Island core inputs: building counts, fertilities with completeness, patrons, disabled needs per level (R21-R24, R43).
- Items per villa/officium with position (R25), exact production module attachments (R55), applied range effects with share
  and method (R26), harbour and fleet (R40, R42), history from `EconomyStatisticManager` (R28), `source` block (R22).
- Trade: route configurations, ships, visits, minimum stock and the derived flow with its basis (R27, R32-R35, R37, R49, R51, R54).
- Validate more islands for the street-distance rule (only one island so far).

## Exchange repo (this repository)

- Config updater: rework so local producers are fully utilized and the rest is imported (R51), and apply the default-supplier
  move of R53; switch `scripts/calculator_config` to the shared savegame readers and trade derivation (layout units L2, L6).

## Open questions

- The reference derivation rule for relay stops and order-dependent routes, and the accuracy figures of the final rule
  (layout decision LD9).
- Latium and Albion campaign maps have no planner template: decide how the planner shows distances for them.
- Spacing and order of the storage-trend buffer; whether generation and consumption are per minute.
- Whether a hand-checked in-game list of buildings reached by a second street-distance effect agrees.
- A save-time field for `source.savedAt` (layout decision LD10).
