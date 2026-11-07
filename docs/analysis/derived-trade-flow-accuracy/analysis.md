# Accuracy of the derived trade flow

## Question

A savegame stores trade routes as ordered stations with cargo slots. The calculators work with a simplified flow: "island B receives product P from island A". This document measures how well that flow, derived from the route configuration alone, matches the trades the game recorded, and which split rule is most accurate when a flow has several receivers or several suppliers.

Scripts: `docs/analysis/derived-trade-flow-accuracy/scripts/`. Result tables: `docs/analysis/derived-trade-flow-accuracy/results/`.

## Data

- Save `Marcia 69.a8s` (`SessionFileVersion` 0x50; sessions Latium 3245, Albion 6627, Aegyptus 149679), decoded with RdaConsole and FileDBReader.
- Routes: outer `MetaGameManager/SessionTradeRouteManager/RouteMap`, 191 routes, 113 owned by the player (participant 41). A station has `AreaID` (island key), `AreaOwner` and `GoodInfos`. One `GoodInfos` entry is one cargo slot: `ProductGUID`, `Amount` (configured tons), `Index` (slot number), `IsLoading` (absent = load, `00` = unload).
- Recorded trades: session `AreaInfo/None[island]/PassiveTrade/History/TradeRouteEntries/None[routeId]/None`. One entry is one visit and one good: `Trader`, `TraderShip` (ship type GUID), `ExecutionTime`, `Finalized`, `RouteID`, `TradedGoods` (`GoodGuid`, signed `GoodAmount`).
- Counts: 1605 `TradeRouteEntries` (1352 player, 253 other traders), plus 52 `PassiveTradeEntries` (unused). Player entries span game time 506,096,000 to 513,287,500 ms (119.9 min). At most 31 entries per island and route (median 3).
- Island minimum stock: `AreaInfo/None[island]/PassiveTrade/MinimumStock` (per island and product, outside the route).

### Sign convention and meaning of an amount

Script `scripts/verify_roles.py`, table `results/role_vs_sign.csv`. Source = only load slots, sink = only unload slots, relay = both, per station and product.

| Role | negative | positive | zero | no entry |
|---|---|---|---|---|
| source | 155 | 0 | 0 | 51 |
| sink | 0 | 138 | 0 | 48 |
| relay | 13 | 120 | 0 | 78 |

Negative means the island gave the good away, positive means it received it. Source and sink roles predict the sign in all 293 pairs with an entry.

An amount is the net of unload minus reload at that visit. Zero nets have no entry (555 of 3149 configured goods are absent from the visits they were configured for). Relay stops therefore show small or negative nets, and visit counts taken from entries undercount visits in which nothing moved.

Conservation per route and good (|sum of nets| / sum of |nets|): median 0.023, p90 0.225, 163 pairs. The residual is cargo in transit.

## Derivation algorithms compared

1. **Roles from slot modes.** Load and unload slot counts and summed `Amount` per station and product. Needs the stations in file order (list order is travel order and the ship returns from the last to the first stop; inferred; in 28 routes it differs from `StationID` order), the slot modes and the slot amounts.
2. **Edge rule.** Each source feeds every sink and relay of that product in the same route.
3. **First-loader rule** (several pure loaders). The first loader in travel order fills the ship, later ones add the rest.
4. **Weight rule.** share_i = visits_i x unload amount_i, normalised. Unload amount = sum of `Amount` of the unload slots. Visits = distinct `ExecutionTime` values at that island and route. Without history only the amount is used (`slots_only`). The configured amount is used, not 50 t.
5. **Equal split.** 1/n.
6. **Cascade** (rejected). The ship carries the source's load amount and each receiver after the source (cyclic order) takes min(unload amount, remainder).
7. **Calculator style.** One supplier is the default (minimum 0, takes the remainder). Every other supplier gets a fixed amount, its capacity rate (visits x unload amount / time) capped at the measured total demand. The default is the largest capacity (`calc_largest`) or the smallest (`calc_smallest`); `calc_best_default` is the better of the two.

## Method

