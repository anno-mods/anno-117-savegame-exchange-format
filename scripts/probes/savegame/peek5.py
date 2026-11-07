import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.path.insert(0, _SCRATCH)
from tree import *
X = (_SCRATCH + r"\x\session_%s.xml") % sys.argv[1]
area = sys.argv[2]
comp = sys.argv[3]
cnt = int(sys.argv[4])
def want(p):
    return len(p) == 5 and p[-1] == "AreaObjectManager" and p[-2] == "AreaManager_" + area
for path, n in stream(X, want):
    objs = n.find("GameObject/objects")
    shown = 0
    for o in objs.kids:
        c = o.get(comp)
        if c is not None and shown < cnt:
            print("guid", o.get("guid").text, "ID", o.get("ID").text)
            show(c, 0, 8, maxkids=6); shown += 1
    break
