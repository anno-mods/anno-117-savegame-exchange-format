import os as _os
from pathlib import Path as _Path
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
_CONFIG = str(_Path(__file__).resolve().parents[3] / "data" / "raw" / "calculator_configs" / "Marcia 69.json")
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.dont_write_bytecode = True
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
rep = json.load(open(SP + r"\x\report.json"))
c = collections.Counter(); b = collections.Counter()
for r in rep:
    for bld, it, alloc in r["unmapped_items"]:
        c[alloc] += 1; b[gd.buildings.get(bld, {}).get("template")] += 1
print("unmapped by allocation", c); print("unmapped by building template", b)
print("mapped residence items", sum(r["items"] for r in rep))
calc = json.load(open(_CONFIG, encoding="utf-8"))
tr = json.loads(calc["tradeRoutes"])
print("calc tradeRoutes", len(tr), collections.Counter(t["from"] + ">" + t["to"] for t in tr).most_common(5), "userSet>0:", sum(1 for t in tr if t["userSetAmount"]), "default:", sum(1 for t in tr if t["isDefaultSupplier"]))
tot_notes = 0; fu = 0; eff = 0; chk = 0
for nm in json.loads(calc["islandNames"]):
    i = json.loads(calc[nm])
    fu += sum(1 for k in i if "fullyUtilize" in k); eff += sum(1 for k in i if k.startswith("island.effect")); chk += sum(1 for k in i if k.endswith("].checked")); tot_notes += sum(1 for k in i if "notes" in k.lower())
print("calc-only: fullyUtilize", fu, "island.effect", eff, "need toggles", chk, "notes", tot_notes)
print("residence guids total in save:", sum(sum(v for g, v in r["counts"].items() if int(g) in gd.residences) for r in rep))
