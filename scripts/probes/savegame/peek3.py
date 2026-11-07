import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.path.insert(0, _SCRATCH)
from tree import *
X = (_SCRATCH + r"\x\data_raw.xml")
want = sys.argv[1]
depth = int(sys.argv[2])
skip = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
def w(p):
    return p[-1] == want
for path, n in stream(X, w):
    n.kids = [k for k in n.kids if k.tag not in skip]
    show(n, 0, depth, maxkids=4)
    break
