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
targets = set(gd.effects[153868]["targets"])
pts = [(x / 2, z / 2, (x, z)) for (x, z) in net.cost]
def touching(p, w, h, sign, th):
    ang = sign * p["angle"]; cos, sin = math.cos(ang), math.sin(ang)
    out = set()
    for x, z, key in pts:
        if abs(x - p["x"]) > 20 or abs(z - p["z"]) > 20:
            continue
        dx, dz = x - p["x"], z - p["z"]
        lx, lz = dx * cos + dz * sin, -dx * sin + dz * cos
        if math.hypot(max(abs(lx) - w / 2, 0), max(abs(lz) - h / 2, 0)) <= th:
            out.add(key)
    return out
def reach(start, metric, budget):
    best = {}; heap = []
    for p in start:
        best[p] = 0.0; heapq.heappush(heap, (0.0, p))
    while heap:
        d, p = heapq.heappop(heap)
        if d > best[p]:
            continue
        for q in net.link.get(p, ()):
            length = math.hypot(q[0] - p[0], q[1] - p[1]) / 2
            step = {"layout": net.cost[q], "euclid_w": length * net.cost[q]}[metric]
            nd = d + step
            if nd <= budget and nd < best.get(q, 1e9):
                best[q] = nd; heapq.heappush(heap, (nd, q))
    return set(best)
objs = [p for p in a["placed"] if fp(p["building"]) and (p["building"] in gd.factories or p["building"] in gd.residences)]
lib = by[LIB]
for sign in (1, -1):
    for th in (0.75, 1.0):
        tmap = {p["id"]: touching(p, *fp(p["building"]), sign, th) for p in objs}
        lt = touching(lib, *fp(lib["building"]), sign, th)
        for metric in ("layout", "euclid_w"):
            r = reach(lt, metric, 62)
            fn = fp_ = 0; prod_un = []
            for p in objs:
                pred = bool(tmap[p["id"]] & r)
                tr = p["id"] in inl
                if p["building"] in gd.factories and p["building"] in targets and not pred:
                    prod_un.append(gd.name(p["building"], "english"))
                if pred and not tr: fp_ += 1
                if tr and not pred: fn += 1
            print("sign", sign, "touch", th, metric, "| false+", fp_, "false-", fn, "| unreached targeted production:", len(prod_un), collections.Counter(prod_un))
