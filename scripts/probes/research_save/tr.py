import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, struct, collections, json
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream, show
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
for p,n in stream(r"x\data_raw.xml", lambda p: p[-1]=="RouteMap"):
    ks=n.kids; own=collections.Counter(); mine=[]
    for i in range(0,len(ks)-1,2):
        r=ks[i+1]; o=u(r.get("Owner").text); own[o]+=1
        if o==41: mine.append(r)
    print(own.most_common(6), "player routes", len(mine))
    shown=0
    for r in mine:
        name=bytes.fromhex(r.get("Name").text).decode("utf-16-le")
        st=r.get("Stations").kids
        gi=[s for s in st if s.get("GoodInfos").kids]
        print(u(r.get("ID").text),name,"ships",u(r.get("Ships").text),"stations",len(st),"with goods",len(gi), "type",r.find("Type/id").text, "ownerType", r.find("OwnerType/OwnerType") and r.find("OwnerType/OwnerType").text, "manual", r.get("ManuallySaved") is not None)
        if gi and shown<1:
            shown+=1
            for s in st: show(s,0,6,None,6)
        if shown>=1 and len(mine)>0: pass
    break
