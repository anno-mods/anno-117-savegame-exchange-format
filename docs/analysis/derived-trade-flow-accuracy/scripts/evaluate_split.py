"""Compare derived trade shares with the recorded ones (the accuracy test of analysis.md).

Test A  sink split inside one route: one pure source, two or more receivers (pure sinks or relays) of a product.
Test B  supplier split at an island: one island and product supplied by two or more different source islands
        (each through a route with exactly one pure source for that product).
Test C  loader split inside one route: two or more pure sources of a product (first-loader rule).

Algorithms (shares sum to 1):
  weight_amount  visits x unload amount of the station (sum of the Amounts of its unload slots)
  weight_50      the same with every slot assumed to hold 50 t (shows the effect of the Amount correction)
  slots_only     unload amount only, no visit counts (what the configuration alone gives)
  equal          1 / n
  cascade        (A) a ship carries the source's load amount per lap and each stop in route order takes
                 min(its unload amount, what is left)
  calc_largest / calc_smallest  (B) calculator style: every supplier except one gets a fixed amount (its capacity
                 rate, capped at the measured total demand); the default supplier (largest or smallest capacity)
                 takes the remainder. calc_best_default is the better of the two choices per case (the default picked with hindsight).
Error = total variation distance to the measured shares (half the sum of absolute differences, 0 = identical, 1 = disjoint).

Inputs: --work (extract_trade.py output). Output: results/split_cases.csv and a summary on stdout.
"""

import collections
import statistics

from common import Names, Tables, arg_parser, measured, require, roles, total_variation, write_csv

MIN_TONS = 100  # a case needs at least this many measured tons, otherwise shares are noise


def pct(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(len(ordered) * q))]


def normalise(weights):
    total = sum(weights)
    return [w / total for w in weights] if total else [1 / len(weights)] * len(weights)


def cascade_shares(order_caps, supply):
    left = supply
    taken = []
    for cap in order_caps:
        t = min(cap, left)
        taken.append(t)
        left -= t
    return normalise(taken) if sum(taken) else [1 / len(taken)] * len(taken)


def summarise(title, rows, algos):
    print("%s  n=%d" % (title, len(rows)))
    for algo in algos:
        vals = [r[algo] for r in rows if r.get(algo) is not None]
        if vals:
            print("   %-14s mean %.2f  median %.2f  p90 %.2f  (n=%d)" % (algo, statistics.mean(vals), statistics.median(vals), pct(vals, 0.9), len(vals)))


