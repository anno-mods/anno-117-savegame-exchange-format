import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
print({g: (s.get("regionId"), s.get("region")) for g, s in gd.sessions.items()})
print({k: (v if not isinstance(v, (dict, list)) else "...") for k, v in list(gd.residences.items())[0][1].items()})
print(gd.fertilities.get(2205), len(gd.fertilities))
for g in (2916, 3070, 2880, 2918, 2958, 3089, 31032, 87351):
    b = gd.buildings.get(g)
    print(g, gd.name(g, "english"), {k: v for k, v in (b or {}).items() if not isinstance(v, (dict, list))} if b else None)
print({k: v for k, v in gd.religion_balancing.items() if not isinstance(v, (dict, list))})
print(len(gd.residences), len(gd.factories), len(gd.buildings), len(gd.items))
print(list(gd.levels.items())[0])
it = gd.items[0xFDC3] if 0xFDC3 in gd.items else None
print(0xFDC3, it and gd.name(0xFDC3, "english"), it and [k for k in it.keys()][:15])
