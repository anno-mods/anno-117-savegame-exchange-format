import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream, show
key=sys.argv[1]; sub=sys.argv[2]; md=int(sys.argv[3]); mk=int(sys.argv[4]); f=sys.argv[5]
for p,n in stream(f, lambda p: len(p)==5 and p[-2]=="AreaManager_"+key and p[-1]==sub):
    show(n,0,md,None,mk); break
