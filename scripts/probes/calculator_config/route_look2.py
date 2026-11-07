from common import *
d, params, plan, save, rep = load()
E = save["empire"]
pn = {i["id"]: i["name"] for i in plan["islands"]}
PROD = {p["guid"]: p["locaText"].get("english") for p in params["products"]}
def nm(a): return pn.get("a%d" % a, "NPC %d" % a)
for rid in (107, 9, 46, 51, 53, 61, 71, 84, 95, 115):
    r = E["routes"][rid]
    print("== route", rid, r["name"], "ships", r["ships"])
    for i, st in enumerate(r["stations"]):
        by = collections.defaultdict(lambda: [0, 0])
        for sl in st["slots"]:
            by[sl["product"]][0 if sl["load"] else 1] += 1
        print("  ", i, nm(st["area"]), "owner", st["owner"], {PROD.get(p, p): ("L%d" % a if a and not b else "U%d" % b if b and not a else "L%dU%d" % (a, b)) for p, (a, b) in by.items()})
