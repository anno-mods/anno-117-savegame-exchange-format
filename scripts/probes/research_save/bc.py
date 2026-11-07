import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
conds={}
for p,n in stream(r"x\data_raw.xml", lambda p: p[-1]=="Conditions" and len(p)>=3 and p[1]=="MetaGameManager"):
    for c in n.kids:
        k=c.get("conditionKey")
        if k is None: continue
        key=bytes.fromhex(k.text).decode("ascii","replace")
        if key.startswith("ItemBoost_"):
            _,g,i=key.split("_")
            res=c.get("Result"); 
            conds[int(i)]=dict(guid=int(g),resolved=c.get("IsResolved") is not None,result=(res.kids[0].text if res is not None and res.kids else None),active=c.get("IsActive") is not None,counter=u(c.get("PlayerCounter").kids[0].text) if c.get("PlayerCounter") is not None and c.get("PlayerCounter").kids else None, amount=u(c.get("CounterAmount").text) if c.get("CounterAmount") is not None else None, op=c.get("ComparisonOp") and c.get("ComparisonOp").kids and c.get("ComparisonOp").kids[0].text, tags=[x.tag for x in c.kids if x.tag in("IsResolved","Result","IsActive","IsPermanent")])
print(len(conds))
import json
items={}
for si in range(3):
  for p,n in stream(r"x\session_%d.xml"%si, lambda p: p[-1]=="ItemMap" and len(p)==4):
    ks=n.kids
    for i in range(0,len(ks)-1,2):
        e=ks[i+1]; iid=u(e.get("ItemID").text); bc=e.get("BoostCondition")
        key=None
        if bc is not None and bc.kids: key=bytes.fromhex(bc.kids[0].text).decode()
        items[iid]=dict(session=si,guid=u(e.get("GUID").text),boosted=e.get("IsBoosted") is not None,cond=key)
cc=collections.Counter()
for iid,it in items.items():
    if it["cond"]:
        i=int(it["cond"].split("_")[2]); c=conds.get(i)
        cc[(it["boosted"], None if c is None else (c["resolved"],c["result"],c["active"]))]+=1
print(cc)
ex=[(iid,it,conds.get(int(it["cond"].split("_")[2]))) for iid,it in items.items() if it["cond"]][:3]
for e in ex: print(e)
print("boosted without cond",sum(1 for it in items.values() if it["boosted"] and not it["cond"]))
json.dump({"items":{str(k):v for k,v in items.items()},"conds":{str(k):v for k,v in conds.items()}},open(r"research2\boost.json","w"))
