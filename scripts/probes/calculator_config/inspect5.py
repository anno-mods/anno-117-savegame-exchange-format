from common import *
r = json.load(open(SP + r"\Marcia 69 updated.changes.json", encoding="utf-8"))
v2 = json.load(open(SP + r"\Marcia 69 updated.v2.changes.json", encoding="utf-8"))
t = r["trade"]
oa = t["ordinary_added"]
print("ordinary (local/user-default) added", len(oa), collections.Counter(x["basis"][:30] for x in oa))
print("min amounts: min %.4f max %.4f median %.4f" % (min(x["userSetAmount"] for x in oa), max(x["userSetAmount"] for x in oa), sorted(x["userSetAmount"] for x in oa)[len(oa)//2]))
for x in oa:
    if x["productGUID"] in (31698, 151703) or x["why"].startswith("user"):
        print(x)
print("sample", [(x["to"], x["productGUID"], x["from"], x["userSetAmount"], x["basis"][:12]) for x in oa[:6]])
print("measured-only (no pure source):", t["measured_only_added"])
new = {(e["productGUID"], e["from"], e["to"]) for e in t["added"]}
old2 = {(e["productGUID"], e["from"], e["to"]) for e in v2["trade"]["added"]}
print("lost vs v2:", sorted(old2 - new))
print("gained vs v2 (non-local):", [k for k in sorted(new - old2) if k not in {(x["productGUID"], x["from"], x["to"]) for x in oa}])
print("approx", t["approximate"])
print("noships/unresolved:", [(k, x.get("no_source_unresolved")) for k, x in {}.items()])
print("skipped", t["skipped"])
print("agreement", collections.Counter(a["status"] for a in t["agreement"]), "entries", len(t["added"]), "total", 40 + len(t["added"]))
# local default type check
d, params, plan, save, rep = load()
names, stores = island_stores(d)
c = collections.Counter()
for x in oa:
    c[stores[x["to"]].get("%d.defaultSupplier.type" % x["productGUID"])] += 1
print("default types of receiving islands for ordinary-added:", c)
print([ (x["to"], x["productGUID"]) for x in oa if stores[x["to"]].get("%d.defaultSupplier.type" % x["productGUID"]) != "factory"])
