"""Append a per-island overview of the construction-material factories (old vs new constructed count) to the change report.

Reads OUT/Marcia 69 updated.json and rewrites OUT/Marcia 69 updated.changes.json with the extra key
`construction_materials_overview`. Run after build_config.py.
"""
import json

from common import NEW_JSON, NEW_REPORT, load

d, params, plan, save, rep = load()
new = json.load(open(NEW_JSON, encoding="utf-8"))
names = json.loads(new["islandNames"])
cmp_ = {p["guid"] for p in params["products"] if p.get("isConstructionMaterial")}
cmf = {f["guid"]: f["name"] for f in params["factories"] if any(o["product"] in cmp_ for o in f.get("outputs", []))}
rows = []
for n in names:
    o = json.loads(d[n]); s = json.loads(new[n])
    for g, nm in cmf.items():
        k = "%d.buildings.constructed" % g
        if k in o or k in s:
            rows.append({"island": n, "factory": g, "name": nm, "old": o.get(k), "new": s.get(k), "fullyUtilizeConstructed": s.get("%d.buildings.fullyUtilizeConstructed" % g)})
p = NEW_REPORT
r = json.load(open(p, encoding="utf-8"))
r["construction_materials_overview"] = rows
json.dump(r, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(len(rows), sum(1 for x in rows if x["old"] != x["new"]))
for x in rows: print(x)
