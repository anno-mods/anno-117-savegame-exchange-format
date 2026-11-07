import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
ex = json.load(open(SP + r"\x\extract.json"))
rep = {r["key"]: r for r in json.load(open(SP + r"\fx_report.json"))}
cases = [("Nusquam", 11, 1, 3245, 2971, 51292), ("Nusquam", 11, 1, 3245, 2971, 156710), ("Tiberia", 32, 1, 3245, 8579, 44114), ("Argantum", 11, 1, 6627, 5959, 44147),
         ("Cudslip", 4, 1, 6627, 5614, 50665), ("Cinis", 31, 1, 3245, 31755, 44114), ("Cragmore", 5, 1, 6627, 5851, 44122), ("Juliana", 5, 1, 3245, 2794, 80225),
         ("Valerium", 35, 1, 3245, 2920, 145268)]
for nm, iid, ai, sess, fac, item in cases:
    code = {3245: 1, 6627: 3}[sess]
    key = (ai << 13) | (iid << 6) | code
    a = next(x for x in ex["areas"] if x["key"] == key)
    holders = [s for s in a["sockets"] if any(i["item"] == item for i in s["items"])]
    rec = gd.items.get(item)
    eff = (rec or {}).get("effect", {})
    d = [x for x in rep[key]["decisions"] if x["factory"] == fac and x["id"] == item]
    n = a["counts"].get(str(fac), a["counts"].get(fac, 0))
    print(nm, gd.name(fac, "english"), "x", n, "| item", gd.name(item, "english"), "alloc", (rec or {}).get("allocation"), "scope", eff.get("scope"), "| socketed in", [gd.name(h["building"], "english") for h in holders], "| decision", d, "| notes", [x for x in rep[key]["notes"] if str(item) in x][:1])
