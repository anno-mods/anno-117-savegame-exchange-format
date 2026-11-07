import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
from tree import stream, show
key=sys.argv[1]; f=sys.argv[2]; comp=sys.argv[3]; cnt=int(sys.argv[4]); md=int(sys.argv[5])
def want(p): return len(p)==8 and p[-5]=="AreaManager_"+key and p[-3]=="GameObject" and p[-2]=="objects"
k=0
for p,n in stream(f, want):
    c=n.get(comp)
    if c is not None and (c.kids or c.text):
        print("== guid",n.get("guid").text,"ID",n.get("ID").text,"pos",n.get("Position").text,"dir",n.get("Direction") and n.get("Direction").text)
        show(c,0,md,None,12); k+=1
        if k>=cnt: break
