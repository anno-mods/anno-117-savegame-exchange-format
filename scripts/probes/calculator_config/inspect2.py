from common import *
d, params, plan, save, rep = load()
names, stores = island_stores(d)
E = {e["guid"]: e for e in params["effects"]}
B = {b["guid"]: b for b in params["buildingBuffs"]}
for g in (153868, 174824, 158336, 158337):
    e = E[g]
    print(g, e["name"], e["effectScope"], e.get("source"), e["buffs"], [ (B[b]["name"], B[b]["productivityUpgrade"], B[b]["baseProductivityUpgrade"]) for b in e["buffs"] if b in B], e["locaText"]["english"] if "locaText" in e else None)
areas = {a["key"]: a for s in save["sessions"] for a in s}
# libraries: which building guids provide effect 153868 in the save
for k, a in areas.items():
    srcs = collections.Counter(1 for e in a["effects"] if e["guid"] == 153868)
    print(k, plan["islands"][[i["id"] for i in plan["islands"]].index("a%d" % k)]["name"], "effect153868 recs", sum(srcs.values()), "patron", a["patron"], "counts 152071:", a["counts"].get(152071))
for n in ("Aeterna",):
    s = stores[n]
    print({k: v for k, v in s.items() if "[" in k and "scaling" in k})
print([ (n["island"], n["note"]) for n in json.load(open(SP + r"\Marcia 69 updated.changes.json"))["notes"] if "not in the calculator data" in n["note"]])
# island.effect keys in old that are building-sourced
c = collections.Counter()
for n, s in stores.items():
    for k, v in s.items():
        m = re.match(r"island\.effect\.(\d+)\.scaling$", k)
        if m and int(m.group(1)) in E and E[int(m.group(1))].get("source") == "building":
            c[(int(m.group(1)), n)] += 1
print(c)
