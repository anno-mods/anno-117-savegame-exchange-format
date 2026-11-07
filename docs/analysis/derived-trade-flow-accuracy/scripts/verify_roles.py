"""Verify the sign convention of recorded amounts and report data facts the analysis relies on.

Checks: entry counts (player and AI traders), entries kept per island and route, role (source / sink / relay,
derived from the slot modes) against the sign of the measured net per island and good, conservation per route and
good, configured goods missing from a visit's entry (zero nets are not written), and cargo slots whose Amount is
not 50 t.
Inputs: --work. Output: results/role_vs_sign.csv, results/slot_amounts.csv and a summary on stdout.
"""

import collections
import statistics

from common import PLAYER, Names, Tables, arg_parser, measured, require, roles, write_csv


def main():
    args = arg_parser(__doc__.splitlines()[0]).parse_args()
    tables = Tables(require(args.work, "--work / ANNO_TRADE_WORK"))
    names = Names()
    net, times, _window = measured(tables)

    route_entries = [v for v in tables.visits if v["kind"] == "TradeRouteEntries"]
    print("TradeRouteEntries %d (player %d, other traders %d); PassiveTradeEntries %d" % (
        len(route_entries), len(tables.player_visits), len(route_entries) - len(tables.player_visits),
        len(tables.visits) - len(route_entries)))
    t_all = [v["t"] for v in tables.player_visits]
    print("window of player entries (game ms): %d .. %d (%.1f min)" % (min(t_all), max(t_all), (max(t_all) - min(t_all)) / 60000))
    per = collections.Counter((v["island"], v["route"]) for v in tables.player_visits)
    print("entries per (island, route): max %d, median %d" % (max(per.values()), statistics.median(per.values())))

    counts = collections.Counter()
    for rid, route in tables.player_routes.items():
        for (product, area), (role, *_rest) in roles(route).items():
            cell = net.get((rid, area, product))
            if cell is None:
                counts[(role, "no record")] += 1
            else:
                counts[(role, "neg" if cell[0] < 0 else "pos" if cell[0] > 0 else "zero")] += 1
    write_csv("role_vs_sign.csv", ["role", "sign_of_measured_net", "pairs"], [[r, s, n] for (r, s), n in sorted(counts.items())])
    for key, n in sorted(counts.items()):
        print("role %-3s measured net %-9s %d" % (key[0], key[1], n))

    residual = []
    for rid in tables.player_routes:
        by_good = collections.defaultdict(lambda: [0, 0])
        for (r, _a, g), cell in net.items():
            if r == rid:
                by_good[g][0] += cell[0]
                by_good[g][1] += abs(cell[0])
        residual += [abs(a) / b for a, b in by_good.values() if b]
    print("conservation |sum| / sum|net| per route and good: median %.3f, p90 %.3f (n=%d)" % (
        statistics.median(residual), sorted(residual)[int(len(residual) * 0.9)], len(residual)))

    configured = missing = 0
    for rid, route in tables.player_routes.items():
        for station in route["stations"]:
            goods = set(s["p"] for s in station["goods"])
            for v in tables.player_visits:
                if v["route"] == rid and v["island"] == station["area"]:
                    configured += len(goods)
                    missing += len(goods - set(g for g, _a in v["goods"]))
    print("configured goods not present in the visit entry (net 0 or not moved): %d of %d" % (missing, configured))

    rows = []
    for rid, route in sorted(tables.routes.items()):
        for station in route["stations"]:
            for slot in station["goods"]:
                if slot["amt"] != 50:
                    rows.append([rid, route["name"], route["owner"], station["area"], names(slot["p"]),
                                 "unload" if slot["load"] == "00" else "load", slot["amt"]])
    write_csv("slot_amounts.csv", ["route", "name", "owner", "area", "product", "mode", "amount"], rows)
    player_rows = [r for r in rows if r[2] == PLAYER]
    print("slots with Amount != 50: %d in all routes, %d in %d player routes; below 50: %d, above 50: %d (player)" % (
        len(rows), len(player_rows), len(set(r[0] for r in player_rows)),
        sum(1 for r in player_rows if r[6] is not None and r[6] < 50), sum(1 for r in player_rows if r[6] is not None and r[6] > 50)))
    for r in player_rows[:6]:
        print("   ", r)


if __name__ == "__main__":
    main()
