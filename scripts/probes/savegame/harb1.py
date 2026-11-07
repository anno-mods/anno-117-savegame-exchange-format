import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
ex = json.load(open((_SCRATCH + r"\x\extract.json")))
post = {h["guid"]: h for h in gd.ships["harbours"]}
for a in ex["areas"]:
    hs = {int(g): c for g, c in a["counts"].items() if int(g) in post}
    other = {gd.name(int(g), "english"): c for g, c in a["counts"].items() if any(w in (gd.buildings.get(int(g), {}).get("name") or "") for w in ("Harbor", "Pier")) and int(g) not in post}
    print(a["key"], (a["key"] >> 6) & 127, {gd.name(g, "english") + f"({g})": c for g, c in hs.items()}, other)
