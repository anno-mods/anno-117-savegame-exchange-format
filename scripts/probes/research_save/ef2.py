import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections, struct
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
shown=collections.Counter(); sp=0
for si in range(3):
  for p,n in stream(r"x\session_%d.xml"%si, lambda p: len(p)==5 and p[-2].startswith("AreaManager_") and p[-1]=="AreaEffectManager"):
    for e in n.get("Effects").kids:
        tags={k.tag for k in e.kids}
        for t in ("ScalingFactor","SourcePosition","TargetArea","ModuleOwner","IsBoostedItem"):
            if t in tags and shown[t]<2:
                shown[t]+=1
                g=u(e.get("Guid").text)
                print(p[-2],t,"guid",g,gd.name(g,"english"),{k.tag:(k.text if k.text is not None else [(x.tag,x.text) for x in k.kids]) for k in e.kids if k.tag not in("Scope",)})
