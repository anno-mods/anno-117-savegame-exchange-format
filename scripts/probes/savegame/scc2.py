import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, pickle, collections, heapq, math
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
by = {p["id"]: p for p in a["placed"]}
net = s.StreetNet(a, gd)
def fp(g):
    d = gd.buildings.get(g) or (gd.factories[g].raw if g in gd.factories else {})
    return (d["width"], d["height"]) if d.get("width") else (1, 1)
lib = by["2201000004220000"]
start = net.touching(lib, *fp(lib["building"]))
def dij(unit):
    best = {}
    heap = []
    for p in start:
        c = 1.0 if unit else net.cost[p]
        best[p] = c; heapq.heappush(heap, (c, p))
    while heap:
        d, p = heapq.heappop(heap)
        if d > best[p]:
            continue
        for q in net.link.get(p, ()):
            nd = d + (1.0 if unit else net.cost[q])
            if nd < best.get(q, 1e9):
                best[q] = nd; heapq.heappush(heap, (nd, q))
    return best
w = dij(False); u = dij(True)
for pid in ["2F01000004220000", "6101000004220000", "6201000004220000"]:
    p = by[pid]
    t = net.touching(p, *fp(p["building"]))
    print(gd.name(p["building"], "english"), pid, "weighted cost", round(min((w[x] for x in t if x in w), default=-1), 1), "hops", min((u[x] for x in t if x in u), default=-1), "touch tiles", len(t), "circle", round(math.hypot(p["x"] - lib["x"], p["z"] - lib["z"]), 1))
# distribution of cost for production buildings in cache list vs not
X = SP + r"\x\session_2.xml"
def want(pth):
    return len(pth) == 5 and pth[-2] == "AreaManager_8708" and pth[-1] == "AreaEffectManager"
for path, n in s.stream(s.Path(X), want):
    kids = n.get("StreetConnectionCache").kids
    ent = {kids[i].text: [c.text for c in kids[i + 1].kids] for i in range(0, len(kids) - 1, 2)}
inl = set(ent["2201000004220000"])
costs_in, costs_out = [], []
for p in a["placed"]:
    if p["building"] not in gd.factories:
        continue
    t = net.touching(p, *fp(p["building"]))
    c = min((w[x] for x in t if x in w), default=None)
    (costs_in if p["id"] in inl else costs_out).append((None if c is None else round(c, 1), gd.name(p["building"], "english")))
print("IN list max costs", sorted([c for c, _ in costs_in if c is not None])[-6:], "none:", [n for c, n in costs_in if c is None])
print("OUT list", costs_out)
# all object types in list vs touching reach
print("list size", len(inl), "types", collections.Counter(gd.name(by[i]["building"], "english") if i in by else "?" for i in inl).most_common(8))
