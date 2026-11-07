import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.path.insert(0, _SCRATCH)
from tree import *
X = (_SCRATCH + r"\x\session_0.xml")
# capture AreaInfo and first AreaManager
def want(p):
    return p[-1] in ("AreaInfo",) or (len(p) == 4 and p[-2] == "AreaManagers")
seen_am = 0
for path, n in stream(X, want):
    if n.tag == "AreaInfo":
        print("AreaInfo kids", len(n.kids))
        ks = n.kids
        for i in range(0, len(ks) - 1, 2):
            key, val = ks[i], ks[i + 1]
            print(i // 2, key.text, val.get("OwnerProfile") and val.get("OwnerProfile").text, val.get("CityNameGuid") and val.get("CityNameGuid").text,
                  val.get("CityNameIterator") and val.get("CityNameIterator").text, [k.tag for k in val.kids][:12])
    else:
        print(path[-1], [ (k.tag, len(k.kids)) for k in n.kids][:40]) if seen_am < 3 else None
        seen_am += 1
