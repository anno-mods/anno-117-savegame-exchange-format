import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
X = (_SCRATCH + r"\x\session_2.xml")
def want(p):
    return len(p) == 5 and p[-2] == "AreaManager_25668" and p[-1] in ("AreaIrrigationManager", "AreaObjectManager")
st = {}
for path, n in s.stream(s.Path(X), want):
    st[n.tag] = n
def dump(n, d=0, mx=4, maxd=4):
    print("  " * d + n.tag + (" = " + n.text[:60] if n.text else "") + (f" [{len(n.kids)}]" if n.kids else ""))
    if d < maxd:
        for k in n.kids[:mx]:
            dump(k, d + 1, mx, maxd)
dump(st["AreaIrrigationManager"])
objs = [o for o in st["AreaObjectManager"].find("GameObject/objects").kids if o.get("guid") is not None]
for g in (152151, 152142, 151994, 152107, 152143, 152153):
    c = collections.Counter()
    for o in objs:
        if s.u32(o.get("guid").text) == g:
            a = o.get("AqueductConsumer")
            c[(len(a.get("DistributorsInRange").kids) if a is not None and a.get("DistributorsInRange") is not None else None, a.get("IsDemandingWater").text if a is not None and a.get("IsDemandingWater") is not None else None)] += 1
    print(g, gd.name(g, "english"), dict(c))
