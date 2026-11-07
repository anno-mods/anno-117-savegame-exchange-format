from common import *
r = json.load(open(SP + r"\Marcia 69 updated.changes.json", encoding="utf-8"))
ch = r["changes"]
b = [c for c in ch if c["category"] == "buildings"]
print("buildings:", len(b), "set to 0:", [(c["island"], c["key"], c["old"]) for c in b if c["new"] == 0], "added keys:", sum(1 for c in b if c["old"] is None))
print("buildings residence vs production:")
t = r["trade"]
print("flow pairs", t["flow_edges_pairs"], "routes with flows", t["routes_with_flows"], "of", t["routes_total"])
# entries produced per route status
print("items 0:", sum(1 for c in ch if c["category"] == "items" and c["new"] == 0), "items up:", sum(1 for c in ch if c["category"] == "items" and c["new"] != 0))
print("buildingEffects off:", sum(1 for c in ch if c["category"] == "buildingEffects" and c["new"] == 0))
print("aqueduct:", [(c["island"], c["key"], c["old"], c["new"]) for c in ch if c["category"] == "aqueduct"])
print("modules:", [(c["island"], c["key"], c["old"], c["new"]) for c in ch if c["category"] == "modules"])
print("patron:", [(c["island"], c["old"], c["new"]) for c in ch if c["category"] == "patron"])
print("fertility old->new:", collections.Counter((c["old"], c["new"]) for c in ch if c["category"] == "fertility"))
print([n["note"] for n in r["notes"]][:20])
print("trade skip reasons", collections.Counter(s["reason"][:40] for s in t["skipped"]))
# per-island supplier set + default for derived pairs added
by = collections.defaultdict(lambda: collections.defaultdict(list))
for a in t["agreement"]:
    by[a["island"]][a["status"]].append(a)
for isl, dd in by.items():
    print(isl, {k: len(v) for k, v in dd.items()})
