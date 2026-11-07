import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream, show
key=sys.argv[1]; oid=sys.argv[2]; f=sys.argv[3]; md=int(sys.argv[4])
def want(p): return len(p)==8 and p[-5]=="AreaManager_"+key and p[-3]=="GameObject" and p[-2]=="objects" 
for p,n in stream(f, want):
    i=n.get("ID")
    if i is not None and i.text==oid:
        show(n,0,md,None,50); break