- **Measured share.** Test A: net tons received per receiver (negatives set to 0) divided by their sum. Test B: tons per ms received from each supplier island, divided by their sum; the window per route runs from its first entry to the last entry of the save. Test C: absolute tons loaded per loader divided by their sum.
- **Error.** Total variation distance TV = 0.5 x sum |p_i - m_i| between predicted shares p and measured shares m (0 identical, 1 disjoint; a predicted 50/50 against a measured 100/0 gives 0.5).
- **Cases.** A: route and product with one pure source and two or more receivers, at least 100 t measured (52 cases). B: island and product with two or more different source islands, each through a route with one pure source, at least 100 t (12 cases). C: route and product with two or more pure loaders, at least 100 t (2 cases). Smaller cases are noise.
- **In-transit cargo** is not corrected (route 151: sinks 1428 t, source 1267 t). It moves sums and hardly shares.
- **Excluded:** stations without entries, `PassiveTradeEntries`, other traders. An island at two stops of one lap (route 66) is merged to one role and enters only Test C.

## Results

### Slots below 50 t

The player routes have 9 slots in 5 routes below 50 t and none above (`results/slot_amounts.csv`). The other 148 non-50 slots belong to other participants' routes.

| Route | Slot | Amount | Recorded per visit |
|---|---|---|---|
| 45 Porridge Jul - Cin | Olive Oil, load at 10177 | 1 t | -1.0 t (22 visits) |
| 51 Roast Beef Cud - Uxo | Roast Beef, load at 8451 | 5 t | -5.0 t (net -45) |
| 51 Roast Beef Cud - Uxo | Cloaks, load at 8451 | 10 t | -10.0 t (net -90) |
| 104 Togas Cin - Uxo | Togas, unload at 8515 | 25 t (two slots, 75 t) | +50 t |
| 53 Wine Uxo - Arg, 81 Silver Cud - Cra | Wigs 10 t, Handmirrors 1 t | | no net recorded |

Where nothing else limits the stop, the recorded quantity equals the configured one. The weight rule with configured amounts differs from the rule with an assumed 50 t per slot in 1 of 52 cases (route 104 Togas: TV 0.364 against 0.298); the means are equal to two decimals.

### Test A: split among the receivers of one source (52 cases), TV mean / median / p90

| Group | n | weight | amounts only | equal | cascade |
|---|---|---|---|---|---|
| all | 52 | 0.23 / 0.18 / 0.46 | 0.42 / 0.42 / 0.62 | 0.39 / 0.36 / 0.62 | 0.54 / 0.48 / 1.00 |
| pure sinks | 17 | 0.17 / 0.18 / 0.34 | 0.42 / 0.43 / 0.50 | 0.31 / 0.27 / 0.50 | 0.16 / 0.17 / 0.40 |
| circuit with relay | 35 | 0.25 / 0.18 / 0.50 | 0.43 / 0.40 / 0.64 | 0.43 / 0.40 / 0.64 | 0.72 / 0.76 / 1.00 |
| 2 receivers | 8 | 0.15 / 0.06 / 0.36 | 0.42 / 0.46 / 0.50 | 0.36 / 0.42 / 0.50 | 0.09 / 0.06 / 0.22 |
| 3-4 receivers | 30 | 0.25 / 0.20 / 0.55 | 0.41 / 0.42 / 0.67 | 0.36 / 0.33 / 0.67 | 0.62 / 0.71 / 1.00 |
| 5+ receivers | 14 | 0.24 / 0.19 / 0.46 | 0.46 / 0.42 / 0.60 | 0.46 / 0.42 / 0.60 | 0.62 / 0.56 / 1.00 |

The weight rule beats the equal split in every group. The gain comes from the visit counts: with equal slot amounts "amounts only" equals the equal split. The cascade fits pure-sink routes and fails in relay circuits, where it sends all supply to the first stop.

### Test B: several suppliers for one island and product (12 cases)

| Algorithm | mean | median | p90 |
|---|---|---|---|
| weight (capacity rate) | 0.21 | 0.20 | 0.30 |
| equal | 0.31 | 0.30 | 0.50 |
| calculator style, default = largest capacity | 0.18 | 0.05 | 0.47 |
| calculator style, default = smallest capacity | 0.22 | 0.01 | 0.61 |
| calculator style, default chosen with hindsight | 0.03 | 0.00 | 0.06 |

