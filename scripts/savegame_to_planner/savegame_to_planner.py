"""Convert an Anno 117 savegame (.a8s) into a Taludas Planner plan file (plan JSON).

Read-only on the savegame. Everything that is decoded goes to a work directory (temporary by default).
See README.md next to this file for prerequisites, usage and the field mapping.

Run it with the Python environment of the Planner repo, e.g.

    cd C:\\dev\\Anno-117-Planner
    uv run python C:\\dev\\Anno-117-Layout-Tool\\tools\\savegame_to_planner\\savegame_to_planner.py SAVE.a8s -o OUT.plan.json
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import os
import re
import shutil
import struct
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

sys.dont_write_bytecode = True  # keep the layout repo free of __pycache__

LAYOUT_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAYOUT_REPO))

import savegame_parser as sp  # noqa: E402  (the layout tool's decoder helpers)

# Region of a session -> prefix of the placeholder island name
REGION_NAME = {"Roman": "Latium", "Celtic": "Albion", "Egyptian": "Aegyptus"}
SIZE_WORD = {"small": "Small", "medium": "Medium", "large": "Large", "extralarge": "XL", "continental": "Continental"}
VILLA_TEMPLATES = {"VillaUrban", "GuestHouse"}
HUMAN_PROFILE = 41


# --------------------------------------------------------------------------- tiny XML tree

class Node:
    """One element of the FileDBReader XML (one tag or leaf per line)."""

    __slots__ = ("tag", "text", "kids")

    def __init__(self, tag: str, text: Optional[str] = None):
        self.tag = tag
        self.text = text
        self.kids: list[Node] = []

    def get(self, tag: str) -> Optional["Node"]:
        for kid in self.kids:
            if kid.tag == tag:
                return kid
        return None

    def all(self, tag: str) -> list["Node"]:
        return [kid for kid in self.kids if kid.tag == tag]

    def find(self, path: str) -> Optional["Node"]:
        node: Optional[Node] = self
        for part in path.split("/"):
            node = node.get(part) if node is not None else None
        return node


_RE_LEAF = re.compile(r"^<([^>/ ]+)>(.*)</\1>$")
_RE_OPEN = re.compile(r"^<([^>/ ]+)>$")
_RE_EMPTY = re.compile(r"^<([^>/ ]+) ?/>$")


def stream(xml_path: Path, want: Callable[[list[str]], bool]) -> Iterator[tuple[list[str], Node]]:
    """Yield (tag path, subtree) for every element whose path satisfies ``want`` (not nested inside another capture)."""
    stack: list[Node] = []
    path: list[str] = []
    root: Optional[Node] = None
    with open(xml_path, encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("</"):
                node = stack.pop()
                path.pop()
                if node is root:
                    root = None
                    yield list(path), node
                continue
            match = _RE_LEAF.match(line)
            if match:
                if root is not None:
                    stack[-1].kids.append(Node(match.group(1), match.group(2)))
                continue
            match = _RE_OPEN.match(line)
            if match:
                node = Node(match.group(1))
                if root is not None:
                    stack[-1].kids.append(node)
                stack.append(node)
                path.append(match.group(1))
                if root is None and want(path):
                    root = node
                continue
            match = _RE_EMPTY.match(line)
            if match and root is not None:
                stack[-1].kids.append(Node(match.group(1), ""))


def pairs(node: Node) -> list[tuple[Node, Node]]:
    """FileDB maps are written as alternating key leaf / value element."""
    kids = node.kids
    return [(kids[i], kids[i + 1]) for i in range(0, len(kids) - 1, 2)]


def u32(hex_text: Optional[str]) -> int:
    return int.from_bytes(bytes.fromhex(hex_text), "little") if hex_text else 0


def f32(hex_text: Optional[str]) -> float:
    return struct.unpack("<f", bytes.fromhex(hex_text))[0] if hex_text else 0.0


def i32(hex_text: str) -> int:
    return int.from_bytes(bytes.fromhex(hex_text), "little", signed=True)


def utf16(hex_text: Optional[str]) -> str:
    return bytes.fromhex(hex_text).decode("utf-16-le", errors="replace").rstrip("\x00") if hex_text else ""


# --------------------------------------------------------------------------- tools and decoding

def find_tools(args: argparse.Namespace) -> tuple[Path, Path]:
    """RdaConsole / FileDBReader: argument, then environment variable, then the layout tool's own lookup."""
    rda = args.rda_console or os.environ.get("ANNO_RDACONSOLE")
    fdb = args.filedb_reader or os.environ.get("ANNO_FILEDBREADER")
    if not (rda and fdb):
        try:
            import tool_manager  # the layout tool's lookup (cached setting, tools folder, PATH)

            found = tool_manager.get_tool_paths({})
            rda = rda or (str(found["RdaConsole"]) if found.get("RdaConsole") else None)
            fdb = fdb or (str(found["FileDBReader"]) if found.get("FileDBReader") else None)
        except Exception:  # tkinter missing or lookup failed: fall through to the error below
            pass
    for label, value in (("RdaConsole", rda), ("FileDBReader", fdb)):
        if not value or not Path(value).is_file():
            raise SystemExit(f"{label} not found: pass --{'rda-console' if label == 'RdaConsole' else 'filedb-reader'} "
                             f"or set ANNO_{label.upper()}")
    return Path(rda), Path(fdb)


def decode_save(save: Path, rda: Path, fdb: Path, work: Path, say: Callable[[str], None]) -> tuple[Path, list[Path]]:
    """.a8s -> data.a7s -> zlib -> outer XML + one decoded XML per session. Returns (outer xml, session xmls)."""
    outer_dir = work / "outer"
    say("extracting the archive")
    sp._rda_extract(rda, save, outer_dir)
    a7s = sp._find_file(outer_dir, ("data.a7s", "*.a7s"))
    if a7s is None:
        raise SystemExit("no data.a7s in the savegame archive")
    raw = work / "data_raw.bin"
    sp._zlib_decompress(a7s, raw)
    say("decoding the outer FileDB (about a minute)")
    outer_xml = sp._filedb_to_xml(fdb, raw, timeout=600)
    blobs = sp._extract_all_session_binaries(outer_xml, work, say)
    sessions = []
    for index, blob in enumerate(blobs):
        say(f"decoding session {index + 1}/{len(blobs)}")
        sessions.append(sp._filedb_to_xml(fdb, blob, timeout=900))
    return outer_xml, sessions


