import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream, show
key=sys.argv[1]; f=sys.argv[2]
def want(p): return len(p)==8 and p[-5]=="AreaManager_"+key and p[-3]=="GameObject" and p[-2]=="objects"
c=collections.Counter(); ne=collections.Counter(); ex={}
nobj=0
for p,n in stream(f, want):
    nobj+=1
    for k in n.kids:
        c[k.tag]+=1
        if k.kids or (k.text not in (None,"")): ne[k.tag]+=1; ex.setdefault(k.tag,k)
print(nobj)
for t,v in c.most_common(): print(t,v,ne[t])
