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
edges = []
for e in st["AreaStreetManager"].find("Graph/Edges").kids:
    g = s.u32(e.get("guid").text); ed = e.get("Edge")
    a, b = ed.get("PosMin").text, ed.get("PosMax").text
    edges.append((g, (s.u32(a[:8]), s.u32(a[8:])), (s.u32(b[:8]), s.u32(b[8:]))))
cnt = collections.Counter(e[0] for e in edges)
for g, c in cnt.most_common(8):
    print("edge guid", g, gd.name(g, "english"), (gd.buildings.get(g) or {}).get("template"), c)
lens = collections.Counter(max(abs(a[0] - b[0]), abs(a[1] - b[1])) for _, a, b in edges)
print("edge lengths (half tiles)", sorted(lens.items())[:12])
xs = [a[0] / 2 for _, a, _ in edges]; zs = [a[1] / 2 for _, a, _ in edges]
print("road x range", min(xs), max(xs), "z", min(zs), max(zs))
objs = []
for o in st["AreaObjectManager"].find("GameObject/objects").kids:
    g = o.get("guid"); p = o.get("Position"); d = o.get("Direction")
    if g is None or p is None or len(p.text) != 24:
        continue
    objs.append((s.u32(g.text), s.f32(p.text[:8]), s.f32(p.text[16:]), s.f32(d.text) if d is not None else 0.0))
print("obj x range", min(o[1] for o in objs), max(o[1] for o in objs), "z", min(o[2] for o in objs), max(o[2] for o in objs))
print("sample objs", [(gd.name(o[0], "english"), o[1:]) for o in objs[:3]], "sample edge", edges[0])
