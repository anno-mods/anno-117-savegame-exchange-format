import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, math, pickle
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
areas = pickle.load(open(SP + r"\x\areas_s2.pkl", "rb"))
a = next(x for x in areas if x["key"] == 8708)
net = s.StreetNet(a, gd)
def rect_dist(p, w, h, px, pz):
    cos, sin = math.cos(p["angle"]), math.sin(p["angle"])
    dx, dz = px - p["x"], pz - p["z"]
    lx, lz = dx * cos + dz * sin, -dx * sin + dz * cos
    return math.hypot(max(abs(lx) - w / 2, 0), max(abs(lz) - h / 2, 0))
ids = ["2901000004220000", "2D01000004220000", "3001000004220000", "3101000004220000", "3301000004220000", "4001000004220000", "6F01000004220000", "7101000004220000", "7301000004220000"]
by = {p["id"]: p for p in a["placed"]}
for i in ids:
    p = by[i]
    d = gd.buildings.get(p["building"]) or gd.factories[p["building"]].raw
    w, h = d["width"], d["height"]
    best = min(((rect_dist(p, w, h, x / 2, z / 2), (x / 2, z / 2)) for (x, z) in net.cost), key=lambda t: t[0])
    best2 = min(rect_dist(p, h, w, x / 2, z / 2) for (x, z) in net.cost)
    print(gd.name(p["building"], "english"), (round(p["x"], 1), round(p["z"], 1)), "angle", round(p["angle"], 2), "nearest road tile dist", round(best[0], 2), best[1], "swapped dims", round(best2, 2))
# how many production buildings touch with each threshold
prod = [p for p in a["placed"] if p["building"] in gd.factories]
import collections
for th in (0.75, 1.0, 1.25, 1.5, 2.0):
    n = 0
    for p in prod:
        d = gd.buildings.get(p["building"]) or gd.factories[p["building"]].raw
        if any(rect_dist(p, d["width"], d["height"], x / 2, z / 2) <= th for (x, z) in net.cost):
            n += 1
    print("threshold", th, "touching production buildings", n, "of", len(prod))
print("road edges by guid", collections.Counter(g for g, *_ in a["roads"]))
print("aqueduct/other road guids names", {g: gd.name(g, "english") for g in {g for g, *_ in a["roads"]}})
