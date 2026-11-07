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
gd = GameData()
SP = _SCRATCH
allfx = {int(k): v for k, v in gd.ships["effects"].items()}
print({g: (v["loca"].get("english") if v.get("loca") else v["name"], v.get("scope"), len(v["sources"])) for g, v in allfx.items()})
for si in range(3):
    for path, node in s.stream(s.Path(SP + r"\x\session_%d.xml" % si), lambda p: p[-1] == "SessionEffectManager" and len(p) == 3):
        effs = node.get("Effects")
        out = []
        for e in effs.kids:
            g = e.get("Guid")
            out.append(s.u32(g.text) if g is not None else None)
        print("session", si, "SessionEffectManager effects", out, [(g, gd.effects.get(g, {}).get("name")) for g in out])
for path, node in s.stream(s.Path(SP + r"\x\data_raw.xml"), lambda p: p[-1] in ("MetaEffectManager", "GlobalEffects", "EffectManager") or p[-1].endswith("EffectManager")):
    print("outer", "/".join(path[-3:]), node.tag, [(k.tag, len(k.kids)) for k in node.kids][:8])