def session_guids(outer_xml: Path) -> list[int]:
    guids: list[int] = []
    inside = False
    with open(outer_xml, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if text == "<GameSessions>":
                inside = True
            elif text == "</GameSessions>":
                break
            elif inside:
                match = re.match(r"<SessionGUID>([0-9A-Fa-f]+)</SessionGUID>", text)
                if match:
                    guids.append(u32(match.group(1)))
    return guids


# --------------------------------------------------------------------------- extraction

def read_empire(outer_xml: Path) -> dict[str, Any]:
    """Dominant patron and researched techs of the human participant (outer XML)."""
    empire: dict[str, Any] = {"dominant_patron": None, "techs": [], "tech_counts": {}, "queue": []}
    for _path, node in stream(outer_xml, lambda p: p[-1] == "ParticipantPatronInfos"):
        data = node.get("Data")
        for key, value in pairs(data) if data is not None else []:
            if u32(key.text) == HUMAN_PROFILE:
                active = value.get("ActiveDominantPatronGuid")
                empire["dominant_patron"] = u32(active.text) if active is not None and active.text else None
        break
    # the tech handler with research progress belongs to the human; the others hold only completed techs
    for _path, node in stream(outer_xml, lambda p: p[-1] == "MetaTechHandler"):
        progress = node.get("TechProgress")
        if progress is not None and progress.kids:
            empire["techs"] = [u32(c.text) for c in node.get("TechCompleted").kids]
            repeat = node.get("TechRepeatables").kids
            empire["tech_counts"] = {u32(repeat[i].text): u32(repeat[i + 1].text) for i in range(0, len(repeat) - 1, 2)}
            empire["queue"] = [u32(c.text) for c in node.get("ResearchQueue").kids]
            break
    # effects the meta layer applies to the human participant (decisions, quests, discoveries)
    empire["meta_effects"] = set()
    for _path, node in stream(outer_xml, lambda p: p[-1] == "MetaEffectManager"):
        effects = node.get("Effects")
        for rec in effects.kids if effects is not None else []:
            target, guid = rec.get("TargetParticipant"), rec.get("Guid")
            if target is not None and guid is not None and u32(target.text) == HUMAN_PROFILE:
                empire["meta_effects"].add(u32(guid.text))
        break
    # the player's trade routes: stations in file (circuit) order with their cargo slots, and the ship count
    empire["routes"] = {}
    for _path, node in stream(outer_xml, lambda p: p[-1] == "RouteMap"):
        for _key, rec in pairs(node):
            if u32(rec.get("Owner").text) != HUMAN_PROFILE:
                continue
            stations = []
            for station in rec.get("Stations").kids:
                slots = []
                for info in station.get("GoodInfos").kids:
                    amount, index, loading = info.get("Amount"), info.get("Index"), info.get("IsLoading")
                    slots.append({"product": u32(info.get("ProductGUID").text), "amount": u32(amount.text) if amount is not None else None,
                                  "load": loading is None or loading.text not in ("00",), "index": u32(index.text) if index is not None else 0})
                stations.append({"area": u32(station.get("AreaID").text), "owner": u32(station.get("AreaOwner").text), "slots": slots})
            ships = rec.get("Ships")
            empire["routes"][u32(rec.get("ID").text)] = {
                "name": utf16(rec.get("Name").text), "ships": len(ships.text) // 16 if ships is not None and ships.text else 0, "stations": stations}
        break
    return empire


def read_session(xml_path: Path) -> list[dict[str, Any]]:
    """Player areas of one session: fertilities, name hash/text, patron, devotion, building counts, residents, sockets."""
    human: dict[int, dict[str, Any]] = {}
    items: dict[str, dict[str, Any]] = {}

    def want(path: list[str]) -> bool:
        if path[-1] == "AreaInfo" and len(path) == 3:
            return True
        if path[-1] == "ItemMap" and len(path) == 4:
            return True
        if len(path) == 5 and path[-2].startswith("AreaManager_") and path[-1] in ("AreaObjectManager", "AreaReligionManager", "AreaEffectManager", "AreaStreetManager",
                                                                                "AreaResidenceConsumptionManager"):
            return int(path[-2].split("_")[1]) in human
        return False

    for path, node in stream(xml_path, want):
        if node.tag == "AreaInfo":
            for key, value in pairs(node):
                owner = value.get("OwnerProfile")
                if owner is None or u32(owner.text) != HUMAN_PROFILE:
                    continue
                fert = value.get("Fertility")
                lode = value.find("LimitedLodeComponent/LimitedLodeFertilities")
                guid = value.get("CityNameGuid")
                custom = value.get("CityName")  # a name typed by the player (Anno 1800 style), if the save has one
                history = value.find("PassiveTrade/History/TradeRouteEntries")
                visits: dict[int, list[int]] = {}  # route id -> game times of the ships' visits at this island
                for route_key, entries in pairs(history) if history is not None else []:
                    visits[u32(route_key.text)] = sorted({u32(e.get("ExecutionTime").text) for e in entries.kids if e.get("ExecutionTime") is not None})
                human[u32(key.text)] = {
                    "visits": visits,
                    "key": u32(key.text),
                    "fertilities": sorted(u32(c.text) for c in fert.kids) if fert is not None else [],
                    "lode": sorted(u32(c.text) for c in lode.kids) if lode is not None else [],
                    "cityNameGuid": int.from_bytes(bytes.fromhex(guid.text), "little", signed=True) if guid is not None and guid.text else None,
                    "cityName": utf16(custom.text) if custom is not None and custom.text else None,
                }
        elif node.tag == "ItemMap":
            for key, value in pairs(node):
                guid, boosted = value.get("GUID"), value.get("IsBoosted")
                items[key.text] = {"guid": u32(guid.text) if guid is not None else None, "boosted": bool(boosted is not None and boosted.text == "01")}
        elif node.tag == "AreaReligionManager":
            area = human[int(path[-1].split("_")[1])]
            patron, devotion = node.get("PatronGuid"), node.get("Devotion")
            area["patron"] = u32(patron.text) if patron is not None and patron.text else None
            area["devotion"] = u32(devotion.text) if devotion is not None and devotion.text else 0
        elif node.tag == "AreaResidenceConsumptionManager":
            area = human[int(path[-1].split("_")[1])]
            product_data = node.get("ProductData")
            area["paused"] = []  # (product, population level) pairs the player stopped supplying
            for key, value in pairs(product_data) if product_data is not None else []:
                info = value.get("PopulationPauseInfo")
                for level, flag in pairs(info) if info is not None else []:
                    if flag.text not in (None, "", "00"):
                        area["paused"].append((u32(key.text), u32(level.text)))
        elif node.tag == "AreaStreetManager":
            area = human[int(path[-1].split("_")[1])]
            edges = node.find("Graph/Edges")
            area["roads"] = []
            for rec in edges.kids if edges is not None else []:
                guid, edge = rec.get("guid"), rec.get("Edge")
                low, high = (edge.get("PosMin"), edge.get("PosMax")) if edge is not None else (None, None)
                if guid is not None and low is not None and high is not None and len(low.text) == 16 and len(high.text) == 16:
                    area["roads"].append((u32(guid.text), u32(low.text[:8]), u32(low.text[8:]), u32(high.text[:8]), u32(high.text[8:])))
        elif node.tag == "AreaEffectManager":
            area = human[int(path[-1].split("_")[1])]
            effects = node.get("Effects")
            area["effects"] = []
            for rec in effects.kids if effects is not None else []:
                scope, source, distance, owner = rec.find("Scope/value/id"), rec.find("Source/ObjectID"), rec.get("Distance"), rec.get("ModuleOwner")
                area["effects"].append({
                    "guid": u32(rec.get("Guid").text), "scope": u32(scope.text) if scope is not None else None,
                    "source": source.text if source is not None else None,
                    "distance": u32(distance.text) if distance is not None and distance.text else None,
                    "owner": owner.text if owner is not None else None})
        elif node.tag == "AreaObjectManager":
            area = human[int(path[-1].split("_")[1])]
            objects = node.find("GameObject/objects")
            counts: dict[int, int] = {}
            sockets: list[dict[str, Any]] = []
            placed: list[dict[str, Any]] = []
            for obj in objects.kids if objects is not None else []:
                guid = obj.get("guid")
                owner = obj.get("OwnerProfile")
                if guid is None or (owner is not None and u32(owner.text) != HUMAN_PROFILE):
                    continue
                building = u32(guid.text)
                counts[building] = counts.get(building, 0) + 1
                position, ident = obj.get("Position"), obj.get("ID")
                if position is not None and position.text and len(position.text) == 24 and ident is not None:
                    aqueduct = obj.find("AqueductConsumer/DistributorsInRange")
                    angle = obj.get("Direction")
                    placed.append({"id": ident.text, "building": building, "x": f32(position.text[:8]), "z": f32(position.text[16:]),
                                   "angle": f32(angle.text) if angle is not None and angle.text else 0.0,
                                   "water": len(aqueduct.kids) if aqueduct is not None else 0})
                socket_items = obj.find("ItemContainer/SocketContainer/SocketItems")
                if socket_items is not None and socket_items.kids:
                    sockets.append({
                        "building": building, "id": ident.text if ident is not None else None,
                        "items": [{"item": u32(s.get("GUID").text), "ref": (s.find("ItemReference/ID").text if s.find("ItemReference/ID") is not None else None)}
                                  for s in socket_items.kids if s.get("GUID") is not None],
                    })
            area["counts"] = counts
            area["sockets"] = sockets
            area["placed"] = placed
    result = list(human.values())
    for area in result:
        area["itemMap"] = items
    return result


def read_session_extra(xml_path: Path) -> dict[str, Any]:
    """Session-wide data: the map template (file, elements) and the ships on trade routes."""
    result: dict[str, Any] = {"map_file": "", "elements": [], "ships": []}

    def want(path: list[str]) -> bool:
        if path[-1] == "MapTemplate" and len(path) == 3:
            return True
        return len(path) == 8 and path[-5].startswith("AreaManager_") and path[-3] == "GameObject" and path[-1] == "None"

    for path, node in stream(xml_path, want):
        if node.tag == "MapTemplate":
            name = node.get("Filename")
            result["map_file"] = utf16(name.text) if name is not None and name.text else ""
            for element in node.all("TemplateElement"):
                inner = element.get("Element")
                position, map_path = (inner.get("Position"), inner.get("MapFilePath")) if inner is not None else (None, None)
                if position is None or not position.text:
                    result["elements"].append(None)
                    continue
                stem = utf16(map_path.text).replace("\\", "/").split("/")[-1].rsplit(".", 1)[0] if map_path is not None and map_path.text else ""
                result["elements"].append({"x": i32(position.text[:8]), "z": i32(position.text[8:]), "stem": stem})
            continue
        vehicle = node.get("PropertyTradeRouteVehicle")
        if vehicle is None or vehicle.get("TradeRouteID") is None:
            continue
        modules = node.find("ShipModuleOwner/InstalledShipModules")
        sockets = node.find("ItemContainer/SocketContainer/SocketItems")
        owner = node.get("OwnerProfile")
        result["ships"].append({
            "type": u32(node.get("guid").text), "route": u32(vehicle.get("TradeRouteID").text),
            "owner": u32(owner.text) if owner is not None else HUMAN_PROFILE,
            "modules": [u32(m.get("ShipModuleGuid").text) for m in modules.kids if m.get("ShipModuleGuid") is not None] if modules is not None else [],
            "items": [{"item": u32(s.get("GUID").text), "ref": (s.find("ItemReference/ID").text if s.find("ItemReference/ID") is not None else None)}
                      for s in sockets.kids if s.get("GUID") is not None] if sockets is not None else []})
    return result


def load_texts(texts_xml: Path) -> dict[int, str]:
    """LineId (signed 64 bit) -> text from the game's texts_<language>.xml."""
    content = texts_xml.read_text(encoding="utf-8", errors="replace")
    return {int(a): b.strip() for a, b in re.findall(r"<LineId>(-?\d+)</LineId>\s*<Text>([^<]*)</Text>", content)}


# --------------------------------------------------------------------------- effects applied to production buildings

SCOPE_RADIUS = 2  # AreaEffectManager scope id of circle effects (6 = street distance, 4 = objects in area, 1 = module owner)
NEAR_TIE = 0.1  # decisions within 10 % of the total (at least one building) of an exact half are reported as near ties


SCOPE_STREET = 6
STREET_TOUCH = 1.0  # a road tile (centre) touches a building when it is within this distance of the footprint (adjacent tiles: 0.5)


class StreetNet:
    """Road network of one area: unit tiles along the save's street edges.

    Edge positions are in half tiles. Mode "euclid" (default) measures the walked distance in tiles, a diagonal step
    is 1.414, and starts at 0 on the source's road tiles. Mode "layout" is the layout tool's model: every step is one
    hop, diagonals included, and the first tile already costs. Both use 1/1.5 per unit on paved and marble roads
    (ROAD_STREET_DISTANCE_MULTIPLIER).
    """

    def __init__(self, area: dict[str, Any], data: Any, mode: str = "euclid"):
        self.euclid = mode == "euclid"
        self.cost: dict[tuple[int, int], float] = {}
        self.link: dict[tuple[int, int], set[tuple[int, int]]] = {}
        for guid, x1, z1, x2, z2 in area.get("roads", []):
            name = str((data.buildings.get(guid) or {}).get("name") or "")
            step = 1.0 / 1.5 if ("Paved" in name or "Marble" in name) else 1.0
            count = max(abs(x2 - x1), abs(z2 - z1)) // 2
            previous = None
            for i in range(count + 1 if count else 0):
                point = (round(x1 + (x2 - x1) * i / count), round(z1 + (z2 - z1) * i / count))
                self.cost[point] = min(self.cost.get(point, step), step)
                if previous is not None and previous != point:
                    self.link.setdefault(previous, set()).add(point)
                    self.link.setdefault(point, set()).add(previous)
                previous = point
        self.cells: dict[tuple[int, int], list[tuple[int, int]]] = {}
        for point in self.cost:
            self.cells.setdefault((point[0] // 32, point[1] // 32), []).append(point)

    def touching(self, building: dict, width: float, height: float) -> set[tuple[int, int]]:
        """Road tiles touching the oriented footprint of a building."""
        reach = math.hypot(width, height) / 2 + 2
        cos, sin = math.cos(building["angle"]), math.sin(building["angle"])
        found: set[tuple[int, int]] = set()
        for cx in range(int((building["x"] - reach) * 2) // 32, int((building["x"] + reach) * 2) // 32 + 1):
            for cz in range(int((building["z"] - reach) * 2) // 32, int((building["z"] + reach) * 2) // 32 + 1):
                for point in self.cells.get((cx, cz), ()):
                    dx, dz = point[0] / 2 - building["x"], point[1] / 2 - building["z"]
                    lx, lz = dx * cos + dz * sin, -dx * sin + dz * cos
                    if math.hypot(max(abs(lx) - width / 2, 0.0), max(abs(lz) - height / 2, 0.0)) <= STREET_TOUCH:
                        found.add(point)
        return found

    def reach(self, start: set[tuple[int, int]], budget: float) -> set[tuple[int, int]]:
        """Road tiles reachable within the budget (weighted shortest path, the layout tool's _street_distance_bfs)."""
        best: dict[tuple[int, int], float] = {}
        heap: list[tuple[float, tuple[int, int]]] = []
        for point in start:
            first = 0.0 if self.euclid else self.cost[point]
            if first <= budget:
                best[point] = first
                heapq.heappush(heap, (first, point))
        while heap:
            spent, point = heapq.heappop(heap)
            if spent > best.get(point, math.inf):
                continue
            for other in self.link.get(point, ()):
                length = math.hypot(other[0] - point[0], other[1] - point[1]) / 2 if self.euclid else 1.0
                total = spent + length * self.cost[other]
                if total <= budget and total < best.get(other, math.inf):
                    best[other] = total
                    heapq.heappush(heap, (total, other))
        return set(best)


def derive_production(area: dict[str, Any], data: Any, item_boosted: Callable[[Optional[str]], bool],
                      street_mode: str = "euclid") -> tuple[dict[int, Any], list[dict], list[str]]:
    """Per production building type: effects applied by range, as planner FactorySettings.

    An effect counts for a type when more than half of the type's buildings are affected (strict majority). A building
    is affected by a circle effect when its centre lies within the radius of the centre of at least one source building
    (the layout tool's rule, canvas_widget._compute_in_range_ids). Returns (settings per factory GUID, decisions, notes).
    """
    from paxplanner.model.project import FactorySettings, ItemSlot

    placed = area.get("placed", [])
    by_id = {p["id"]: p for p in placed}
    types: dict[int, list[dict]] = {}
    for p in placed:
        if p["building"] in data.factories:
            types.setdefault(p["building"], []).append(p)
    effects = area.get("effects", [])
    radius_of: dict[str, int] = {}
    street_of: dict[str, int] = {}
    for rec in effects:
        if rec["source"] and rec["distance"] and rec["scope"] == SCOPE_RADIUS:
            radius_of[rec["source"]] = max(radius_of.get(rec["source"], 0), rec["distance"])
        elif rec["source"] and rec["distance"] and rec["scope"] == SCOPE_STREET:
            street_of[rec["source"]] = max(street_of.get(rec["source"], 0), rec["distance"])

    settings: dict[int, Any] = {}
    decisions: list[dict] = []
    notes: list[str] = []
    network: list[StreetNet] = []
    touch_cache: dict[str, set[tuple[int, int]]] = {}
    reach_cache: dict[tuple[str, float], set[tuple[int, int]]] = {}

    def in_range(source: dict, radius: float, factory: int) -> set[str]:
        limit = radius * radius
        return {p["id"] for p in types.get(factory, []) if (p["x"] - source["x"]) ** 2 + (p["z"] - source["z"]) ** 2 <= limit}

    def footprint(guid: int) -> Optional[tuple[float, float]]:
        factory = data.factories.get(guid)
        dims = data.buildings.get(guid) or (factory.raw if factory else {})
        return (dims["width"], dims["height"]) if dims.get("width") and dims.get("height") else None

    def in_street(source: dict, budget: float, factory: int) -> set[str]:
        if not network:
            network.append(StreetNet(area, data, street_mode))
        net = network[0]

        def tiles_of(obj: dict) -> set[tuple[int, int]]:
            if obj["id"] not in touch_cache:
                dims = footprint(obj["building"])
                touch_cache[obj["id"]] = net.touching(obj, *dims) if dims else set()
            return touch_cache[obj["id"]]

        if footprint(factory) is None or footprint(source["building"]) is None:
            note = f"building {factory}: footprint unknown, street reach replaced by the circle of the same distance"
            if note not in notes:
                notes.append(note)
            return in_range(source, budget, factory)

        if (source["id"], budget) not in reach_cache:
            reach_cache[(source["id"], budget)] = net.reach(tiles_of(source), budget)
        reached = reach_cache[(source["id"], budget)]
        return {p["id"] for p in types.get(factory, []) if tiles_of(p) & reached}

    def decide(factory: int, kind: str, ident: int, affected: set[str], apply: Callable[[Any], None], circle: Optional[set[str]] = None) -> None:
        total = len(types[factory])
        applied = len(affected) * 2 > total
        decision = {"factory": factory, "kind": kind, "id": ident, "affected": len(affected), "total": total, "applied": applied,
                    "near_tie": total >= 2 and abs(len(affected) - total / 2) <= max(1.0, NEAR_TIE * total)}
        if circle is not None:
            decision.update({"method": "street", "circle_affected": len(circle), "circle_applied": len(circle) * 2 > total})
        decisions.append(decision)
        if applied:
            apply(settings.setdefault(factory, FactorySettings()))

    # (1) items in villas, officia and other buildings with sockets, by circle
    item_hits: dict[tuple[int, int, bool], set[str]] = {}
    item_circle: dict[tuple[int, int, bool], set[str]] = {}
    for socket in area["sockets"]:
        holder = by_id.get(socket["id"])
        building = data.buildings.get(socket["building"]) or {}
        radius = radius_of.get(socket["id"]) or building.get("effectRadius")
        for entry in socket["items"]:
            rec = data.items.get(entry["item"])
            effect = (rec or {}).get("effect") or {}
            targets = set(effect.get("targets") or []) & set(types)
            if not rec or not effect.get("buffs") or not targets or holder is None:
                continue
            boosted = item_boosted(entry["ref"])
            if effect.get("scope") == "StreetDistance":
                budget = street_of.get(socket["id"]) or (building.get("radius") or {}).get("value")
                if not budget:
                    notes.append(f"item {entry['item']} in building {socket['building']}: street scope without a distance, not computed")
                    continue
                for factory in targets:
                    key = (factory, entry["item"], boosted)
                    item_hits.setdefault(key, set()).update(in_street(holder, budget, factory))
                    item_circle.setdefault(key, set()).update(in_range(holder, budget, factory))
            elif effect.get("scope") == "Radius" and radius:
                for factory in targets:
                    item_hits.setdefault((factory, entry["item"], boosted), set()).update(in_range(holder, radius, factory))
            else:
                notes.append(f"item {entry['item']} in building {socket['building']}: scope {effect.get('scope')} / radius {radius}, not computed")
    for (factory, item, boosted), hits in item_hits.items():
        decide(factory, "item", item, hits, lambda s, i=item, b=boosted: s.items.append(ItemSlot(i, b)),
               item_circle.get((factory, item, boosted)))

    # (2) radius effects of buildings: granaries (building_effects) and Hippodrome splendour (effects)
    effect_hits: dict[tuple[int, int], set[str]] = {}
    effect_circle: dict[tuple[int, int], set[str]] = {}
    for rec in effects:
        known = rec["guid"] in data.building_boosts or rec["guid"] in data.area_boosts
        source = by_id.get(rec["source"]) if rec["source"] else None
        if not known or source is None:
            continue
        if rec["scope"] not in (SCOPE_RADIUS, SCOPE_STREET) or not rec["distance"]:
            notes.append(f"effect {rec['guid']} from building {source['building']}: scope {rec['scope']}, not computed")
            continue
        for factory in set(data.effects[rec["guid"]]["targets"]) & set(types):
            key = (factory, rec["guid"])
            if rec["scope"] == SCOPE_RADIUS:
                effect_hits.setdefault(key, set()).update(in_range(source, rec["distance"], factory))
            else:
                effect_hits.setdefault(key, set()).update(in_street(source, rec["distance"], factory))
                effect_circle.setdefault(key, set()).update(in_range(source, rec["distance"], factory))
    for (factory, guid), hits in effect_hits.items():
        if guid in data.building_boosts:
            decide(factory, "building_effect", guid, hits, lambda s, g=guid: s.building_effects.append(g), effect_circle.get((factory, guid)))
        else:
            decide(factory, "effect", guid, hits, lambda s, g=guid: s.effects.append(g), effect_circle.get((factory, guid)))

    # (3) silo / dovecote modules: the module's effect record names the farm that owns it
    modules = {m["guid"] for m in data.silo_modules}
    owners: dict[int, set[str]] = {}
    for rec in effects:
        source = by_id.get(rec["source"]) if rec["source"] else None
        owner = by_id.get(rec["owner"]) if rec["owner"] else None
        if source is not None and owner is not None and source["building"] in modules and owner["building"] in types:
            owners.setdefault(owner["building"], set()).add(owner["id"])
    for factory in types:
        if data.factories[factory].raw.get("additionalModule"):
            decide(factory, "silo", data.factories[factory].raw["additionalModule"], owners.get(factory, set()), lambda s: setattr(s, "silo", True))

    # (4) water: buildings with a distributor (aqueduct / irrigation) in range, for types with an optional water buff
    for factory, instances in types.items():
        if data.factories[factory].raw.get("aqueduct"):
            decide(factory, "aqueduct", 0, {p["id"] for p in instances if p["water"] > 0}, lambda s: setattr(s, "aqueduct", True))
    return settings, decisions, notes


# --------------------------------------------------------------------------- harbours, position, needs

def derive_harbour(area: dict[str, Any], data: Any, region: Optional[str], item_boosted: Callable[[Optional[str]], bool]) -> tuple[Optional[int], int, Any]:
    """(trading post GUID or None for the region's basic post, number of trading piers, harbour item) of an island.

    The harbour item is an item from the game data's harbour items (Julia Publica) in a villa or officium whose circle
    (the radius of its effect records, else the building's effectRadius) covers the trading post.
    """
    from paxplanner.model.project import ItemSlot

    harbours = [h for h in data.ships.get("harbours", []) if h.get("region") == region]
    posts = [h["guid"] for h in harbours if "Pier" not in str(h.get("name"))]
    piers = {h["guid"] for h in harbours if "Pier" in str(h.get("name"))}
    placed = area.get("placed", [])
    post = next((p for p in placed if p["building"] in posts), None)
    count = sum(1 for p in placed if p["building"] in piers)
    if post is None:
        return None, count, None
    radius_of: dict[str, int] = {}
    for rec in area.get("effects", []):
        if rec["source"] and rec["scope"] == SCOPE_RADIUS and rec["distance"]:
            radius_of[rec["source"]] = max(radius_of.get(rec["source"], 0), rec["distance"])
    by_id = {p["id"]: p for p in placed}
    wanted = {i["guid"] for i in data.ships.get("harbourItems", [])}
    item = None
    for socket in area.get("sockets", []):
        holder = by_id.get(socket["id"])
        radius = radius_of.get(socket["id"]) or (data.buildings.get(socket["building"]) or {}).get("effectRadius")
        for entry in socket["items"]:
            if holder is not None and radius and entry["item"] in wanted and math.hypot(holder["x"] - post["x"], holder["z"] - post["z"]) <= radius:
                item = ItemSlot(entry["item"], item_boosted(entry["ref"]))
    return (None if post["building"] == posts[0] else post["building"]), count, item


def derive_disabled_needs(area: dict[str, Any], data: Any) -> dict[int, list[int]]:
    """Needs the player stopped supplying (AreaResidenceConsumptionManager PopulationPauseInfo), per population level."""
    result: dict[int, set[int]] = {}
    for product, level in area.get("paused", []):
        residence = data.residence_by_level.get(level) or {}
        for need in residence.get("needs", []):
            if (data.needs.get(need["need"]) or {}).get("product") == product:
                result.setdefault(level, set()).add(need["need"])
    return {level: sorted(needs) for level, needs in result.items()}


def derive_position(extra: dict[str, Any], key: int, data: Any) -> tuple[Optional[str], str, str]:
    """(map slot, island size, map file stem) of an area.

    The island id of the area key is the 1-based index of the island file in the session's map template. Aegyptus slots
    are the Planner's island names (large_01 ...), Prophecies of Ash continental island is "Cinis". The campaign
    templates of Latium and Albion are not among the Planner's random map templates, so their slots stay unset.
    """
    elements = extra.get("elements", [])
    island_id = (key >> 6) & 127
    element = elements[island_id - 1] if 0 < island_id <= len(elements) else None
    stem = (element or {}).get("stem", "")
    word = re.search(r"(?:island|valley)_(small|medium|large|extralarge|continental)", stem)
    size = SIZE_WORD.get(word.group(1), "Large") if word else "Large"
    slot = None
    if "valley_" in stem and stem.split("valley_")[1] in {i["name"] for i in (data.maps.get("egypt") or {}).get("islands", [])}:
        slot = stem.split("valley_")[1]
    elif "continental" in stem:
        slot = "Cinis"
    return slot, size, stem


# --------------------------------------------------------------------------- trade routes and fleet

def derive_trade(plan: Any, data: Any, empire: dict[str, Any], areas: dict[int, dict[str, Any]], ships: list[dict[str, Any]]) -> dict[str, Any]:
    """Ship templates, supplied_by and route settings from the game's trade routes (requirement R37).

    Roles per product follow from the slot modes: a station with only load slots is a source, a station with unload
    slots receives (a relay passes nothing on). Each receiver is served by the nearest source before it in the circuit
    (cyclic). An island served by several sources splits by weight = visits at the island x configured unload amount.
    The largest weight is listed last with -1, every other supplier gets its share of the island's demand in t/min.
    """
    from paxplanner.model.engine import Engine
    from paxplanner.model.project import RouteSettings, ShipTemplate

    ids = {i.id: i for i in plan.islands}
    ship_names = {s["guid"]: str((s.get("loca") or {}).get("english") or s["guid"]) for s in data.ships.get("ships", [])}
    captains = {c["guid"] for c in data.ships.get("captains", [])}
    report: dict[str, Any] = {"templates": [], "imports": [], "pairs": [], "notes": []}

    # ship configurations in use, and the template of every route
    templates: dict[tuple, ShipTemplate] = {}
    route_template: dict[int, list[Any]] = {}
    for ship in ships:
        if ship["owner"] != HUMAN_PROFILE or ship["route"] not in empire["routes"] or ship["type"] not in ship_names:
            continue
        captain = next((i["item"] for i in ship["items"] if i["item"] in captains), None)
        boosted = bool(captain and ship["itemMap"].get(next(i["ref"] for i in ship["items"] if i["item"] == captain), {}).get("boosted"))
        config = (ship["type"], tuple(ship["modules"]), captain, boosted)
        if config not in templates:
            templates[config] = ShipTemplate(name=f"{ship_names[ship['type']]} {len(templates) + 1}", ship=ship["type"], id=f"t{len(templates) + 1}",
                                             modules=list(ship["modules"]), captain=captain, boosted=boosted)
        route_template.setdefault(ship["route"], []).append(templates[config])
    plan.ship_templates = list(templates.values())
    report["templates"] = [{"id": t.id, "name": t.name, "ship": t.ship, "modules": t.modules, "captain": t.captain, "boosted": t.boosted} for t in plan.ship_templates]

    # flow edges from the route configurations
    demand_engine = Engine(data, plan, True)
    weights: dict[tuple[str, int], dict[str, float]] = {}
    per_route: dict[int, dict[tuple[str, str], float]] = {}
    for rid, route in empire["routes"].items():
        stations = route["stations"]
        roles: list[dict[int, dict[str, float]]] = []
        for station in stations:
            products: dict[int, dict[str, float]] = {}
            for slot in station["slots"]:
                entry = products.setdefault(slot["product"], {"load": 0, "unload": 0, "amount": 0.0})
                if slot["load"]:
                    entry["load"] += 1
                else:
                    entry["unload"] += 1
                    entry["amount"] += slot["amount"] or 0
            roles.append(products)
        for product in {p for products in roles for p in products}:
            sources = [i for i, products in enumerate(roles) if product in products and products[product]["load"] and not products[product]["unload"]]
            if not sources:
                report["notes"].append(f"route {rid} {route['name']}: no source for product {product}")
                continue
            for r, products in enumerate(roles):
                if product not in products or not products[product]["unload"]:
                    continue
                supplier = stations[max((s for s in sources if s < r), default=sources[-1])]["area"]
                receiver = stations[r]["area"]
                if supplier == receiver:
                    continue
                if f"a{supplier}" not in ids or f"a{receiver}" not in ids:
                    report["notes"].append(f"route {rid}: station of a non-player area {supplier if f'a{supplier}' not in ids else receiver} skipped")
                    continue
                visits = max(1, len((areas.get(receiver) or {}).get("visits", {}).get(rid, [])))
                weight = visits * products[product]["amount"]
                weights.setdefault((f"a{receiver}", product), {}).setdefault(f"a{supplier}", 0.0)
                weights[(f"a{receiver}", product)][f"a{supplier}"] += weight
                per_route.setdefault(rid, {}).setdefault((f"a{supplier}", f"a{receiver}"), 0.0)
                per_route[rid][(f"a{supplier}", f"a{receiver}")] += weight

    results = {i.id: demand_engine.solve_island(i) for i in plan.islands}
    for (receiver, product), suppliers in sorted(weights.items()):
        island = ids[receiver]
        if any(data.factories[g].output == product for g in island.existing if g in data.factories):
            # the planner imports the whole demand of a listed good and builds no producers for it; an island that
            # also produces the good in the save keeps its producers, the partial import is not expressible
            report["notes"].append(f"{receiver} product {product}: local production, import not written")
            report["skipped"] = report.get("skipped", 0) + 1
            continue
        line = results[receiver].lines.get(product)
        demand = float(line.amount) if line is not None else 0.0
        order = sorted(suppliers.items(), key=lambda kv: (kv[1], kv[0]))
        total = sum(w for _, w in order) or 1.0
        entry: dict[str, float] = {}
        for supplier, weight in order[:-1]:
            if demand > 0:
                entry[supplier] = round(demand * weight / total, 4)
        entry[order[-1][0]] = -1.0
        island.supplied_by[product] = entry
        report["imports"].append({"island": receiver, "product": product, "demand": round(demand, 4),
                                  "weights": {s: w for s, w in order}, "supplied_by": entry})

    # ship settings per supplier>receiver pair: the route's ships split by the pair's share of its flow
    pair_ships: dict[str, float] = {}
    pair_templates: dict[str, dict[str, float]] = {}
    for rid, pairs_ in per_route.items():
        total = sum(pairs_.values()) or 1.0
        for (supplier, receiver), weight in pairs_.items():
            key = f"{supplier}>{receiver}"
            share = empire["routes"][rid]["ships"] * weight / total
            pair_ships[key] = pair_ships.get(key, 0.0) + share
            for template in route_template.get(rid, [])[:1]:
                pair_templates.setdefault(key, {})
                pair_templates[key][template.id] = pair_templates[key].get(template.id, 0.0) + share
    used = {f"{s}>{r}" for island in plan.islands for suppliers in island.supplied_by.values() for s in suppliers for r in [island.id] if s in ids}
    for key in sorted(used):
        best = max(pair_templates.get(key, {}).items(), key=lambda kv: kv[1], default=(None, 0))[0]
        count = max(1, round(pair_ships.get(key, 0.0)))
        plan.routes[key] = RouteSettings(template=best, ships=count)
        report["pairs"].append({"pair": key, "ships": count, "template": best, "exact_share": round(pair_ships.get(key, 0.0), 2)})
    return report


# --------------------------------------------------------------------------- plan

def build_plan(args: argparse.Namespace, empire: dict[str, Any], sessions: list[list[dict]], extras: list[dict[str, Any]], guids: list[int],
               texts: dict[int, str]):
    from paxplanner.model.gamedata import GameData
    from paxplanner.model.project import IslandPlan, ItemSlot, Plan
    from paxplanner.model.routes import optional_ship_effects

    data = GameData()
    plan = Plan(name=args.plan_name)
    plan.techs = sorted({t for t in empire["techs"] if t in data.techs} | {t for t in empire["tech_counts"] if t in data.techs})
    plan.tech_counts = {t: c for t, c in empire["tech_counts"].items() if t in data.techs}
    plan.research_queue = [t for t in empire["queue"] if t in data.techs]
    plan.dominant_patron = empire["dominant_patron"] if empire["dominant_patron"] in data.patrons else None
    # effects on all ships the plan cannot derive itself (decisions, quests): the optional ship effects the meta layer applies to the player
    plan.ship_effects = sorted(e["guid"] for e in optional_ship_effects(data) if e["guid"] in empire["meta_effects"])
    plan.map.dlc01 = any("dlc01" in extra["map_file"].lower() for extra in extras)

    resolved = 0
    report: list[dict] = []
    positions: dict[str, Any] = {}
    all_areas: dict[int, dict[str, Any]] = {}
    for index, areas in enumerate(sessions):
        session = guids[index]
        region = data.session_region(session)
        for area in sorted(areas, key=lambda a: a["key"]):
            all_areas[area["key"]] = area
            key = area["key"]
            island_id, area_index = (key >> 6) & 127, key >> 13
            counts = area["counts"]
            residences: dict[int, int] = {}
            for guid, count in counts.items():
                if guid in data.residences:
                    level = data.residences[guid]["populationLevel"]
                    residences[level] = residences.get(level, 0) + count
            present = set(area["fertilities"]) | set(area["lode"])
            missing = sorted(f for f, rec in data.fertilities.items()
                             if rec.get("regions") and data.natural_fertility(f, region) and f not in present)
            patron = area.get("patron")
            residence_items = []
            for socket in area["sockets"]:
                template = (data.buildings.get(socket["building"]) or {}).get("template")
                for entry in socket["items"]:
                    rec = data.items.get(entry["item"])
                    if rec is None or template not in VILLA_TEMPLATES or rec.get("allocation") != "Villa":
                        continue  # items acting on factories need building positions: not mapped
                    if set(data.residences) & set((rec.get("effect") or {}).get("targets") or []):
                        boosted = bool((area["itemMap"].get(entry["ref"]) or {}).get("boosted"))
                        residence_items.append(ItemSlot(entry["item"], boosted))
            boosted_of = lambda ref, m=area["itemMap"]: bool((m.get(ref) or {}).get("boosted"))  # noqa: E731
            factories, decisions, notes = derive_production(area, data, boosted_of, args.street_mode)
            harbour, piers, harbour_item = derive_harbour(area, data, region, boosted_of)
            disabled = derive_disabled_needs(area, data)
            slot, size, stem = derive_position(extras[index], key, data)
            placeholder = f"{REGION_NAME.get(region, str(region))} {island_id}" + (f".{area_index}" if area_index != 1 else "")
            name = area.get("cityName") or texts.get(area.get("cityNameGuid")) or placeholder
            resolved += name != placeholder
            island = IslandPlan(
                name=name, session=session, id=f"a{key}", residences=residences, disabled_needs=disabled,
                existing={g: c for g, c in counts.items() if g in data.factories},
                patron=patron if patron in data.patrons else None, devotion=float(area.get("devotion") or 0),
                factories=factories, missing_fertilities=missing, residence_items=residence_items, island_size=size,
                map_slot=slot, harbour=harbour, piers=piers, harbour_item=harbour_item)
            plan.islands.append(island)
            positions[island.id] = {"stem": stem, "slot": slot, "size": size}
            report.append({"key": key, "name": name, "decisions": decisions, "notes": notes, "harbour": harbour, "piers": piers,
                           "harbour_item": harbour_item.item if harbour_item else None,
                           "disabled_needs": {str(level): [{"need": n, "name": data.needs[n]["name"]} for n in needs] for level, needs in disabled.items()}})
    ships = [dict(ship, itemMap=sessions[index][0]["itemMap"] if sessions[index] else {}) for index, extra in enumerate(extras) for ship in extra["ships"]]
    trade = derive_trade(plan, data, empire, all_areas, ships)
    applied = sum(d["applied"] for entry in report for d in entry["decisions"])
    print(f"{len(plan.islands)} islands, {resolved} with a resolved name, {applied} range effects applied to production buildings, "
          f"{sum(len(i.supplied_by) for i in plan.islands)} imports, {len(plan.routes)} routes, {len(plan.ship_templates)} ship templates")
    if args.report:
        args.report.write_text(json.dumps({"islands": report, "positions": positions, "trade": trade, "ship_effects": plan.ship_effects}, indent=1), encoding="utf-8")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Anno 117 savegame (.a8s) -> Taludas Planner plan JSON")
    parser.add_argument("save", type=Path, help="the .a8s savegame (read only)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="plan JSON to write (existing file is replaced)")
    parser.add_argument("--planner-repo", type=Path, default=Path(os.environ.get("ANNO_PLANNER_REPO", LAYOUT_REPO.parent / "Anno-117-Planner")),
                        help="Planner checkout providing paxplanner (env ANNO_PLANNER_REPO)")
    parser.add_argument("--texts", type=Path, help="the game's texts_<language>.xml (data/base/config/gui) to resolve island names")
    parser.add_argument("--rda-console", help="RdaConsole.exe (env ANNO_RDACONSOLE)")
    parser.add_argument("--filedb-reader", help="FileDBReader.exe (env ANNO_FILEDBREADER)")
    parser.add_argument("--work-dir", type=Path, help="keep the decoded XML here (default: temporary folder, removed afterwards)")
    parser.add_argument("--reuse", action="store_true", help="with --work-dir: reuse already decoded XML there instead of decoding again")
    parser.add_argument("--report", type=Path, help="write the decisions (range effects, harbours, positions, disabled needs, trade) as JSON")
    parser.add_argument("--street-mode", choices=("euclid", "layout"), default="euclid",
                        help="street distance: walked length in tiles (default, validated in game) or the layout tool's hop count")
    parser.add_argument("--plan-name", default=None, help="plan name (default: save file name)")
    args = parser.parse_args()
    args.plan_name = args.plan_name or args.save.stem
    if not args.save.is_file():
        raise SystemExit(f"savegame not found: {args.save}")
    sys.path.insert(0, str(args.planner_repo))
    rda, fdb = find_tools(args)

    def say(message: str) -> None:
        print(message, flush=True)

    temp = None if args.work_dir else tempfile.mkdtemp(prefix="sg_to_planner_")
    work = args.work_dir or Path(temp)
    work.mkdir(parents=True, exist_ok=True)
    try:
        decoded = sorted(work.glob("session_*.xml"))
        if args.reuse and (work / "data_raw.xml").is_file() and decoded:
            outer_xml, session_xmls = work / "data_raw.xml", decoded
        else:
            outer_xml, session_xmls = decode_save(args.save, rda, fdb, work, say)
        guids = session_guids(outer_xml)
        if len(guids) != len(session_xmls):
            raise SystemExit("session count does not match the session GUIDs")
        say("reading the empire data")
        empire = read_empire(outer_xml)
        sessions, extras = [], []
        for index, xml in enumerate(session_xmls):
            say(f"reading session {index + 1}/{len(session_xmls)}")
            sessions.append(read_session(xml))
            extras.append(read_session_extra(xml))
        texts = load_texts(args.texts) if args.texts else {}
        plan = build_plan(args, empire, sessions, extras, guids, texts)
        plan.save(args.output)
        say(f"wrote {args.output}")
    finally:
        if temp:
            shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    main()
