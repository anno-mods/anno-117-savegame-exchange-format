import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.path.insert(0, _SCRATCH)
from tree import *
X = (_SCRATCH + r"\x\session_0.xml")
def want(p):
    return len(p) == 5 and p[-1] == "AreaObjectManager" and p[-2] == "AreaManager_8513"
for path, n in stream(X, want):
    objs = n.find("GameObject/objects")
    tagcount = {}
    shown = 0
    for o in objs.kids:
        for k in o.kids:
            tagcount[k.tag] = tagcount.get(k.tag, 0) + 1
        if shown < 3 and any(k.tag not in ("guid", "ID", "SkinGuid", "ObjectFolderID", "Position", "Direction", "OwnerProfile", "Mesh") for k in o.kids):
            show(o, 0, 7, maxkids=5); shown += 1
    print(tagcount)
    break
