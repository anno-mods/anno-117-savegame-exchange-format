"""Validate the updated calculator config (OUT/Marcia 69 updated.json) against the original and the change report.

Prints PASS/FAIL lines and "ALL OK" / "SOME FAILED". Optional first argument: folder holding the three output files
(default OUT, e.g. data/processed/calculator_configs to validate the shipped files).
"""
import collections
import csv
import json
import re
import sys
from pathlib import Path

from common import NEW_CSV, NEW_JSON, NEW_REPORT, load

if len(sys.argv) > 1:
    folder = Path(sys.argv[1])
    NEW_JSON, NEW_REPORT, NEW_CSV = (folder / p.name for p in (NEW_JSON, NEW_REPORT, NEW_CSV))
d, params, plan, save, rep = load()
new = json.load(open(NEW_JSON, encoding="utf-8"))
r = json.load(open(NEW_REPORT, encoding="utf-8"))
ok = True


def check(cond, msg):
    global ok
    print(("PASS " if cond else "FAIL ") + msg)
    ok = ok and cond

check(list(new) == list(d), "top-level keys and order identical to the original (%d keys)" % len(new))
names = json.loads(new["islandNames"])
check(names == json.loads(d["islandNames"]) and new["islandName"] == d["islandName"], "islandNames / islandName unchanged")
for k in ("calculatorSettings", "collapsibleStates", "versionCalculator", "darkMode.checked", "islandNames", "islandName"):
    check(new[k] == d[k], "%s byte-identical" % k)

FAC = {f["guid"]: f for f in params["factories"]}; RES = {x["guid"] for x in params["residenceBuildings"]}
ITEM = {i["guid"] for i in params["items"]}; EFF = {e["guid"] for e in params["effects"]}
FERT = {f["guid"] for f in params["fertilities"]}; NEED = {n["guid"] for n in params["needs"]}
POPL = {p["guid"] for p in params["populationLevels"]}; PATRON = {p["guid"] for p in params["patrons"]}
MOD = {m["guid"] for m in params["modules"]}; PROD = {p["guid"] for p in params["products"]}
pats = [
    (r"^session$", lambda m, v: v in {3245, 6627, 149679, 37135}),
    (r"^gameConnector\.(islandID|areaIndex)$", lambda m, v: True),
    (r"^selectedPatron$", lambda m, v: v == "" or int(v) in PATRON),
    (r"^devotion$", lambda m, v: True),
    (r"^(\d+)\.defaultSupplier\.(type|id)$", lambda m, v: int(m.group(1)) in PROD),
    (r"^(\d+)\[(\d+)\]\.checked$", lambda m, v: int(m.group(1)) in POPL and int(m.group(2)) in NEED),
    (r"^(\d+)\[(\d+)\]\.notes$", lambda m, v: True),
    (r"^(\d+)\[(\d+)\]\.scaling$", lambda m, v: int(m.group(1)) in FAC and (int(m.group(2)) in ITEM or int(m.group(2)) in EFF)),
    (r"^island\.effect\.(\d+)\.scaling$", lambda m, v: int(m.group(1)) in EFF),
    (r"^island\.fertility\.(\d+)\.checked$", lambda m, v: int(m.group(1)) in FERT),
    (r"^(\d+)\.buildings\.(constructed|planned|fullyUtilizeConstructed)$", lambda m, v: int(m.group(1)) in FAC or int(m.group(1)) in RES),
    (r"^(\d+)\.aqueductBuff\.checked$", lambda m, v: int(m.group(1)) in FAC and FAC[int(m.group(1))].get("aqueductProductivityBuff")),
    (r"^(\d+)\.module\[(\d+)\]\.checked$", lambda m, v: int(m.group(1)) in FAC and int(m.group(2)) in MOD),
    (r"^(\d+)\.effectCoverage$", lambda m, v: True),
    (r"^(\d+)\.notes$", lambda m, v: True),
    (r"^passiveTrade\.userSetAmount$", lambda m, v: True),
]
bad = []
changed_keys = 0
by_island_changed = {}
for n in names:
    s = json.loads(new[n]); o = json.loads(d[n])
    for k, v in s.items():
        for p, fn in pats:
            m = re.match(p, k)
            if m:
                try:
                    good = bool(fn(m, v))
                except Exception:
                    good = False
                if not good and (k not in o or o[k] != v):
                    bad.append((n, k, v))
                break
        else:
            bad.append((n, k, "no pattern"))
    if set(o) - set(s):
        check(False, "%s: no key removed" % n)
    diff = [k for k in set(s) | set(o) if s.get(k) != o.get(k)]
    # numeric equality 1 vs "1" are changes only if value differs
    diff = [k for k in diff if not (k in s and k in o and str(s[k]) == str(o[k]))]
    by_island_changed[n] = len(diff)
