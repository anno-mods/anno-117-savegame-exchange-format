from common import *
v = json.load(open(SP + r"\trade\visits.json", encoding="utf-8"))
print(len(v), v[0].keys())
print(collections.Counter(x["trader"] for x in v).most_common(5))
ts = [x["t"] for x in v if x["trader"] == 41]
print(min(ts), max(ts), (max(ts) - min(ts)) / 10000 / 60, "min if t in 1e-4 s?")
for isl, prod in ((10177, 151703), (8452, 31698), (10177, 31698)):
    rows = [(x["route"], x["t"], g) for x in v if x["island"] == isl and x["trader"] == 41 for g in x["goods"] if g[0] == prod]
    print(isl, prod, len(rows), rows[:8])
# routes 143 visits at Nusquam/Juliana goods for ivory
for x in v:
    if x["route"] in (143, 191) and x["trader"] == 41:
        print(x["route"], x["island"], x["t"], x["goods"][:10])
