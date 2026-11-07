import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections, json
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream, show
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
def i(h): return int.from_bytes(bytes.fromhex(h),"little",signed=True) if h else 0
agg={}; tmin=10**18; tmax=0; nentries=0; ex=None
for si in range(3):
  for p,n in stream(r"x\session_%d.xml"%si, lambda p: p[-1]=="AreaInfo" and len(p)==3):
    ks=n.kids
    for a in range(0,len(ks)-1,2):
        key=u(ks[a].text); v=ks[a+1]
        te=v.find("PassiveTrade/History/TradeRouteEntries")
        if te is None: continue
        for j in range(0,len(te.kids)-1,2):
            rid=u(te.kids[j].text)
            for e in te.kids[j+1].kids:
                t=u(e.get("ExecutionTime").text); tmin=min(tmin,t); tmax=max(tmax,t); nentries+=1
                if ex is None: ex=(key,rid,[ (c.tag,[(x.tag,x.text) for x in c.kids]) for c in e.get("TradedGoods").kids[:2]], e.get("Trader").text)
                for gdn in e.get("TradedGoods").kids:
                    g=u(gdn.get("GoodGuid").text) if gdn.get("GoodGuid") is not None else u(gdn.kids[0].text); amt=i(gdn.get("GoodAmount").text)
                    d=agg.setdefault((si,key,g),[0,0,0]); d[0]+=amt; d[1]+= amt if amt>0 else 0; d[2]+= -amt if amt<0 else 0
print(nentries, tmin, tmax, ex)
for k,v in list(agg.items())[:10]: print(k,gd.name(k[2],"english"),v)
print(len(agg))
