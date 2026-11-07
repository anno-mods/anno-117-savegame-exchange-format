import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys
sys.path.insert(0, _SCRATCH)
from tree import *
X = (_SCRATCH + r"\x\data_raw.xml")
want = sys.argv[1]
def w(p):
    return p[-1] == want
i = 0
for path, n in stream(X, w):
    print("PATH", "/".join(path), [ (k.tag, k.text if k.text else len(k.kids)) for k in n.kids][:14])
    i += 1
    if i >= 3: break
