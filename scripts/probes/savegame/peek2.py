import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.path.insert(0, _SCRATCH)
from tree import *
X = (_SCRATCH + r"\x\session_%s.xml") % sys.argv[1]
target = "AreaManager_%s" % sys.argv[2]
mgr = sys.argv[3]
depth = int(sys.argv[4]) if len(sys.argv) > 4 else 6
def want(p):
    return len(p) == 4 and p[-1] == target
for path, n in stream(X, want):
    print([(k.tag, len(k.kids)) for k in n.kids])
    m = n.get(mgr)
    if m: show(m, 0, depth, maxkids=3)
    break
