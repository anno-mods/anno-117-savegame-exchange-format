import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
from paxplanner.model.routes import optional_ship_effects
gd = GameData()
SP = _SCRATCH
opt = {e["guid"]: e for e in optional_ship_effects(gd)}
allfx = {int(k): v for k, v in gd.ships["effects"].items()}
print("ship effects total", len(allfx), "optional (no source, non-local)", len(opt))
for g, e in list(opt.items())[:12]:
    print("  opt", g, e["loca"].get("english"), e.get("scope"))
rewards = []
for path, node in s.stream(s.Path(SP + r"\x\data_raw.xml"), lambda p: p[-1] == "MetaTechHandler"):
    if node.get("TechProgress") is not None and node.get("TechProgress").kids:
        ar = node.get("ActiveEffectRewards3")
        kids = ar.kids
        rewards = [s.u32(kids[i].text) for i in range(0, len(kids) - 1, 2)]
        print("human ActiveEffectRewards3", len(rewards), "sample", rewards[:6], [k.text for k in kids[:4]])
        break
hit = [g for g in rewards if g in allfx]
print("active rewards that are ship effects:", [(g, allfx[g]["loca"].get("english") if allfx[g].get("loca") else allfx[g]["name"], g in opt) for g in hit])
# all human + other tags that list effect ids: search text of data_raw for ship effect guids appearing as 4-byte hex
import re
txt = open(SP + r"\x\data_raw.xml", encoding="utf-8", errors="replace").read()
for g in list(opt)[:200]:
    h = g.to_bytes(4, "little").hex().upper()
    c = len(re.findall(r"<None>" + h + r"</None>|<Guid>" + h + r"</Guid>|>" + h + r"<", txt))
    if c:
        print("effect", g, opt[g]["loca"].get("english"), "occurrences in outer xml", c)
