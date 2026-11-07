import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, struct, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
def f(h): return struct.unpack("<f",bytes.fromhex(h))[0]
for tag in ("Effects","LocalEffects"):
  for p,n in stream(r"x\data_raw.xml", lambda p,t=tag: p[-1]==t and len(p)>=3 and p[1]=="MetaGameManager" and p[2]=="MetaEffectManager"):
    items=[]
    if tag=="Effects": items=[(None,e) for e in n.kids]
    else:
        ks=n.kids
        for i in range(0,len(ks)-1,2):
            for e in ks[i+1].kids: items.append((u(ks[i].text),e))
    c=collections.Counter(); 
    for o,e in items:
        sf=e.get("ScalingFactor")
        if sf is not None: c[(u(e.get("Guid").text),round(f(sf.text),3))]+=1
    print(tag,len(items),"with scale",sum(c.values()))
    for (g,s),k in list(c.items())[:8]: print("  ",g,gd.name(g,"english"),s,k)
    print("tags", collections.Counter(k.tag for o,e in items for k in e.kids))