The calculator style is bimodal: close to 0 when the default is the supplier that covers the remainder, large otherwise (1.0 for 26308 Statuettes). The choice of the default supplier decides the error, and capacity does not identify it. With a hindsight choice the form represents the measured flows, so the representation suffices and its inputs are the estimates. The fixed amounts use the measured total demand, so this is a partial oracle.

Examples: 8451 Tin Ore (routes 9 and 179) measured 0.49/0.51 (equal 0.007, weight 0.045). 10177 Wine (three routes, two supplier islands) measured 0.93/0.07 (weight 0.30, equal 0.43). 8515 Wine (routes 104 and 186) measured 0.82/0.18 (weight 0.28, equal 0.32). 10177 Obsidian with four suppliers measured 0.34/0.08/0.15/0.43 (weight 0.12, equal 0.27).

### Test C: several loaders in one route (2 cases)

| Route | Measured | weight | equal | first loader |
|---|---|---|---|---|
| 66 Coal Arg - Can (8899, 8515 -> 9795) | 0.50/0.50 | 0.05 | 0.005 | 0.495 |
| 71 Clan Shields Cud - Can (Cheese) | 0.90/0.10 | 0.30 | 0.40 | 0.40 |

In route 66 the ship alternates between the loaders (-319 t and -313 t), so the first-loader rule fails.

### Route 151 Dates

Two Aba (Nile Galley, 5 slots) ships; every slot holds 50 t.

| Station | Island | Slots | Island min stock | Visits | Net | Per visit |
|---|---|---|---|---|---|---|
| 2 | 41796 | 5 load | none | 7 | -1267 t | -181 t |
| 3 | 25668 | 5 unload + 5 load (Index 0..4) | none | 8 | +480 t | +60 t |
| 4 | 8708 | 5 unload + 5 load | 50 | 8 | +352 t | +44 t |
| 5 | 8452 | 5 unload + 5 load | 100 | 8 | +400 t | +50 t |
| 6 | 26308 | 5 unload | none | 7 | +196 t | +28 t |

The source is load-only, the middle stops do both (the same slot `Index` unloads, then loads) and the last stop is unload-only. Measured receiver shares are 0.34/0.25/0.28/0.14. The weight rule (visits 8, 8, 8, 7 times 250 t) predicts 0.26/0.26/0.26/0.23, TV 0.100. The equal split has TV 0.116 and the cascade 0.664. Routes 72 and 182 (same source 41796, one Quinquireme with 6 slots each) are point to point and exact: 300 t per visit. In route 151 the ship leaves the source with 140-235 t, not 250 t.

### Where the rules fail

- **Demand-limited stops.** Median delivered per visit divided by unload amount (`results/minstock_effect.csv`): pure sinks 0.30 without a level and 0.46 with one; relays 0.07 and 0.10.
- **Leftover cargo downstream.** Route 48 Statuettes, five receivers, measured 0.52/0.43/0.04/0/0, weight TV 0.455, equal 0.555. Route 76 Fine Glass measured 0.67/0.33/0/0/0 (weight 0.175).
- **Inverse of the slot ratio.** Route 104 Togas, receivers 8515 (75 t) and 9603 (150 t) predict 1:2; measured +150 t and +65 t.
- **Manual one-slot routes** are exact where nothing limits them: route 45 moves 50 t per visit for four goods (-1050 t in 21 visits).
- **An island at two stops** (route 66): 9795 records 10 visits against 5 and 6 at the loaders; the merged role gives one sink and two loaders (Test C).
- **A sink listed before most loaders** (route 73 Resin): sink 8899 has 250 t unload capacity and received 87 t; loader 9795 (-85 t), listed after it, supplies it on the next lap; loaders 8451, 9603 and 8515 have no entries. The derivation must treat the route as a cycle.

## Findings

