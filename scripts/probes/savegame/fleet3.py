import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
allfx = {int(k): v for k, v in gd.ships["effects"].items()}
def show(n, d=0, maxd=4, mx=8):
    print("  " * d + n.tag + (" = " + n.text[:70] if n.text else "") + (f" [{len(n.kids)}]" if n.kids else ""))
    if d < maxd:
        for k in n.kids[:mx]:
            show(k, d + 1, maxd, mx)
for path, node in s.stream(s.Path(SP + r"\x\data_raw.xml"), lambda p: p[-1] == "MetaEffectManager"):
    effs = node.get("Effects")
    n = 0
    byguid = collections.Counter()
    for e in effs.kids:
        g = e.get("Guid")
        if g is None: continue
        gv = s.u32(g.text)
        byguid[gv] += 1
        if gv in allfx and n < 20:
            print("SHIP EFFECT", gv, allfx[gv]["loca"].get("english") if allfx[gv].get("loca") else allfx[gv]["name"], [(k.tag, k.text if k.text else len(k.kids)) for k in e.kids if k.tag in ("Scope", "TargetParticipant", "Source", "EndTimestamp", "Id")])
            n += 1
    print("distinct guids", len(byguid), "ship effects present:", {g: c for g, c in byguid.items() if g in allfx})
    print("first record:")
    show(effs.kids[0], 0, 4)
    # participants
    break
