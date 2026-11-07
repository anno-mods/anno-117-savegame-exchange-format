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
def f(h): return struct.unpack("<f",bytes.fromhex(h))[0]
for p,n in stream(r"x\data_raw.xml", lambda p: p[-1]=="History" and len(p)>=3 and p[1]=="MetaGameManager"):
    ah=n.get("areaHistory")
    ks=ah.kids
    out={}
    for i in range(0,len(ks)-1,2):
        area=u(ks[i].text); snaps=ks[i+1].get("Snapshots").kids
        L=[]
        for s in snaps:
            def pairs(tag,conv):
                k=s.get(tag).kids
                return {u(k[j].text):conv(k[j+1].text) for j in range(0,len(k)-1,2)}
            L.append({"t":u(s.get("CreationTime").text),"amt":pairs("AmountPerProduct",u),"gen":pairs("GenerationPerProduct",f),"con":pairs("ConsumptionPerProduct",f),"app":len(s.get("AmountPerPopulation").kids)})
        out[area]=L
    json.dump(out,open(r"research2\hist.json","w"))
    print(len(out), {a:len(v) for a,v in list(out.items())[:5]})
    a=8513; L=out[a]
    print([x["t"] for x in L]); print([x["t"]-y["t"] for x,y in zip(L[1:],L)])
    for x in L[:2]+L[-1:]:
        print(x["t"], len(x["amt"]), len(x["gen"]))
        print({gd.name(g,"english"):v for g,v in list(x["amt"].items())[:8]})
        print({gd.name(g,"english"):round(v,3) for g,v in list(x["gen"].items()) if v})
        print({gd.name(g,"english"):round(v,3) for g,v in list(x["con"].items()) if v})
    print("lastSnapshot",u(n.get("lastSnapshot").text))
    break
