"""Extract the trade tables from a decoded savegame into small JSON files (the first script to run).

Reads   <decoded>/data_raw.xml (outer) and <decoded>/session_N.xml.
Writes  <work>/routes.json    SessionTradeRouteManager/RouteMap routes with stations and cargo slots
        <work>/visits.json    AreaInfo/.../PassiveTrade/History entries (one per visit and good)
        <work>/minstock.json  AreaInfo/.../PassiveTrade/MinimumStock per island
        <work>/areas.json     island key -> session index and owner
        <work>/ships.json     ship objects with a PropertyTradeRouteVehicle component
Nothing is written into the repo; keep <work> outside it.
"""

import json
from pathlib import Path

from common import arg_parser, require
from xmlstream import i32, stream, u


def extract_routes(outer):
    routes = {}
    for _path, node in stream(outer, lambda p: p[-1] == "RouteMap"):
        kids = node.kids
        for i in range(0, len(kids) - 1, 2):
            r = kids[i + 1]
            route = {
                "id": u(r.get("ID").text),
                "name": bytes.fromhex(r.get("Name").text).decode("utf-16-le"),
                "owner": u(r.get("Owner").text),
                "ships_raw": r.get("Ships").text,
                "manual": r.get("ManuallySaved") is not None,
                "stations": [],
            }
            for s in r.get("Stations").kids:
                station = {
                    "sid": u(s.get("StationID").text),
                    "area": u(s.get("AreaID").text),
                    "areaOwner": u(s.get("AreaOwner").text),
                    "rights": s.get("HasTradeRights") is not None,
                    "vanish": s.get("VanishGoods") is not None,
                    "goods": [],
                }
                for gi in s.get("GoodInfos").kids:
                    amount = gi.get("Amount")
                    index = gi.get("Index")
                    loading = gi.get("IsLoading")
                    station["goods"].append({
                        "p": u(gi.get("ProductGUID").text),
                        "amt": u(amount.text) if amount is not None else None,
                        "load": loading.text if loading is not None else None,
                        "idx": u(index.text) if index is not None else None,
                    })
                route["stations"].append(station)
            routes[route["id"]] = route
    return routes


def extract_sessions(work_in, count):
    visits, minstock, areas, ships = [], {}, {}, []
    for si in range(count):
        xml = str(work_in / ("session_%d.xml" % si))
        for _path, node in stream(xml, lambda p: p[-1] == "AreaInfo" and len(p) == 3):
            kids = node.kids
            for a in range(0, len(kids) - 1, 2):
                key = u(kids[a].text)
                info = kids[a + 1]
                owner = info.get("OwnerProfile")
                areas[key] = {"session": si, "owner": u(owner.text) if owner is not None else None}
                level = info.find("PassiveTrade/MinimumStock")
                if level is not None:
                    minstock[key] = {"session": si, "levels": {
                        str(u(level.kids[j].text)): u(level.kids[j + 1].text) for j in range(0, len(level.kids) - 1, 2)}}
                for kind in ("TradeRouteEntries", "PassiveTradeEntries"):
                    hist = info.find("PassiveTrade/History/" + kind)
                    if hist is None:
                        continue
                    for j in range(0, len(hist.kids) - 1, 2):
                        rid = u(hist.kids[j].text)
                        for e in hist.kids[j + 1].kids:
                            ship = e.get("TraderShip")
                            trader = e.get("Trader")
                            visits.append({
                                "session": si, "island": key, "kind": kind, "route": rid,
                                "t": u(e.get("ExecutionTime").text),
                                "ship": u(ship.text) if ship is not None else None,
                                "trader": u(trader.text) if trader is not None else None,
                                "goods": [[u(g.get("GoodGuid").text), i32(g.get("GoodAmount").text)] for g in e.get("TradedGoods").kids],
                            })
        for _path, node in stream(xml, lambda p: len(p) == 8 and p[-5].startswith("AreaManager_") and p[-3] == "GameObject"):
            vehicle = node.get("PropertyTradeRouteVehicle")
            if vehicle is None:
                continue
            meta = node.get("MetaPersistent")
            mods = node.find("ShipModuleOwner/InstalledShipModules")
            slots = node.find("ItemContainer/SlotContainer/SlotList")
            route = vehicle.get("TradeRouteID")
            station = vehicle.get("TargetStationID")
            owner = node.get("OwnerProfile")
            ships.append({
                "session": si, "guid": u(node.get("guid").text), "id": u(node.get("ID").text),
                "owner": u(owner.text) if owner is not None else 41,
                "meta": u(meta.get("MetaID").text) if meta is not None and meta.get("MetaID") is not None else None,
                "modules": [u(k.text) if k.text else None for k in mods.kids] if mods is not None else [],
                "route": u(route.text) if route is not None else None,
                "station": u(station.text) if station is not None else None,
                "slots": len(slots.kids) if slots is not None else None,
            })
    return visits, minstock, areas, ships


def main():
    parser = arg_parser("Extract trade tables from a decoded savegame.", need_decoded=True)
    parser.add_argument("--sessions", type=int, default=3, help="number of session_N.xml files")
    args = parser.parse_args()
    decoded = require(args.decoded, "--decoded / ANNO_DECODED")
    work = require(args.work, "--work / ANNO_TRADE_WORK")
    work.mkdir(parents=True, exist_ok=True)
    routes = extract_routes(str(decoded / "data_raw.xml"))
    visits, minstock, areas, ships = extract_sessions(decoded, args.sessions)
    for name, data in (("routes.json", routes), ("visits.json", visits), ("minstock.json", minstock),
                       ("areas.json", areas), ("ships.json", ships)):
        Path(work / name).write_text(json.dumps(data), encoding="utf-8")
    print("routes %d, visits %d, islands with minimum stock %d, areas %d, ships %d" % (
        len(routes), len(visits), len(minstock), len(areas), len(ships)))


if __name__ == "__main__":
    main()
