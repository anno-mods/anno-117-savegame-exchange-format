import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, struct, json
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream, show
f=sys.argv[1]; key=int(sys.argv[2]); md=int(sys.argv[3]); mk=int(sys.argv[4]); sub=sys.argv[5]
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
for p,n in stream(f, lambda p: p[-1]=="AreaInfo" and len(p)==3):
    ks=n.kids
    for i in range(0,len(ks)-1,2):
        if u(ks[i].text)==key:
            v=ks[i+1]
            print([ (k.tag,len(k.kids)) for k in v.kids])
            t=v
            for q in sub.split("/"):
                if q: t=t.get(q)
            show(t,0,md,None,mk)
