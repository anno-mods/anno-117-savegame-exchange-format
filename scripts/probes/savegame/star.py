import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, math, pickle, os
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
cache = SP + r"\x\areas_s2.pkl"
if os.path.exists(cache):
    areas = pickle.load(open(cache, "rb"))
else:
    areas = s.read_session(s.Path(SP + r"\x\session_2.xml"))
    pickle.dump(areas, open(cache, "wb"))
KEY = int(sys.argv[1]) if len(sys.argv) > 1 else 8708
a = next(x for x in areas if x["key"] == KEY)
net = s.StreetNet(a, gd)
by_id = {p["id"]: p for p in a["placed"]}
libs = [e for e in a["effects"] if e["guid"] == 153868]
print("library records", [(e["source"], e["scope"], e["distance"]) for e in libs])
targets = set(gd.effects[153868]["targets"])
def fp(g):
    f = gd.factories.get(g)
    d = gd.buildings.get(g) or (f.raw if f else {})
    return (d["width"], d["height"]) if d.get("width") else None
prod = [p for p in a["placed"] if p["building"] in gd.factories]
print("production buildings", len(prod), "of effect targets", sum(p["building"] in targets for p in prod))
res = {}
for lib in libs:
    src = by_id[lib["source"]]
    st = net.touching(src, *fp(src["building"]))
    reached = net.reach(st, lib["distance"])
    for p in prod:
        f = fp(p["building"])
        t = net.touching(p, *f) if f else None
        res.setdefault(p["id"], {"p": p, "by": []})
        if f is None:
            res[p["id"]]["by"].append((lib["source"], "nofootprint-circle", math.hypot(p["x"] - src["x"], p["z"] - src["z"]) <= lib["distance"]))
        else:
            res[p["id"]]["by"].append((lib["source"], "street", bool(t & reached)))
print("lib source tiles", len(st), "reached tiles", len(reached), "of", len(net.cost))
un = []
for pid, r in res.items():
    ok = any(x[2] for x in r["by"])
    if not ok:
        un.append(r["p"])
print("UNREACHED:", len(un))
for p in un:
    print("  ", gd.name(p["building"], "english"), p["building"], p["id"], (round(p["x"], 1), round(p["z"], 1)), "in effect targets" if p["building"] in targets else "NOT a target", "footprint", fp(p["building"]))
# nearest road distance for unreached
for p in un:
    f = fp(p["building"])
    print("  unreached touch tiles:", len(net.touching(p, *f)) if f else None)
import collections
print("reached by type", collections.Counter(gd.name(r["p"]["building"], "english") for r in res.values() if any(x[2] for x in r["by"])).most_common(5))
