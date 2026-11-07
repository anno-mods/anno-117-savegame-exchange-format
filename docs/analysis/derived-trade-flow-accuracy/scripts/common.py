"""Shared helpers: paths, game data names, loading of the extracted trade tables, route roles and measured flows.

Folders:
  --work DIR   or environment ANNO_TRADE_WORK     extracted tables (written by extract_trade.py, read by the others)
  --decoded DIR or environment ANNO_DECODED       decoded savegame XML (data_raw.xml, session_0.xml ..)
The repo root is found from this file's location (docs/analysis/<name>/scripts), so run the scripts with the
Planner's interpreter (uv run python ...) to import paxplanner.
"""

import argparse
import collections
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
RESULTS = Path(__file__).resolve().parents[1] / "results"
PLAYER = 41  # participant id of the human player in Marcia 69


def arg_parser(description, need_decoded=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--work", default=os.environ.get("ANNO_TRADE_WORK"), help="folder with the extracted tables")
    if need_decoded:
        parser.add_argument("--decoded", default=os.environ.get("ANNO_DECODED"), help="folder with the decoded save XML")
    return parser


def require(path, what):
    if not path:
        sys.exit("missing %s (argument or environment variable, see scripts/README.md)" % what)
    return Path(path)


def game_data():
    sys.path.insert(0, str(REPO))
    from paxplanner.model.gamedata import GameData
    return GameData()


class Names:
    def __init__(self):
        self.gd = game_data()

    def __call__(self, guid):
        return self.gd.name(guid, "english")


def load(work, name):
    with open(Path(work) / name, encoding="utf-8") as handle:
        return json.load(handle)


class Tables:
    """The extracted tables with integer keys."""

    def __init__(self, work):
        self.routes = {int(k): v for k, v in load(work, "routes.json").items()}
        self.visits = load(work, "visits.json")
        self.minstock = {int(k): {int(g): a for g, a in v["levels"].items()} for k, v in load(work, "minstock.json").items()}
        self.areas = {int(k): v for k, v in load(work, "areas.json").items()}
        self.ships = load(work, "ships.json")
        self.player_visits = [v for v in self.visits if v["kind"] == "TradeRouteEntries" and v["trader"] == PLAYER]
        self.player_routes = {rid: r for rid, r in self.routes.items() if r["owner"] == PLAYER}

    def session_of(self, area):
        info = self.areas.get(area)
        return info["session"] if info else None


def station_modes(route):
    """Per station in file order: (station, {product: [load_slots, unload_slots, load_amount, unload_amount]}).

    A GoodInfos entry is one cargo slot. IsLoading absent = load, IsLoading = 00 = unload.
    """
    out = []
    for station in route["stations"]:
        per = {}
        for slot in station["goods"]:
            entry = per.setdefault(slot["p"], [0, 0, 0, 0])
            amount = slot["amt"] or 0
            if slot["load"] == "00":
                entry[1] += 1
                entry[3] += amount
            else:
                entry[0] += 1
                entry[2] += amount
        out.append((station, per))
    return out


def roles(route):
    """(product, area) -> (role, load_slots, unload_slots, load_amount, unload_amount); role is src, snk or rel."""
    out = {}
    for station, per in station_modes(route):
        for product, (ls, us, la, ua) in per.items():
            out[(product, station["area"])] = ("rel" if ls and us else ("src" if ls else "snk"), ls, us, la, ua)
    return out


def measured(tables):
    """(route, island, product) -> [net tons, entries]; (route, island) -> set of visit times; route -> [first, last]."""
    net = collections.defaultdict(lambda: [0, 0])
    times = collections.defaultdict(set)
    window = {}
    for visit in tables.player_visits:
        times[(visit["route"], visit["island"])].add(visit["t"])
        span = window.setdefault(visit["route"], [visit["t"], visit["t"]])
        span[0] = min(span[0], visit["t"])
        span[1] = max(span[1], visit["t"])
        for product, amount in visit["goods"]:
            cell = net[(visit["route"], visit["island"], product)]
            cell[0] += amount
            cell[1] += 1
    return net, times, window


def total_variation(a, b):
    """Total variation distance between two share vectors (each sums to 1): half the sum of absolute differences."""
    return sum(abs(x - y) for x, y in zip(a, b)) / 2


def write_csv(name, header, rows):
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / name
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(",".join(header) + "\n")
        for row in rows:
            handle.write(",".join(str(c).replace(",", ";") for c in row) + "\n")
    return path
