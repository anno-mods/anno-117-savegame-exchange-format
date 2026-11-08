# Calculator plan: decisions and their status

Subject: `docs/plans/calculator-implementation-plan.md` against `docs/spec/exchange-format-requirements.md` and the calculator
source (`anno-117-calculator/src`). Each row names a decision that had to be settled for round-trip imports to work and for
the intention of a value to be clear, with the calculator evidence and where it is settled. "Open" rows are the open
decisions CD3, CD4, CD6, CD7 and CD10 of the plan; CD8 (per-product passive-trade storage) is a deferred storage change, not a decision of this plan.

## Meaning of an absent or default value in the calculator

| Key | What the calculator does when it is absent or default | Evidence | Settled in |
| --- | --- | --- | --- |
| `<level>[<need>].checked` | Reads as on: a need keeps its constructor default `checked = true`; a stored value is restored only while the need is available; a stored "0" of a DLC-locked need is applied when the DLC is switched on. The option `activateAllNeeds` is not persisted. | `consumption.ts:104`, `world.ts:296-302`, `728-750` | KTD8, R43 |
| `island.fertility.<g>.checked` | Defaults to checked, except unchecked when the fertility's regions exclude the island's region | `production.ts:738`, `world.ts:855-861` | R23, U5 |
| `<factory>.buildings.fullyUtilizeConstructed` | Off for ordinary factories, on for construction-material factories and module buildings | `factories.ts:610-611`, `factories.ts:427` | R50, KTD13, U9 |
| `<product>.defaultSupplier.type/id` | `resetDefaultSupplier()` picks the region's forced factory or passive trade; the strings "null" and "null" mean no default supplier; a trade-route default is not written (the stored type stays `factory`) | `production.ts:302-314`, `world.ts:1076-1128`, `trade.ts:316` | KTD13, mapping row `producer` |
| `<f>[<item>].scaling` | Off | R48 | R48, U5 |
| `passiveTrade.userSetAmount` | 0; one key shared by all products | `suppliers.ts:67`, `world.ts:1073` | R52, CD8 |
| `buildings.planned` | Persisted and summed, drives no result | `world.ts:722-724`, `aggregate.ts:131` | mapping row `planned` |

## A route with `userSetAmount` above 0 that is the default supplier

A route supplies `max(userSetAmount, amount)` (`trade.ts:136`). For the default route `amount` is the demand minus what the other
suppliers supply (`production.ts:291`), so `userSetAmount` is a floor under the import from that supplier and a surplus over demand
counts as excess production. The interface hides the floor input for the default route (`components.ts:266`), but the stored value
stays and is reused when the route stops being the default (`trade.ts:173-176`). The format carries it as the supplier `amount` (basis
entered), also on the default route (catalog row `trade.imports[]`, KTD9, CP3); a zero-minimum ordinary route is exported as a
supplier without `amount` (U9).

## Status of each decision

| ID | Decision | Status | Where |
| --- | --- | --- | --- |
| D0 | The exporter writes explicit choices, with named exceptions | settled | KTD13, U9 |
| D1 | Absent need key means on; `activateAllNeeds` needs no handling | settled | KTD8 |
| D2 | `disabledNeeds` written for every island; missing key reported as not provided | settled | R43, KTD8, CP17 |
| D3 | Disabled needs the calculator cannot apply | settled: written as unread localStorage keys, listed again on export | calculator plan, settled decisions |
| D4 | Default route with `userSetAmount` above 0 | settled | catalog row `trade.imports[]`, KTD9, CP3 |
| D5 | Zero-minimum ordinary routes are exported and recreated | settled | U6, U9 |
| D6 | Which supplier is the default: flag, then share, then none | settled | R54, KTD9, CP2 |
| D7 | R37 and R51 conflict on non-default minima | settled: R51 governs | R37, R54 |
| D8 | Local producer and import: file's `fullyUtilize` wins | settled | R37, KTD9 |
| D9 | `products[p].producer` and the default supplier key | settled | KTD13, mapping row `producer` |
| D10 | Governor suppliers and the shared passive-trade key | settled: preserved, not applied; per-product storage is a later change | R52, CD8 |
| D11 | R46 against R52 on governors | settled | R46, R52 |
| D12 | Restore of a preserved degraded supplier after an edit | open | CD10 |
| D13 | Absent fertility under replacement | settled | R23, AE8, U5 |
| D13a | Routes naming "All Islands" or an orphan island | settled | U6, U9 |
| D13b | Cycles and two defaults for one product | settled | U6 |
| D14 | Device preferences survive an import | settled | R5, CP10, U8 |
| D15 | `settings.dlcs` absent | settled: the layout writer derives it from the save (field located under LD8); otherwise `DLC.used` | calculator plan, settled decisions; LD8 |
| D16 | Island name after a collision suffix | open | CD3 |
| D17 | `fullyUtilize` states and the `materials` precedence | settled: `buildings` wins | KTD13, U7, U9 |
| D18 | Factory entries absent or partial | settled | U5 |
| D18a | View modes and `research.basis` | open for `effects.global` content | CD6 |
| D19 | Precedence when the same fact appears twice | open for volcano and seasons | CD7 |
| D20 | Strictness: reject, repair or keep | open | CD4 |
| D21 | Round-trip equality | settled | U9, CP11 |
| D22 | Meaning of `planned` | settled: carried one to one | mapping row `planned` |
| D23 | Fractional `devotion` is truncated at load | settled: accepted, reported as approximated | calculator plan, settled decisions |
