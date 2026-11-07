import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
n = next(v for v in gd.needs.values() if v.get("product") == 2156)
print({k: v for k, v in n.items() if k != "loca"})
print(list(gd.levels[1498].keys()), gd.levels[1498].get("needs") and len(gd.levels[1498]["needs"]))
# trading posts / harbour buildings
for g, b in gd.buildings.items():
    t = str(b.get("template"))
    if any(w in t for w in ("Harbor", "Harbour", "Kontor", "LoadingPier", "Warehouse", "Pier", "Trading")) or any(w in str(b.get("name")) for w in ("Harbor", "Harbour", "Kontor", "Pier", "Trading")):
        print(g, b["name"], t, gd.name(g, "english"))
print({k: (v if not isinstance(v, (dict, list)) else "...") for k, v in gd.trade.items()})
print(list(gd.trade.keys()))
