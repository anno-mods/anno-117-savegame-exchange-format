import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
for p,n in stream(r"x\session_0.xml", lambda p: p[-1]=="AreaInfo" and len(p)==3):
    ks=n.kids
    for i in range(0,len(ks)-1,2):
        v=ks[i+1]; k=u(ks[i].text)
        st=v.find("AreaEconomy/StorageTrends")
        if st is None or not st.kids: print(k,"no trends", v.get("OwnerProfile") and v.get("OwnerProfile").text); continue
        lp=collections.Counter(u(st.kids[j].get("LastPointTime").text) for j in range(1,len(st.kids),2))
        print(k,dict(lp), "StrgLrg" , v.find("AreaEconomy/StrgLrg").text[:40] if v.find("AreaEconomy/StrgLrg") is not None else None, "TradeStorage", v.find("AreaEconomy/TradeStorage") is not None)
