import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, struct, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream, show
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
def f(h): return struct.unpack("<f",bytes.fromhex(h))[0]
for p,n in stream(r"x\data_raw.xml", lambda p: p[-1]=="LocalEffects" and len(p)>=3 and p[1]=="MetaGameManager"):
    ks=n.kids; c=collections.Counter(); shown=0; owners=collections.Counter()
    for i in range(0,len(ks)-1,2):
        oid=u(ks[i].text); owners[oid>>32]+=1
        for e in ks[i+1].kids:
            g=u(e.get("Guid").text); c[g]+=1
            if e.get("IsBoostedItem") is not None and shown<4:
                shown+=1; print("owner",hex(oid),"guid",g,gd.name(g,"english"),"boosted",e.get("IsBoostedItem").text,"scale",e.get("ScalingFactor") and f(e.get("ScalingFactor").text), "scope",e.get("Scope").kids[0].kids[0].text,"src",e.get("Source").kids[0].text)
    print(len(c),"distinct effect guids; owner high-dword",owners.most_common(5))
    for g,k in c.most_common(8): print(g,gd.name(g,"english"),k)
