from common import *
from trade_derive import derive
d, params, plan, save, rep = load()
ids = [i["id"] for i in plan["islands"]]
w, e, diag = derive(save, ids)
pl = {(i["id"], int(p)) for i in plan["islands"] for p in i["supplied_by"]}
miss = set(w) - pl
rt = collections.Counter()
for (rid, s, r, p), wt in e.items():
    if (r, p) in miss:
        rt[rid] += 1
print(rt)
for rid in rt:
    print(diag[rid])
# what do these routes have in common vs others
ships0 = [rid for rid, x in diag.items() if x["ships"] == 0]
print("routes with 0 ships", ships0)
print(len(save["empire"]["routes"]))
