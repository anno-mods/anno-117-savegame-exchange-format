import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections
sys.path.insert(0,_SCRATCH)
from tree import stream
c=collections.Counter(); n_=0
for si in range(3):
  for p,n in stream(r"x\session_%d.xml"%si, lambda p: len(p)==5 and p[-2].startswith("AreaManager_") and p[-1]=="AreaEffectManager"):
    for e in n.get("Effects").kids:
        n_+=1
        for k in e.kids: c[k.tag]+=1
print(n_,dict(c))
