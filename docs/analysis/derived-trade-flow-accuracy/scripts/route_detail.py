"""Print one route in detail: configuration per station, island minimum stock, recorded visits and net flow.

Usage: route_detail.py --work DIR [--product NAME] ROUTE_ID [ROUTE_ID ...]
Per station: cargo slots per product as load/unload slot counts and Amount sums, the island's minimum stock level
for the product, number of recorded visits, recorded net tons and the average per visit. Then the visit sequence of
the first 12 entries of the route (island, minutes since the first entry, net tons of the selected product).
Input: --work (extract_trade.py output). Output: stdout only.
"""

import collections

from common import Names, Tables, arg_parser, measured, require, station_modes


def main():
    parser = arg_parser(__doc__.splitlines()[0])
    parser.add_argument("--product", help="only this product (English name)")
    parser.add_argument("routes", nargs="+", type=int)
    args = parser.parse_args()
    tables = Tables(require(args.work, "--work / ANNO_TRADE_WORK"))
    names = Names()
    net, times, _window = measured(tables)
    for rid in args.routes:
        route = tables.routes[rid]
        print("== route %d %s | owner %d | ships %d | manual %s" % (rid, route["name"], route["owner"], len(route["ships_raw"] or "") // 16, route["manual"]))
        for station, per in station_modes(route):
            for product, (ls, us, la, ua) in per.items():
                if args.product and names(product) != args.product:
                    continue
                cell = net.get((rid, station["area"], product), [0, 0])
                visits = len(times.get((rid, station["area"]), ()))
                level = tables.minstock.get(station["area"], {}).get(product)
                print("  station %d area %d (session %s, owner %d): %-18s load %d slots/%d t, unload %d slots/%d t | min stock %s | visits %d, net %d t, %.1f t/visit" % (
                    station["sid"], station["area"], tables.session_of(station["area"]), station["areaOwner"], names(product),
                    ls, la, us, ua, level, visits, cell[0], cell[0] / visits if visits else 0))
        seq = sorted((v for v in tables.player_visits if v["route"] == rid), key=lambda v: v["t"])
        if seq:
            t0 = seq[0]["t"]
            print("  sequence:", [(v["island"], round((v["t"] - t0) / 60000, 1), sum(a for g, a in v["goods"] if not args.product or names(g) == args.product)) for v in seq[:12]])
        by_ship = collections.Counter(v["ship"] for v in seq)
        print("  ship types in the entries:", dict(by_ship))


if __name__ == "__main__":
    main()
