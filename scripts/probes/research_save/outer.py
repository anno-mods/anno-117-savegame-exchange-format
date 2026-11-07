import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream, show
tag=sys.argv[1]; md=int(sys.argv[2]); mk=int(sys.argv[3]); f=sys.argv[4]
for p,n in stream(f, lambda p: p[-1]==tag and len(p)>=3 and p[1]=="MetaGameManager"):
    show(n,0,md,None,mk); break
