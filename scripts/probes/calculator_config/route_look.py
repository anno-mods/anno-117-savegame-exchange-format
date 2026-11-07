from common import *
d, params, plan, save, rep = load()
E = save["empire"]
areas = {a["key"]: a for s in save["sessions"] for a in s}
pn = {i["id"]: i["name"] for i in plan["islands"]}
def nm(a): return pn.get("a%d" % a, "non-player %d" % a)
for prod, label in ((31698, "Gold"), (151703, "Ivory Caskets")):
    print("=====", label)
    for rid, r in E["routes"].items():
        hit = [i for i, st in enumerate(r["stations"]) if any(sl["product"] == prod for sl in st["slots"])]
        if not hit: continue
        print("route", rid, r["name"], "ships", r["ships"])
        for i, st in enumerate(r["stations"]):
            sl = ["%s%s%s" % ("L" if x["load"] else "U", x["product"], "(%s)" % x["amount"] if x["amount"] else "") for x in st["slots"]]
            print("  ", i, nm(st["area"]), st["area"], st["owner"], sl)
        for st in r["stations"]:
            a = areas.get(st["area"])
            if a and rid in a["visits"]:
                v = a["visits"][rid]
                print("   visits at", nm(st["area"]), len(v), "first", v[0], "last", v[-1])
