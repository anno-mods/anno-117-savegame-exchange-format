# Conversion rules

The tools model some discoveries and settings differently. Each rule below says what a reader of the format does
(R39, R44). "Calculator" and "planner" name the two tools; a third-party tool follows the Rule column.

| Case | Calculator | Planner | Rule |
|---|---|---|---|
| Plain discoveries (15 with production effects) | global effect scale 0 or 1 | discovery in the tech list | import: a scale above 0 puts the discovery in `research.researched`; export: a researched discovery writes scale 1 for each of its effects |
| Repeatable discovery (Beneath Bedrock, 37870) | scale equals the repeat count | discovery plus repeat count | `research.counts[guid]` equals scale; scale 0 when not researched |
| Volcanic soil level and unlocks (Obsidian Gathering 145095, Obsidian Mining 148043, Fertile Soil 145099) | the same scale on each unlocked effect, in the Latium and the Meta session | one level and a list of unlocked effects | level is the largest scale; unlocked effects are those above 0; differing values are reported; export writes the level to each unlocked effect and 0 to the others, in both sessions; eruption phases and durations stay in `settings.volcano` |
| Volcano settings and volcano effects disagree (CD7) | reads and applies the effects in `effects.bySession` | reads `settings.volcano` | each reader uses its own model: the calculator applies the effects, the planner applies `settings.volcano`; neither overwrites the other's block; the reader reports the disagreement and preserves both |
| Nile flood harvest effect (155616) | scale 1 in the Aegyptus session, effect values adjusted to the season average | seasons enabled, phase, unlocks | a scale above 0 enables seasons in average mode; export writes 1 when seasons are enabled in average mode; a planner phase setting (one season only) has no calculator value and is reported; the unlocks stay in `settings.seasons` |
| Wonder effects derived from devotion (Vervactor's Plough 43620, Arboreal Rhizome, other patron wonders) | global effect 1 | derived from the sum of the patron's devotion over all islands reaching the threshold (4000) | exchanged as specific effects in `effects.global`; the planner derives them from the summed devotion and ignores the stored value; the calculator value is informational; a disagreement goes into the report |
| Area buffs (four fertility grants of discoveries: Mackerel Hauling, Vino Veritas, Blood of Terra, Ulex & Agogae) | a 0 or 1 scale `<buff GUID>.scaling` with no control in the interface | fertility derived from the discovery | derived from `research`; the stored area-buff scale is ignored and kept verbatim in `ext.calculator`; whether an island has a fertility belongs to `fertilities` |
| Fertility effects of other effects (Open Sesame, Mature Trees) | ordinary effect scale | none or derived | specific effects in `effects.global` |
| Patron local effects | island effect scales recomputed from patron and devotion | patron and devotion | only patron and devotion are exchanged, as entered and without rounding |
| Wonder splendour rewards (Hippodrome, Colosseum) | island effect 0 or 1 per reward | rank 0 to 10 and coverage | set rewards give a lower bound for the rank; a rank sets the rewards up to it; coverage has no calculator value |
| Building, mythical-item and other calculator-only effects | island or global effect scale | none | kept as specific effects (R38) |
| Dominant patron | none | dominant patron | `dominantPatron`, preserved by the calculator |
| Need consumption difficulty | option id | difficulty option id | same ids, `settings.difficulty.needConsumption` |
| Discoveries without a calculator counterpart | none | in the tech list | `research` only, preserved by the calculator |
| "All Islands" aggregate (Meta session) | its own store | none | stays in `ext.calculator`; never imported as an island |
| `research.basis` (R44) | the calculator's Plan and Master view modes set global effects on; Master also sets volcano effects to level 5 and Nile flood on, so its scales are partly an all-on default; it writes `"applied"` in every view mode | writes `"researched"` | a reader treats `"applied"` values as settings and not as researched state; the savegame writer and the planner write `"researched"`; absent means researched |
| Specific effect and `research` entry for the same discovery (R39) | uses the specific effect | uses the specific effect | the specific effect (`effects.global` or `effects.bySession`) wins |
| DLC switched on later | needs of a DLC that is off are kept; a stored "0" applies when it is switched on | n/a | a need not in `disabledNeeds` is on, including needs of a DLC newly switched on (R43, AE22) |
| Per-level and per-building residences (R24) | per building | per population level | both present: per-building wins and the difference is reported; per-level only: a reader that models per-building counts maps it to the level's residence building |

## Item rules (KTD16)

- Item records (`itemHolders[].items`, `itemHolders[].carried`, `itemStorage`, `account.*`, `unlocatedItems`) are preserved
  verbatim by readers that do not model them and written back to their original places. The report counts the records per place.
- Possession is not application: a reader never derives `factories[f].items` from item records and never derives item
  records from `factories[f].items`.
- The one effect a reader may apply from item records: for each socketed item of a building holder (`kind` absent or `building`)
  whose record carries `mythicEffect: E` and `boostConditionMet: true`, island effect `E` has scale 1. Every other effect
  of the same island that the reader knows to be a mythical-item effect is 0; unrelated effects are left alone. An entry
  `islands[].effects[E]` sets the same effect and the larger value wins. A ship holder's `mythicEffect` is preserved and
  reported as not applied. An unknown effect GUID is kept in the record and reported (R38).
- `factories[f].items` as numbers in a tool with scales: listed item 1; boosted item with a boost buff 2; boosted on an
  item without a boost buff is written 1 and reported as approximated; a stored 0 is not listed (R48).
- A duplicate `instance` across the file is a defect of the writer: a reader reports it, still preserves every record, and
  does not repair it.
- Preserved item records of a deleted island go with that island (R14); `account.*` and `unlocatedItems` name no island and are never pruned.

## Module attachments (R55)

`moduleAttachments` identifies exact owner and module instances; it is not a range effect. A reader with only a
type-level module flag may project attachments by strict majority, reports that projection, and preserves the exact
records. After a user edits that factory type's flag, export drops that type's attachments and writes the edit to
`factories[guid].modules`, reporting the dropped records. Other factory types' attachments stay unchanged.

## Suppliers (R52, R54)

Readers use `trade.imports` as plan input. With one `default: true` supplier, that supplier is residual. Otherwise,
among island suppliers with a share, the largest share wins, breaking ties by lexically smallest island id.
With neither flag nor island share there is no residual. Multiple defaults are reported and preserved without inventing a split.

The calculator maps an island residual to its default route, with the supplier's entered `amount` as its minimum
(zero when absent). The planner writes other island suppliers first with their entered amount or zero, and the residual
last with `-1` (everything). No entered amount is calculated from a share. Without a residual, the planner sends the
remainder to trade and the calculator leaves its product default supplier unchanged.

A governor can be residual only through `default: true`. The planner uses `-1` on its governor key; the calculator
preserves governor suppliers without applying them or changing its default supplier, and reports that limitation.
Calculator default-route cycles are reported and preserved. Fixed minima can exceed demand in the calculator;
the planner caps deliveries at demand and reports the difference while preserving the entered amounts.

The calculator can combine fully utilized local production with imports for the remaining demand, respecting an
explicit `fullyUtilize: false`. The planner cannot combine local production and `supplied_by` for one product;
it reports the limitation and preserves the source data. Neither limitation changes the file's supplier topology.

## Island identity and edits (R14, R15)

A rename changes display text and retains the island id and preserved fields. Deletion removes the island and the
parts of document-level records that reference it: route stations, receiving imports and supplier references,
visits, history, live and computed entries. Unrelated parts remain. Readers report the dropped parts.
An edit replaces the modelled value while keeping unknown sibling fields; it takes precedence over a preserved copy.
