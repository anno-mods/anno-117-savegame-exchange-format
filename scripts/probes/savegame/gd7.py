import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
def short(x, n=500):
    return json.dumps(x, ensure_ascii=False)[:n]
print("ships keys", list(gd.ships.keys()))
for h in gd.ships["harbours"]:
    print("HARBOUR", {k: v for k, v in h.items() if k not in ("loca",)})
print("harbourItems", [(i["guid"], gd.name(i["guid"], "english")) for i in gd.ships.get("harbourItems", [])])
print("ships sample", short(gd.ships["ships"][0], 600) if isinstance(gd.ships.get("ships"), list) else short(gd.ships.get("ships"), 300))
for k in ("modules", "captains", "shipBuffs", "harbourBuffs", "harbourEffects"):
    v = gd.ships.get(k)
    print(k, type(v).__name__, len(v) if v is not None else None, short(v if not isinstance(v, dict) else dict(list(v.items())[:2]), 400))
print("maps keys", list(gd.maps.keys())[:10])