check(not bad, "all new/changed keys fit a persist pattern with a GUID known to the calculator data (%s)" % bad[:5])
rep_counts = collections.Counter(c["island"] for c in r["changes"] if c["source"] != "unchanged" and c["category"] != "tradeRoutes" and c["category"] != "discoveries")
mism = {n: (by_island_changed[n], rep_counts.get(n, 0)) for n in names if by_island_changed[n] != rep_counts.get(n, 0)}
check(not mism, "per-island changed key count equals the report (%s)" % mism)
unchanged_isl = [n for n in names if json.loads(new[n]) == json.loads(d[n])]
print("islands without any store change:", unchanged_isl)
# session untouched
check(all(json.loads(new[n]).get("session") == json.loads(d[n]).get("session") for n in names), "sessions unchanged")
for n in ("Monument Demand",):
    check(new[n] == d[n], "Monument Demand store identical")
# trade routes
tr = json.loads(new["tradeRoutes"]); otr = json.loads(d["tradeRoutes"])
check(tr[:len(otr)] == otr, "existing %d trade route entries unchanged and first" % len(otr))
check(len(tr) - len(otr) == len(r["trade"]["added"]), "added entries %d match report" % (len(tr) - len(otr)))
keys = collections.Counter((x["productGUID"], x["from"], x["to"]) for x in tr)
check(max(keys.values()) == 1, "no duplicate (product, from, to)")
defs = collections.Counter((x["productGUID"], x["to"]) for x in tr if x["isDefaultSupplier"])
check(max(defs.values()) == 1, "one default supplier per island and product")
check(all(x["from"] in names and x["to"] in names and x["from"] != x["to"] and x["productGUID"] in PROD for x in tr), "route islands and products exist, no self route")
check(all(set(x) == {"productGUID", "from", "to", "userSetAmount", "isDefaultSupplier"} for x in tr), "route entries have exactly the calculator fields")
dfm = {(x["productGUID"], x["to"]): x["from"] for x in tr if x["isDefaultSupplier"]}
cyc = 0
for (p, to), frm in dfm.items():
    cur = frm; seen = set()
    while (p, cur) in dfm:
        if cur == to or cur in seen:
            cyc += 1; break
        seen.add(cur); cur = dfm[(p, cur)]
    else:
        if cur == to: cyc += 1
check(cyc == 0, "no cycle in the default supplier chains (%d)" % cyc)
# counts add up
cat = collections.Counter(c["category"] for c in r["changes"] if c["source"] != "unchanged")
check(sum(cat.values()) == r["summary"]["changes"] == sum(r["summary"]["by_island"].values()), "category total %d = island total" % sum(cat.values()))
check(cat["tradeRoutes"] == len(r["trade"]["added"]), "tradeRoutes change rows = added entries")
print(dict(cat))
rows = list(csv.DictReader(open(NEW_CSV, encoding="utf-8")))
check(len(rows) == len(r["changes"]), "CSV rows %d = JSON changes %d" % (len(rows), len(r["changes"])))
print("ALL OK" if ok else "SOME FAILED")
