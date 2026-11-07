import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections, struct
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream, show
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
for si in range(3):
  for p,n in stream(r"x\session_%d.xml"%si, lambda p: p[-1]=="ItemMap" and len(p)==4):
    ks=n.kids; tags=collections.Counter(); ne=collections.Counter(); ex={}
    for i in range(0,len(ks)-1,2):
        e=ks[i+1]
        for k in e.kids:
            tags[k.tag]+=1
            if k.kids or k.text: ne[k.tag]+=1; ex.setdefault(k.tag,[]).append(k)
    print(si,len(ks)//2,dict(tags),dict(ne))
    for t in ("EffectID","BoostCondition","IsBoosted"):
        if t in ex:
            print(t, [ (k.text if not k.kids else (k.tag,[ (c.tag,c.text,len(c.kids)) for c in k.kids])) for k in ex[t][:3]])
