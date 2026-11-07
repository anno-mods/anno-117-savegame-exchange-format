"""Classify the 113 player routes into good-flow constellations and count them.

A route can fall into several classes. Roles come from the slot modes of each station (see common.roles):
src = only load slots, snk = only unload slots, rel = both, for one product at one station.
Inputs: --work. Output: results/constellations.csv (class, routes, example route id, example text) and stdout.
"""

import collections

from common import Names, Tables, arg_parser, measured, require, station_modes, write_csv


def ships_of(raw):
    data = bytes.fromhex(raw or "")
    return [int.from_bytes(data[i:i + 8], "little") for i in range(0, len(data), 8)]


def main():
    args = arg_parser(__doc__.splitlines()[0]).parse_args()
    tables = Tables(require(args.work, "--work / ANNO_TRADE_WORK"))
    names = Names()
    _net, times, _window = measured(tables)
    visit_total = collections.Counter(v["route"] for v in tables.player_visits)
    classes = collections.defaultdict(list)
    sink_routes = collections.defaultdict(set)

    def describe(rid):
        parts = []
        for station, per in station_modes(tables.routes[rid]):
            goods = ",".join("%s:%s %d/%d" % (names(p), "both" if e[0] and e[1] else "load" if e[0] else "unload", e[0], e[1]) for p, e in per.items())
            parts.append("%d[%s]" % (station["area"], goods))
        return "#%d %s: %s" % (rid, tables.routes[rid]["name"], " -> ".join(parts))

    for rid, route in sorted(tables.player_routes.items()):
        stations = station_modes(route)
        products = set(p for _s, per in stations for p in per)
        found = set()
        for product in products:
            src = [s["area"] for s, per in stations if product in per and per[product][0] and not per[product][1]]
            snk = [s["area"] for s, per in stations if product in per and per[product][1] and not per[product][0]]
            rel = [s["area"] for s, per in stations if product in per and per[product][0] and per[product][1]]
            loaders = [s["area"] for s, per in stations if product in per and per[product][0]]
            if rel:
                found.add("relay: a stop loads and unloads the same good")
            if len(src) == 1 and len(snk) + len(rel) == 1:
                found.add("point to point: 1 source, 1 receiver")
            if len(src) == 1 and len(snk) + len(rel) >= 2:
                found.add("distribution: 1 source, 2 or more receivers")
            if len(src) >= 2 and len(snk) + len(rel) >= 1:
                found.add("collection: 2 or more pure loaders of a good")
            if len(loaders) >= 2:
                found.add("good loaded at 2 or more stops")
            if not src and not rel:
                found.add("good unloaded but never loaded")
            if not snk and not rel:
                found.add("good loaded but never unloaded")
            for a in snk + rel:
                sink_routes[(a, product)].add(rid)
        sources = {p: frozenset(s["area"] for s, per in stations if p in per and per[p][0] and not per[p][1]) for p in products}
        if len(products) >= 2:
            found.add("multi-good")
            if len(set(sources.values())) > 1:
                found.add("multi-good with different source islands per good")
        for p in products:
            for q in products:
                if p < q:
                    for a in sources[p]:
                        for b in sources[q]:
                            at_p = [s["area"] for s, per in stations if p in per and per[p][1]]
                            at_q = [s["area"] for s, per in stations if q in per and per[q][1]]
                            if a != b and b in at_p and a in at_q:
                                found.add("bidirectional: A to B good P, B to A good Q")
        areas = [s["area"] for s, _per in stations]
        if len(set(areas)) != len(areas):
            found.add("an island appears at 2 stops of one lap")
        if any(s["areaOwner"] != 41 for s, _per in stations):
            found.add("stop at a non-player area (AreaOwner != 41)")
        if route["manual"]:
            found.add("ManuallySaved")
        if visit_total[rid] < 3:
            found.add("fewer than 3 recorded visits")
        if not ships_of(route["ships_raw"]):
            found.add("no ship assigned")
        if len(set(tables.session_of(a) for a in areas)) > 1:
            found.add("stops in several sessions")
        if len(stations) >= 3 and sum(1 for _s, per in stations if all(e[0] and not e[1] for e in per.values())) == 1 and \
                sum(1 for _s, per in stations if all(e[1] and not e[0] for e in per.values())) == len(stations) - 1:
            found.add("one load-only stop, all others unload-only")
        if [s["sid"] for s in route["stations"]] != sorted(s["sid"] for s in route["stations"]):
            found.add("list order differs from StationID order")
        if any(sl["amt"] != 50 for s in route["stations"] for sl in s["goods"] if sl["amt"] is not None):
            found.add("a cargo slot with Amount != 50")
        for label in found:
            classes[label].append(rid)
    shared = sorted((a, p, sorted(rs)) for (a, p), rs in sink_routes.items() if len(rs) >= 2)
    rows = []
    for label, rids in sorted(classes.items(), key=lambda kv: -len(kv[1])):
        pick = sorted(rids, key=lambda r: -len(tables.routes[r]["stations"]))[0]
        rows.append([label, len(rids), pick, describe(pick)[:300]])
        print("%3d  %s   e.g. %s" % (len(rids), label, describe(pick)[:160]))
    rows.append(["several routes unload the same good at one island", len(shared), "", "; ".join("%d/%s:%s" % (a, names(p), rs) for a, p, rs in shared[:6])])
    print("%3d  several routes unload the same good at one island   e.g. %s" % (len(shared), shared[:3]))
    print(write_csv("constellations.csv", ["class", "routes", "example_route", "example"], rows))


if __name__ == "__main__":
    main()

