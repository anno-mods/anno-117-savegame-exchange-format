from common import *
d, params, plan, save, rep = load()
names, stores = island_stores(d)
tr = json.loads(d["tradeRoutes"])
print(len(tr))
c = collections.Counter(r["from"] for r in tr); print(c)
c = collections.Counter(r["to"] for r in tr); print(c)
print(collections.Counter((r["isDefaultSupplier"], r["userSetAmount"] > 0) for r in tr))
print([r for r in tr if r["userSetAmount"] > 0][:5])
# default supplier chosen non-null
ds = collections.Counter()
for n, s in stores.items():
    for k, v in s.items():
        m = re.match(r"(\d+)\.defaultSupplier\.type$", k)
        if m and v != "null":
            ds[(n, v)] += 1
print(ds)
prods = {p["guid"] for p in params["products"]}
print("tr products not in params", [r["productGUID"] for r in tr if r["productGUID"] not in prods])
print(sum(1 for r in tr if r["from"] == "All Islands" or r["to"] == "All Islands"))
# types in tradeRoutes file as in raw
print(d["tradeRoutes"][:300])
print(type(d["versionCalculator"]), d["versionCalculator"], d["darkMode.checked"])
