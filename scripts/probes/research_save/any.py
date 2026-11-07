import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream, show
f=sys.argv[1]; tag=sys.argv[2]; ln=int(sys.argv[3]); md=int(sys.argv[4]); mk=int(sys.argv[5])
for p,n in stream(f, lambda p: p[-1]==tag and len(p)==ln):
    show(n,0,md,None,mk); break
