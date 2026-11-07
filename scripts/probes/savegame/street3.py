import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections, math
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SES, KEY = int(sys.argv[1]), int(sys.argv[2])
X = (_SCRATCH + r"\x\session_%d.xml") % SES
def want(p):
    return len(p) == 5 and p[-2] == "AreaManager_%d" % KEY and p[-1] in ("AreaStreetManager", "AreaObjectManager")
st = {}
for path, n in s.stream(s.Path(X), want):
    st[n.tag] = n
tiles = set()
for e in st["AreaStreetManager"].find("Graph/Edges").kids:
    ed = e.get("Edge"); a, b = ed.get("PosMin").text, ed.get("PosMax").text
    x1, z1, x2, z2 = s.u32(a[:8]), s.u32(a[8:]), s.u32(b[:8]), s.u32(b[8:])
    n = max(abs(x2 - x1), abs(z2 - z1)) // 2
    for i in range(n + 1):
        tiles.add((x1 / 2 + (x2 - x1) / 2 * i / n, z1 / 2 + (z2 - z1) / 2 * i / n))
tiles = list(tiles)
print("road tile points", len(tiles))
def dist(o, w, h, px, pz):
    ang = o[3]
    dx, dz = px - o[1], pz - o[2]
    lx = dx * math.cos(ang) + dz * math.sin(ang)
    lz = -dx * math.sin(ang) + dz * math.cos(ang)
    ex, ez = max(abs(lx) - w / 2, 0), max(abs(lz) - h / 2, 0)
    return math.hypot(ex, ez)
objs = []
for o in st["AreaObjectManager"].find("GameObject/objects").kids:
    g = o.get("guid"); p = o.get("Position"); d = o.get("Direction")
    if g is None or p is None or len(p.text) != 24:
        continue
    gg = s.u32(g.text)
    b = gd.buildings.get(gg)
    if not b or b.get("template") in (None,) or "Road" in (b.get("name") or ""):
        continue
    if gg in gd.residences or gg in gd.factories:
        objs.append((gg, s.f32(p.text[:8]), s.f32(p.text[16:]), s.f32(d.text) if d is not None else 0.0))
print("objects", len(objs))
for conv in ("wh", "hw"):
    hist = collections.Counter()
    for o in objs:
        b = gd.buildings[o[0]]
        w, h = (b["width"], b["height"]) if conv == "wh" else (b["height"], b["width"])
        m = min(dist(o, w, h, px, pz) for px, pz in tiles if abs(px - o[1]) < 20 and abs(pz - o[2]) < 20) if any(abs(px - o[1]) < 20 and abs(pz - o[2]) < 20 for px, pz in tiles) else 99
        hist[round(min(m, 5) * 4) / 4] += 1
    print(conv, sorted(hist.items()))