def main():
    args = arg_parser(__doc__.splitlines()[0]).parse_args()
    tables = Tables(require(args.work, "--work / ANNO_TRADE_WORK"))
    names = Names()
    net, times, window = measured(tables)
    t_end = max(v["t"] for v in tables.player_visits)
    csv_rows = []

    def add_case(test, ref, name, product, n, group, errors, truth):
        shares = ' '.join('%.2f' % x for x in truth)
        for algo, err in errors.items():
            if algo not in ('group', 'n_recv', 'differs'):
                csv_rows.append([test, ref, name, product, n, group, algo, '%.3f' % err, shares])

    # ---- Test A
    rows_a = []
    for rid, route in sorted(tables.player_routes.items()):
        rl = roles(route)
        order = [s["area"] for s in route["stations"]]
        for product in sorted(set(p for p, _a in rl)):
            srcs = [a for (p, a), x in rl.items() if p == product and x[0] == "src"]
            if len(srcs) != 1:
                continue
            src_pos = order.index(srcs[0])
            # receivers in travel order starting after the source (routes are cyclic: the ship returns to the first station)
            recv = sorted((a for a in order if (product, a) in rl and rl[(product, a)][0] in ("snk", "rel")),
                          key=lambda a: (order.index(a) - src_pos) % len(order))
            if len(srcs) != 1 or len(recv) < 2:
                continue
            got = [max(0, net.get((rid, a, product), [0])[0]) for a in recv]
            if sum(got) < MIN_TONS:
                continue
            visits = [len(times.get((rid, a), ())) for a in recv]
            unload_amt = [rl[(product, a)][4] for a in recv]
            unload_slots = [rl[(product, a)][2] for a in recv]
            supply = rl[(product, srcs[0])][3]
            truth = normalise(got)
            pred = {
                "weight_amount": normalise([v * x for v, x in zip(visits, unload_amt)]),
                "weight_50": normalise([v * s * 50 for v, s in zip(visits, unload_slots)]),
                "slots_only": normalise(unload_amt),
                "equal": [1 / len(recv)] * len(recv),
                "cascade": cascade_shares(unload_amt, supply),
            }
            row = {k: total_variation(v, truth) for k, v in pred.items()}
            row.update(group="circuit with relay" if any(rl[(product, a)][0] == "rel" for a in recv) else "pure sinks",
                       n_recv=len(recv), differs=any(rl[(product, a)][4] != rl[(product, a)][2] * 50 for a in recv))
            rows_a.append(row)
            add_case("A", rid, route["name"], names(product), len(recv), row["group"], {k: row[k] for k in pred}, truth)
    algos_a = ["weight_amount", "weight_50", "slots_only", "equal", "cascade"]
    print("== Test A: sink split inside a route (cases with >= %d t measured)" % MIN_TONS)
    summarise("all", rows_a, algos_a)
    for group in ("pure sinks", "circuit with relay"):
        summarise(group, [r for r in rows_a if r["group"] == group], algos_a)
    for lo, hi in ((2, 2), (3, 4), (5, 99)):
        summarise("%d..%d receivers" % (lo, hi), [r for r in rows_a if lo <= r["n_recv"] <= hi], algos_a)
    print("cases where an unload slot is below or above 50 t at a receiver:", sum(1 for r in rows_a if r["differs"]))

    # ---- Test B
    supply = collections.defaultdict(lambda: collections.defaultdict(list))  # (island, product) -> source -> [routes]
    for rid, route in tables.player_routes.items():
        rl = roles(route)
        for product in set(p for p, _a in rl):
            srcs = [a for (p, a), x in rl.items() if p == product and x[0] == "src"]
            if len(srcs) != 1:
                continue
            for (p, a), x in rl.items():
                if p == product and x[0] in ("snk", "rel"):
                    supply[(a, product)][srcs[0]].append(rid)
    rows_b = []
    for (island, product), by_src in sorted(supply.items()):
        if len(by_src) < 2:
            continue
        sources = sorted(by_src)
        got, cap = [], []
        for src in sources:
            g = c = 0.0
            for rid in by_src[src]:
                span = max(1, t_end - window[rid][0])
                g += max(0, net.get((rid, island, product), [0])[0]) / span
                c += len(times.get((rid, island), ())) * roles(tables.routes[rid])[(product, island)][4] / span
            got.append(g)
            cap.append(c)
        total = sum(got)
        if total * (t_end - min(window[r][0] for rs in by_src.values() for r in rs)) < MIN_TONS:
            continue
        truth = normalise(got)
        row = {"weight_amount": total_variation(normalise(cap), truth), "equal": total_variation([1 / len(sources)] * len(sources), truth)}
        for label, pick in (("calc_largest", max), ("calc_smallest", min)):
            default = cap.index(pick(cap))
            fixed = [0.0 if j == default else min(cap[j], total) for j in range(len(sources))]
            fixed[default] = max(0.0, total - sum(fixed))
            row[label] = total_variation(normalise(fixed), truth)
        row["calc_best_default"] = min(row["calc_largest"], row["calc_smallest"])
        rows_b.append(row)
        add_case("B", "island %d routes %s" % (island, "+".join(str(r) for rs in by_src.values() for r in rs)), "%d suppliers" % len(sources),
                 names(product), len(sources), "supplier split", row, truth)
    print("== Test B: supplier split at an island and product (>= 2 source islands)")
    summarise("all", rows_b, ["weight_amount", "equal", "calc_largest", "calc_smallest", "calc_best_default"])

    # ---- Test C
    rows_c = []
    for rid, route in sorted(tables.player_routes.items()):
        rl = roles(route)
        order = [s["area"] for s in route["stations"]]
        for product in sorted(set(p for p, _a in rl)):
            srcs = [a for a in order if (product, a) in rl and rl[(product, a)][0] == "src"]
            if len(srcs) < 2:
                continue
            got = [max(0, -net.get((rid, a, product), [0])[0]) for a in srcs]
            if sum(got) < MIN_TONS:
                continue
            load_amt = [rl[(product, a)][3] for a in srcs]
            visits = [len(times.get((rid, a), ())) for a in srcs]
            demand = sum(rl[(product, a)][4] for (p, a) in rl if p == product and rl[(p, a)][0] in ("snk", "rel"))
            truth = normalise(got)
            row = {"weight_amount": total_variation(normalise([v * x for v, x in zip(visits, load_amt)]), truth),
                   "equal": total_variation([1 / len(srcs)] * len(srcs), truth),
                   "first_loader": total_variation(cascade_shares(load_amt, demand), truth)}
            rows_c.append(row)
            add_case("C", rid, route["name"], names(product), len(srcs), "loaders", row, truth)
    print("== Test C: loader split inside a route")
    summarise("all", rows_c, ["weight_amount", "equal", "first_loader"])
    print(write_csv("split_cases.csv", ["test", "ref", "name", "product", "n", "group", "algorithm", "error", "measured_shares"], csv_rows))


if __name__ == "__main__":
    main()




