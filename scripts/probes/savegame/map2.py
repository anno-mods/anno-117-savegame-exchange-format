import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, pickle, math, re
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
M = gd.maps
SP = _SCRATCH
def elements(si):
    out = []
    for path, n in s.stream(s.Path(SP + r"\x\session_%d.xml" % si), lambda p: p[-1] == "MapTemplate" and len(p) == 3):
        for el in n.kids:
            if el.tag != "TemplateElement": continue
            e = el.get("Element")
            pos = e.get("Position"); pth = e.get("MapFilePath")
            x = s.u32(pos.text[:8]); z = s.u32(pos.text[8:])
            x = x - (1 << 32) if x >= 1 << 31 else x
            z = z - (1 << 32) if z >= 1 << 31 else z
            name = s.utf16(pth.text).split("/")[-1][:-4] if pth is not None and pth.text else None
            out.append((x, z, name))
    return out
el = [elements(i) for i in range(3)]
pickle.dump(el, open(SP + r"\x\elements.pkl", "wb"))
ISL = {k: v for k, v in s.read_session.__globals__.items() if k == "ISLAND_SIZES"}
lat = [(x, z, n) for x, z, n in el[0] if n and re.search(r"island_(small|medium|large|extralarge|continental)|campaign_player|dlc01", n)]
print("latium real islands", len(lat))
# compare with profiles
best = []
for key, p in M["profiles"].items():
    if not key.endswith("|1"): continue
    slots = p["latium"]
    for off in (0, 1):
        pass
    sx = {(sl["x"], sl["y"]) for sl in slots}
    hits = sum(1 for x, z, n in lat if (x, z) in sx)
    best.append((hits, key, len(slots)))
print(sorted(best, reverse=True)[:5])
# egypt: compare names
eg = {i["name"]: i for i in M["egypt"]["islands"]}
for x, z, n in el[2]:
    if n and re.search(r"valley_(small|medium|large)_", n):
        key = n.split("valley_")[1]
        e = eg.get(key)
        print(n, (x, z), "planner", (e["x"], e["y"], e["size"]) if e else None)
