from common import *
d, params, plan, save, rep = load()
names, stores = island_stores(d)
areas = {a["key"]: a for s in save["sessions"] for a in s}
pislands = {i["id"]: i for i in plan["islands"]}
print("areas", len(areas), "plan islands", len(pislands))
for n in names:
    s = stores[n]
    k = area_key(s)
    print(n, s["session"], k, k in areas, ("a%s" % k) in pislands)
a = areas[next(iter(areas))]
print({k: (type(v).__name__, (len(v) if hasattr(v, "__len__") else v)) for k, v in a.items()})
print(a["patron"], a["devotion"], a["paused"][:5], a["counts"] and list(a["counts"].items())[:5])
resg = {r["guid"]: r for r in params["residenceBuildings"]}
fac = {f["guid"]: f for f in params["factories"]}
print("residence guids", sorted(resg))
# which save counts guid are unknown to calc
unk = collections.Counter()
for k, a in areas.items():
    for g, c in a["counts"].items():
        if g not in resg and g not in fac:
            unk[g] += c
print("save building guids not in calc residences/factories:", len(unk))
# what constructed-keys in old are not in either
oldg = collections.Counter()
for n, s in stores.items():
    for key in s:
        m = re.match(r"(\d+)\.buildings\.constructed$", key)
        if m:
            g = int(m.group(1))
            if g not in resg and g not in fac:
                oldg[g] += 1
print("old constructed keys outside residences/factories", oldg)
# disabled needs
print("disabled_needs", {i["id"]: i["disabled_needs"] for i in plan["islands"] if i["disabled_needs"]})
print("paused raw", {k: a["paused"] for k, a in areas.items() if a["paused"]})
# plan effects
eff = collections.Counter()
be = collections.Counter()
for i in plan["islands"]:
    for f, fs in i["factories"].items():
        for e in fs["effects"]: eff[e] += 1
        for e in fs["building_effects"]: be[e] += 1
print("effects", eff); print("building_effects", be)
E = {e["guid"]: e for e in params["effects"]}
for g in list(eff) + list(be):
    e = E.get(g)
    print(g, e and (e["name"], e["effectScope"], e.get("source"), len(e.get("targets", []))))
bb = {b["guid"]: b for b in params["buildingBuffs"]}
print("buildingBuffs sample", list(bb.items())[:1])
print("fert", sorted(set(f for a in areas.values() for f in a["fertilities"])), [f["guid"] for f in params["fertilities"]])
print("lode", sorted(set(f for a in areas.values() for f in a["lode"])))
