import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import json, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
rep = json.load(open(SP + r"\fx_report_v3.json"))
ex = json.load(open(SP + r"\x\extract.json"))
name = {}
tot = collections.Counter()
for r in rep:
    k = r["key"]
    ds = [d for d in r["decisions"] if d.get("method") == "street"]
    if not ds and not r["notes"]:
        continue
    print(k, "island", (k >> 6) & 127, "notes", r["notes"][:2])
    for d in ds:
        tot["street"] += 1
        tot["street_applied"] += d["applied"]
        tot["circle_applied"] += d["circle_applied"]
        tot["differ"] += d["applied"] != d["circle_applied"]
        tot["near"] += d["near_tie"]
        print("  ", gd.name(d["factory"], "english"), d["kind"], d["id"], f"street {d['affected']}/{d['total']} circle {d['circle_affected']}/{d['total']}", "applied" if d["applied"] else "-", "(circle applied)" if d["circle_applied"] else "", "NEAR" if d["near_tie"] else "")
print(dict(tot))
