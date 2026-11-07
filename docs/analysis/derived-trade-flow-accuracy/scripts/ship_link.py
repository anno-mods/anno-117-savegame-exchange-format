"""Check the link between routes and ships.

RouteMap/None/Ships is a packed list of u64 ship ids = MetaPersistent/MetaID of ship objects. The ship object
(PropertyTradeRouteVehicle) names its route in TradeRouteID. This script verifies both directions for the player
routes, counts ships per route and ship types, and prints the ships of chosen routes.
Inputs: --work. Output: results/ship_types.csv and stdout.
"""

import collections
import json

from common import PLAYER, REPO, Tables, arg_parser, require, write_csv


def ids(raw):
    data = bytes.fromhex(raw or "")
    return [int.from_bytes(data[i:i + 8], "little") for i in range(0, len(data), 8)]


def main():
    parser = arg_parser(__doc__.splitlines()[0])
    parser.add_argument("--routes", type=int, nargs="*", default=[151, 72, 182])
    args = parser.parse_args()
    tables = Tables(require(args.work, "--work / ANNO_TRADE_WORK"))
    with open(REPO / 'paxplanner' / 'data' / 'game' / 'ships.json', encoding='utf-8') as handle:
        ship_names = {s['guid']: (s.get('loca') or {}).get('english') or s.get('name') for s in json.load(handle)['ships']}
    names = lambda guid: ship_names.get(guid, str(guid))
    mine = [s for s in tables.ships if s["owner"] == PLAYER]
    by_meta = {s["meta"]: s for s in mine}
    listed = matched = back = 0
    for rid, route in tables.player_routes.items():
        for meta in ids(route["ships_raw"]):
            listed += 1
            ship = by_meta.get(meta)
            matched += ship is not None
            back += ship is not None and ship["route"] == rid
    print("player ships %d, ships naming a route %d" % (len(mine), sum(1 for s in mine if s["route"] is not None)))
    print("route.Ships entries %d: found as ship object by MetaID %d, ship names the same route %d" % (listed, matched, back))
    print("ships per route:", sorted(collections.Counter(len(ids(r["ships_raw"])) for r in tables.player_routes.values()).items()))
    types = collections.Counter((s["guid"], s["slots"], len(s["modules"])) for s in mine)
    rows = [[g, names(g), slots, mods, n] for (g, slots, mods), n in sorted(types.items(), key=lambda kv: -kv[1])]
    print(write_csv("ship_types.csv", ["ship_guid", "name", "cargo_slots", "modules", "ships"], rows))
    for rid in args.routes:
        route = tables.routes[rid]
        print("route %d %s: ships %s" % (rid, route["name"], [(m, names(by_meta[m]["guid"]) if m in by_meta else None, by_meta[m]["slots"] if m in by_meta else None) for m in ids(route["ships_raw"])]))


if __name__ == "__main__":
    main()

