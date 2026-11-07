from common import *
from trade_derive import derive
d, params, plan, save, rep = load()
ids = [i["id"] for i in plan["islands"]]
w, e, diag = derive(save, ids)
imps = rep["trade"]["imports"]
print(len(imps), len({(i["island"], i["product"]) for i in imps}))
# plan supplied_by vs mine
pl = {}
for i in plan["islands"]:
    for p, s in i["supplied_by"].items():
        pl[(i["id"], int(p))] = s
print("plan supplied_by keys", len(pl))
only_mine = set(w) - set(pl); only_plan = set(pl) - set(w)
print(len(only_mine), len(only_plan))
print(list(only_mine)[:5], list(only_plan)[:5])
for k in list(set(w) & set(pl))[:3]:
    print(k, w[k], pl[k])
print(73 in diag, diag.get(73))
print(sorted(diag)[:10], len(diag))
