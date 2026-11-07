# Roadmap

What remains, per repo. Requirement IDs refer to `docs/spec/exchange-format-requirements.md`, which holds the
detail and acceptance examples (AE1-AE22).

## Specification repo (new, `anno-117-exchange-format`)

- JSON Schema (draft 2020-12) for the envelope and all catalog keys; no closed lists for regions, building kinds,
  effect kinds, source kinds or DLC names (R19).
- Specification text: key catalog with scope, type, writers and placement (core / core-optional / extension), area key
  layout, coordinate system, conversion rules, the reference trade-flow derivation (R37, R51).
- Conformance fixtures shared by all implementations (R20, R35): minimal file, unknown generator, newer minor
  version, preserved unknown fields, deletion and rename of islands, unknown region/building/effect GUIDs, trade
  constellations, construction materials (4 sawmills on Cinis).
- Release tags per format version; the other repos vendor schema and fixtures at a tag and check the copy.

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
- Suppliers: `{island}` and `{governor}`; degrade unsupported suppliers and report (R46, R52).
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
  minimum amounts for several suppliers.
- Preserve everything unknown in `ext.calculator` and the document-level unknown fields (R13, R38).

## Layout tool / savegame writer

- Make `tools/savegame_to_planner` write the exchange format instead of the planner's plan file (R29, R36).
- Items per villa/officium with position (R25), applied effects with share and method (R26), harbour and fleet
  (R40, R42), history from `EconomyStatisticManager` and storage trends (R28), `source` block (R22).
- Validate more islands for the street-distance rule (only one island so far).

## Open questions

- Game routes -> calculator routes beyond the reference derivation: relay stops and order-dependent routes
  (several loaders feeding one unload slot, same sink visited twice), the demand value the calculators supply for
  "covers everything" (the only item deferred to planning in the requirements).
- Rework the updated calculator config so local producers are fully utilized and the rest is imported (R51); the
  current file uses ordinary routes with measured minimums for 35 such entries.
- Latium and Albion campaign maps have no planner template: decide how the planner shows distances for them.
- Meaning of the `VanishGoods` marker; spacing and order of the storage-trend buffer; whether generation and
  consumption are per minute.
- Whether a hand-checked in-game list of buildings reached by a second street-distance effect agrees.
- License of this repo and of the shared specification.
