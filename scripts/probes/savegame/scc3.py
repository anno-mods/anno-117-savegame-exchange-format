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
KEY = 8708
a = next(x for x in areas if x["key"] == KEY)
by = {p["id"]: p for p in a["placed"]}
net = s.StreetNet(a, gd)
def fp(g):
    d = gd.buildings.get(g) or (gd.factories[g].raw if g in gd.factories else {})
    return (d["width"], d["height"]) if d.get("width") else None
X = SP + r"\x\session_2.xml"
def want(pth):
    return len(pth) == 5 and pth[-2] == "AreaManager_%d" % KEY and pth[-1] == "AreaEffectManager"
for path, n in s.stream(s.Path(X), want):
    kids = n.get("StreetConnectionCache").kids
    ent = {kids[i].text: [c.text for c in kids[i + 1].kids] for i in range(0, len(kids) - 1, 2)}
LIB = "2201000004220000"
inl = set(ent[LIB])
lib = by[LIB]
start = net.touching(lib, *fp(lib["building"]))
def step_cost(metric, p, q):
    paved = net.cost[q] < 1.0
    dx, dz = abs(q[0] - p[0]), abs(q[1] - p[1])
    length = math.hypot(dx, dz) / 2  # tiles
    base = {"hops": 1.0, "weighted": net.cost[q], "euclid": length, "euclid_w": length * net.cost[q], "chebyshev_w": net.cost[q]}[metric]
    return base
def dij(metric, init):
    best = {}
    heap = []
    for p in start:
        c = init(metric, p)
        best[p] = c; heapq.heappush(heap, (c, p))
    while heap:
        d, p = heapq.heappop(heap)
        if d > best[p]:
            continue
        for q in net.link.get(p, ()):
            nd = d + step_cost(metric, p, q)
            if nd < best.get(q, 1e9):
                best[q] = nd; heapq.heappush(heap, (nd, q))
    return best
objs = [p for p in a["placed"] if fp(p["building"]) and "Road" not in (gd.buildings.get(p["building"], {}).get("name") or "") and (p["building"] in gd.factories or p["building"] in gd.residences)]
for metric in ("hops", "weighted", "euclid", "euclid_w"):
    for init_name, init in (("start=0", lambda m, p: 0.0), ("start=step", lambda m, p: step_cost(m, p, p) if m == "hops" else net.cost[p])):
        best = dij(metric, init)
        ins, outs = [], []
        for p in objs:
            t = net.touching(p, *fp(p["building"]))
            c = min((best[x] for x in t if x in best), default=None)
            if c is None:
                continue
            (ins if p["id"] in inl else outs).append(c)
            if p["id"] not in inl and metric in ("weighted", "euclid_w", "hops") and init_name == "start=0":
                print("   OUT", metric, gd.name(p["building"], "english"), p["id"][:4], round(c, 1))
        print(metric, init_name, "IN n", len(ins), "max", round(max(ins), 1) if ins else None, "| OUT n", len(outs), "min", round(min(outs), 1) if outs else None, "| OUT below 62:", sum(c <= 62 for c in outs), " IN above 62:", sum(c > 62 for c in ins))
