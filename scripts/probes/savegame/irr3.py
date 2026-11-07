import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, re, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
b = gd.buffs[28480]
print("buff 28480", b["name"], json.dumps(b.get("calc"), ensure_ascii=False)[:300], b.get("properties"))
q = open(r"C:\dev\Anno-117-Planner\paxplanner\data\game\quests.json", encoding="utf-8").read()
for m in list(re.finditer(r"ConditionIrrigationPercentage", q))[:3]:
    print("QUEST ctx", q[max(0, m.start() - 200): m.end() + 250].replace("\n", " "))
# irrigation-related building templates
for g, bd in gd.buildings.items():
    if "rrigat" in str(bd.get("template")):
        print("BUILDING", g, bd["name"], bd["template"])
# Egyptian farm types
for g, f in gd.factories.items():
    if "Egyptian" in f.regions and f.raw.get("isAgriculture"):
        print("EGY FARM", g, f.raw["name"], "farmType", f.raw.get("farmType"), "aq", (f.raw.get("aqueduct") or {}).get("type"), (f.raw.get("aqueduct") or {}).get("water"), "module", f.raw.get("module"), "freeArea", f.raw.get("freeArea"))
X = (_SCRATCH + r"\x\session_2.xml")
ex = json.load(open((_SCRATCH + r"\x\extract.json")))
keys = sorted(a["key"] for a in ex["areas"] if a["sessionIndex"] == 2)
def want(p):
    return len(p) == 5 and p[-2].startswith("AreaManager_") and int(p[-2].split("_")[1]) in keys and p[-1] == "AreaIrrigationManager"
for path, n in s.stream(s.Path(X), want):
    key = int(path[-1].split("_")[1])
    areas = n.get("IrrigationAreas")
    out = []
    for a in areas.kids if areas is not None else []:
        if a.get("Index") is None:
            continue
        fp = a.get("FilledPipes")
        bits = bytes.fromhex(fp.get("bits").text) if fp is not None and fp.get("bits") is not None and fp.get("bits").text else b""
        grid = a.find("IrrigationGrid/Grid")
        gx = a.find("IrrigationGrid/Grid/x"); gy = a.find("IrrigationGrid/Grid/y"); gb = a.find("IrrigationGrid/Grid/bits")
        gbytes = bytes.fromhex(gb.text) if gb is not None and gb.text else b""
        out.append((a.get("Index").text, "pipesFilledBits", sum(bin(x).count("1") for x in bits), "gridBits", sum(bin(x).count("1") for x in gbytes), "grid", (s.u32(gx.text) if gx is not None else None, s.u32(gy.text) if gy is not None else None)))
    print(key, "areas", len(out), out[:4], "children", [k.tag for k in n.kids], "unlocked", n.get("UnlockedTypes").text if n.get("UnlockedTypes") is not None else None)
