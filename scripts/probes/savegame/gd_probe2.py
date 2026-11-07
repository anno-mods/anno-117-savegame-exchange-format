import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
for g, r in gd.residences.items():
    print(g, r["name"], r["populationLevel"], r["regions"], r["upgrades"], (r.get("romanization") if not isinstance(r.get("romanization"), dict) else "d"))
print(3141 in gd.buildings, 3141 in gd.residences, gd.buildings.get(3141, {}).get("name"))
b = gd.buildings.get(3087)
print(b and {k: v for k, v in b.items() if not isinstance(v, (dict, list))})
print(list(gd.sessions[3245].keys()))
print([ (g, f["name"], f["regions"]) for g, f in gd.fertilities.items()][:40])