- **Role prediction is reliable.** All 293 source and sink pairs with an entry match the sign; relays are +120 / -13. The topology can be derived from the configuration.
- **Share prediction is approximate.** The best rule (visits x configured unload amount) has a mean TV of 0.23 (0.17 on pure sinks, 0.25 on relay circuits) against 0.39 for the equal split. A TV of 0.2 means one fifth of the tons goes to a different receiver.
- **Minimum stock level.** It is stored in `PassiveTrade/MinimumStock` per island and product, not in the route. The effect is weak: Dates at 8708 (level 50) 44 t per visit, 8452 (level 100) 50 t, 25668 (none) 60 t, 26308 (none, last stop) 28 t. Over all receiving stops: pure sinks 0.46 with a level against 0.30 without, relays 0.10 against 0.07. No cap equal to the level shows in the amounts. The game's rule, as stated by the player, is that the level reserves stock on its island: the island's production buildings ignore it, and a route that loads there takes only as much as keeps the stock at or above the level. Receiving stops are therefore not limited by it, which fits the weak effect measured here; the measurement did not look at loading stops.
- **Exchange format.** The derivation needs, per route, the stations in travel order with island; per station and product the mode, the slot count and the slot `Amount`; the ship type (cargo slots) and ship count; and the recorded visits per island and route. The estimates are the receiver shares, the tons per visit at relays and sinks, and the supplier shares (including the choice of the default supplier). Store the configuration and the visits, and mark derived flows as estimates with the rule used.

## Target models

- **Calculator** (`src/trade.ts`, `src/production.ts`, localStorage `tradeRoutes`). One entry per product with `from`, `to`, `userSetAmount` and `isDefaultSupplier`. A route supplies `max(userSetAmount, amount)`. Per island and product, `demandCalculationSubscription` subtracts the supply of all non-default suppliers from the demand and passes the remainder to the default supplier (`setDemand`). Several suppliers are therefore possible: routes with `userSetAmount` above 0 supply at least that amount, and the default supplier with minimum 0 covers the rest. Cycles for one product are rejected.
- **Planner** (`paxplanner/model/project.py`, `paxplanner/model/engine.py` `import_split`). `IslandPlan.supplied_by[product]` is an ordered mapping from supplier to t/min or -1. Each supplier takes `min(wanted, remaining)` in order, -1 takes all that remains, and the rest is bought from traders. `Plan.routes` holds ship settings per supplier-receiver pair, not per good.
- **Directly expressible:** one source to many receivers, several suppliers with fixed amounts plus one remainder supplier, point to point, multi-good routes (one edge per good).
- **Approximation:** relay circuits (the flow through a relay stop is lost), and supplier shares without a default (weights written as fixed t/min).
- **Not expressible:** travel order, mode per stop, slot amounts, visit history, and "this stop gets what earlier stops left".

## Limitations and open questions

- One save, 120 min of game time, at most 31 entries per island and route; 52, 12 and 2 cases in tests A, B and C. The numbers size the errors in this save and are not validated bounds.
- Zero nets are absent, so entry-based visit counts are lower bounds and relay weights are biased.
- Stop order and cycle closure are inferred (route 151 sequences, list order); `Waypoint` is empty everywhere. `VanishGoods` (29 stations) is undecoded.
- Test B fixed amounts use the measured total demand; the calculator derives it from consumption.
- Visit entries hold the ship type, not the ship instance.
- Open: what a relay reloads (the net hides it); whether a minimum stock level changes unload quantities (needs a controlled save); the route 73 stops without entries (not visited, or zero net).

## Reproducing

Decode the save (see `docs/analysis/derived-trade-flow-accuracy/scripts/README.md`), then from the repo root:

```
$env:ANNO_DECODED = "<folder with data_raw.xml and session_0..2.xml>"
$env:ANNO_TRADE_WORK = "<empty folder outside the repo>"
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/extract_trade.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/verify_roles.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/constellations.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/evaluate_split.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/minstock_effect.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/ship_link.py
uv run python docs/analysis/derived-trade-flow-accuracy/scripts/route_detail.py 151 72 182 --product Dates
```

Expected key lines: `TradeRouteEntries 1605 (player 1352, other traders 253)`; `slots with Amount != 50: 157 in all routes, 9 in 5 player routes`; Test A `all n=52` with weight mean 0.23 and equal mean 0.39; Test B `n=12`.
