import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, struct, json
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
def i32(h): return int.from_bytes(bytes.fromhex(h),"little",signed=True)
def f(h): return struct.unpack("<f",bytes.fromhex(h))[0]
for p,n in stream(r"x\session_0.xml", lambda p: p[-1]=="AreaInfo" and len(p)==3):
    ks=n.kids
    for i in range(0,len(ks)-1,2):
        if u(ks[i].text)==8513:
            v=ks[i+1]; st=v.find("AreaEconomy/StorageTrends").kids
            print(len(st)//2)
            res={}
            for j in range(0,len(st)-1,2):
                g=u(st[j].text); e=st[j+1]; pts=e.get("Points")
                print(g,gd.name(g,"english"),[(k.tag,k.text,len(k.kids)) for k in pts.kids[:3]], [(k.tag,k.text) for k in pts.kids[-4:]], e.get("LastPointTime").text, e.get("Estimation").text) if j<8 else None
                vals=[k for k in pts.kids if k.tag=="None"]
                res[g]=[u(k.text) for k in vals]
            H=json.load(open(r"research2\hist.json"))["8513"]
            for g in (2071,2063,2063):
                pass
            lard=[g for g in res if gd.name(g,"english")=="Lard"][0]
            print("hist lard", [x["amt"][str(lard)] for x in H]); print("points lard", res[lard])
            print("LPT", u(v.find("AreaEconomy/StorageTrends").kids[1].get("LastPointTime").text))
