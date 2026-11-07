import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, math, pickle, collections
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
def dims(g):
    d = gd.buildings.get(g) or (gd.factories[g].raw if g in gd.factories else {})
    return (d["width"], d["height"]) if d.get("width") else None
def rect_dist(p, w, h, px, pz, sign, off=0.0):
    ang = sign * p["angle"]
    cos, sin = math.cos(ang), math.sin(ang)
    dx, dz = px - p["x"], pz - p["z"]
    lx, lz = dx * cos + dz * sin, -dx * sin + dz * cos
    return math.hypot(max(abs(lx) - w / 2, 0), max(abs(lz) - h / 2, 0))
for a in areas:
    net = s.StreetNet(a, gd)
    pts = [(x / 2, z / 2) for (x, z) in net.cost]
    res = {}
    for variant in ("+wh", "-wh", "+hw", "-hw"):
        sign = 1 if variant[0] == "+" else -1
        swap = variant[1:] == "hw"
        hist = collections.Counter(); diag = collections.Counter()
        for p in a["placed"]:
            d = dims(p["building"])
            if not d or not (p["building"] in gd.factories or p["building"] in gd.residences):
                continue
            w, h = (d[1], d[0]) if swap else d
            m = min((rect_dist(p, w, h, x, z, sign) for x, z in pts if abs(x - p["x"]) < 20 and abs(z - p["z"]) < 20), default=99)
            ok = m <= 0.75
            hist["ok" if ok else "no"] += 1
            if abs(math.sin(2 * p["angle"])) > 0.5:
                diag["ok" if ok else "no"] += 1
        res[variant] = (dict(hist), dict(diag))
    print(a["key"], res)
