"""Compare delivered tons per visit at receiving stops with and without an island-level minimum stock level.

The level is AreaInfo/.../PassiveTrade/MinimumStock (island and product, not part of the route). For every receiving
stop (unload slots) with at least 3 recorded visits the ratio (recorded net tons per visit) / (unload slot amount) is
computed. Stops are grouped by relay or pure sink and by the presence of a level for the product on that island.
Also lists the Dates route stops (the case discussed in analysis.md).
Inputs: --work. Output: results/minstock_effect.csv and stdout.
"""

import collections
import statistics

from common import Names, Tables, arg_parser, measured, require, station_modes, write_csv


def main():
    parser = arg_parser(__doc__.splitlines()[0])
    parser.add_argument("--dates-routes", type=int, nargs="*", default=[151])
    args = parser.parse_args()
    tables = Tables(require(args.work, "--work / ANNO_TRADE_WORK"))
    names = Names()
    net, times, _window = measured(tables)
    groups = collections.defaultdict(list)
    for rid, route in sorted(tables.player_routes.items()):
        for station, per in station_modes(route):
            for product, (ls, us, _la, ua) in per.items():
                visits = len(times.get((rid, station["area"]), ()))
                if not us or visits < 3 or not ua:
                    continue
                level = tables.minstock.get(station["area"], {}).get(product, 0)
                tons = net.get((rid, station["area"], product), [0])[0]
                groups[("relay" if ls else "pure sink", "level > 0" if level else "no level")].append((tons / visits) / ua)
    rows = []
    for key, vals in sorted(groups.items()):
        rows.append([key[0], key[1], len(vals), "%.2f" % statistics.median(vals), "%.2f" % statistics.mean(vals)])
        print("%-9s %-9s n=%3d  median delivered per visit / unload amount %.2f (mean %.2f)" % (key[0], key[1], len(vals), statistics.median(vals), statistics.mean(vals)))
    print(write_csv("minstock_effect.csv", ["stop", "minimum_stock", "n", "median_ratio", "mean_ratio"], rows))
    for rid in args.dates_routes:
        route = tables.routes[rid]
        print("route %d %s" % (rid, route["name"]))
        for station, per in station_modes(route):
            for product, (ls, us, _la, ua) in per.items():
                visits = len(times.get((rid, station["area"]), ()))
                tons = net.get((rid, station["area"], product), [0])[0]
                print("   area %d %-6s level %s  visits %d  net %d t  per visit %.1f t  (%s)" % (
                    station["area"], "relay" if ls and us else "sink" if us else "source",
                    tables.minstock.get(station["area"], {}).get(product), visits, tons, tons / visits if visits else 0, names(product)))


if __name__ == "__main__":
    main()
