import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, re
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
rep = json.load(open((_SCRATCH + r"\fx_report.json")))
notes = [n for r in rep for n in r["notes"]]
print(len(notes));
import collections
print(collections.Counter(notes))
def show(d, n=900):
    return json.dumps({k: v for k, v in d.items() if k not in ("loca", "targets", "icon")}, ensure_ascii=False)[:n]
for g in (153868, 174824, 158336, 158337, 158334):
    e = gd.effects.get(g)
    print(g, show(e) if e else None, "targets", len(e["targets"]) if e else None)
print("area_boosts", {g: (show(v["effect"], 300), v["grantedBy"], v["holders"]) for g, v in gd.area_boosts.items()})
b = gd.buildings.get(31368); print(31368, gd.name(31368, "english"), {k: v for k, v in b.items() if not isinstance(v, (dict, list))} if b else None, b.get("radius") if b else None)
for g in (31032, 87351, 152969, 149838, 31050):
    b = gd.buildings.get(g); print(g, gd.name(g, "english"), b.get("radius"), b.get("effectRadius"), b.get("effectStreet"))
# discovery of irrigation
txt = open(r"C:\dev\Anno-117-Planner\paxplanner\model\wiki.py", encoding="utf-8").read().splitlines()
for i, l in enumerate(txt):
    if "Irrigation" in l:
        print("wiki.py", i + 1, l.strip()[:200])
