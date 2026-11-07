from common import *
from trade_derive import derive
d, params, plan, save, rep = load()
ids = [i["id"] for i in plan["islands"]]
w, e, diag = derive(save, ids, True)
pn = {int(i["id"][1:]): i["name"] for i in plan["islands"]}
PROD = {p["guid"]: p["locaText"].get("english") for p in params["products"]}
V = json.load(open(SP + r"\trade\visits.json", encoding="utf-8"))
for rid, dg in sorted(diag.items()):
    for prod in dg["no_source"]:
        nets = collections.defaultdict(int); n = collections.Counter()
        for x in V:
            if x["route"] == rid and x["trader"] == 41:
                for g in x["goods"]:
                    if g[0] == prod:
                        nets[pn.get(x["island"], "NPC%d" % x["island"])] += g[1]; n[x["island"]] += 1
        print(rid, dg["name"], PROD.get(prod), dict(nets))
print("noships:", [r for r, x in diag.items() if x.get("noships_skipped")])
