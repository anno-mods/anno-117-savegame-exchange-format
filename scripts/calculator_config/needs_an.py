"""Analysis: which needs are switched off in the original config and why (DLC, public building, no producer, user choice).

Reads OUT/Marcia 69 updated.json (its trade routes feed the 'imported' test; pass another updated config as first
argument to use it instead) and writes OUT/needs_rows.json.
"""
import collections
import json
import sys

from common import NEW_JSON, OUT, area_key, island_stores, load

d, params, plan, save, rep = load()
names, stores = island_stores(d)
NEED = {n["guid"]: n for n in params["needs"]}
POPL = {p["guid"]: p for p in params["populationLevels"]}
RES = params["residenceBuildings"]
REGION_ID = {r["guid"]: r["id"] for r in params["regions"]}
SESSION_REGION = {s["guid"]: REGION_ID[s["region"]] for s in params["sessions"]}
PROD = {p["guid"]: p for p in params["products"]}
FAC = {f["guid"]: f for f in params["factories"]}
areas = {a["key"]: a for s in save["sessions"] for a in s}
pislands = {i["id"]: i for i in plan["islands"]}

# need universe per region: (level, need)
def universe(region):
    u = {}
    for r in RES:
        if region in r["associatedRegions"]:
            for nl in r["needsList"]:
                u.setdefault((r["populationLevel"], nl["need"]), []).append(nl.get("requiresItem"))
    return u

dlc3 = {g for g, n in NEED.items() if 67904 in (n.get("dlcUnlocks") or [])}
dlcany = {g: n["dlcUnlocks"] for g, n in NEED.items() if n.get("dlcUnlocks")}
print("needs with dlcUnlocks:", {g: v for g, v in dlcany.items()})
print("levels with dlc:", {g: p.get("dlcUnlocks") for g, p in POPL.items() if p.get("dlcUnlocks")})
print("residences with dlc:", [(r["guid"], r["dlcUnlocks"]) for r in RES if r["dlcUnlocks"]])
for reg in ("Roman", "Celtic", "Egyptian"):
    u = universe(reg)
    print(reg, "universe", len(u), "dlc3 needs in universe:", sorted((l, n) for (l, n) in u if n in dlcany))

producers = collections.defaultdict(set)
for f in FAC.values():
    for o in f.get("outputs", []):
        producers[o["product"]].add(f["guid"])

cfg_path = sys.argv[1] if len(sys.argv) > 1 else NEW_JSON
new_tr = json.loads(open(cfg_path, encoding="utf-8").read().replace("\r", ""))
rows = []
tr = json.loads(new_tr["tradeRoutes"])
imports = collections.defaultdict(set)
for r in tr:
    imports[r["to"]].add(r["productGUID"])
for n in names:
    s = stores[n]
    k = area_key(s)
    if k is None:
        continue
    region = SESSION_REGION[int(s["session"])]
    area = areas[k]
    pl = pislands["a%d" % k]
    dis = {"%s[%d].checked" % (l, nn) for l, ns in pl["disabled_needs"].items() for nn in ns}
    u = universe(region)
    counts = area["counts"]
    resid_by_level = collections.Counter()
    for r in RES:
        if region in r["associatedRegions"]:
            resid_by_level[r["populationLevel"]] += counts.get(r["guid"], 0)
    for (lvl, nd) in sorted(u):
        key = "%d[%d].checked" % (lvl, nd)
        old = s.get(key)
        eff = 1 if old is None else int(float(old))
        if eff == 1 or key in dis:
            continue
        need = NEED[nd]
        prod = need.get("needProduct")
        reasons = []
        if need.get("dlcUnlocks"):
            reasons.append("dlc")
        elif need.get("isBuilding"):
            reasons.append("public building need")
        else:
            local = any(counts.get(f) for f in producers.get(prod, ()))
            imp = prod in imports[n]
            if not producers.get(prod):
                reasons.append("no producer in data")
            elif not any(region in FAC[f]["associatedRegions"] for f in producers[prod]):
                reasons.append("good not producible in region")
            elif not local and not imp:
                reasons.append("not produced/imported")
        if resid_by_level[lvl] == 0:
            reasons.append("tier has no residences")
        rows.append({"island": n, "region": region, "key": key, "old": old, "level": lvl, "need": nd, "prod": prod, "reasons": reasons or ["user switched off"]})
c = collections.Counter((r["region"], tuple(r["reasons"])) for r in rows)
for k, v in sorted(c.items()): print(v, k)
print(len(rows))
by = collections.defaultdict(collections.Counter)
for r in rows: by[r["island"]][r["reasons"][0] if len(r["reasons"]) == 1 else "+".join(r["reasons"])] += 1
for i, v in by.items(): print(i, dict(v))
json.dump(rows, open(OUT / "needs_rows.json", "w"), indent=1)
