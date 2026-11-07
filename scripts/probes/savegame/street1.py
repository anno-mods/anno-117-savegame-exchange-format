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
X = (_SCRATCH + r"\x\session_2.xml")
KEY = int(sys.argv[1])
def want(p):
    return len(p) == 5 and p[-2] == "AreaManager_%d" % KEY and p[-1] in ("AreaStreetManager", "AreaEffectManager")
st = {}
for path, n in s.stream(s.Path(X), want):
    st[n.tag] = n
def dump(n, d=0, mx=3, maxd=6):
    print("  " * d + n.tag + (" = " + n.text[:70] if n.text else "") + (f" [{len(n.kids)}]" if n.kids else ""))
    if d < maxd:
        for k in n.kids[:mx]:
            dump(k, d + 1, mx, maxd)
dump(st["AreaStreetManager"], 0, 3, 8)
