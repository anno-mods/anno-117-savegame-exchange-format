import sys, json
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
def short(d, n=700):
    return json.dumps(d, ensure_ascii=False)[:n]
it = gd.items[64963]
print("ITEM", short({k: v for k, v in it.items() if k not in ("loca", "description")}, 1500))
print("EFFECT 51637", short({k: v for k, v in gd.effects[51637].items() if k != "loca"}))
print("EFFECT 99011", short({k: v for k, v in gd.effects[99011].items() if k != "loca"}))
f = next(iter(gd.factories.values()))
print("FACTORY", short({k: v for k, v in f.raw.items() if k not in ("loca",)}, 1500))
farm = next(x for x in gd.factories.values() if x.raw.get("additionalModule"))
print("FARM", farm.guid, short({k: v for k, v in farm.raw.items() if k not in ("loca",)}, 1500))
print("SILO", short(gd.silo_modules[:2], 1200))
print("building_boosts", list(gd.building_boosts)[:10])
print("area_boosts", list(gd.area_boosts)[:10])
