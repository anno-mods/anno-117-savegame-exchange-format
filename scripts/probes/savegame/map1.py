import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, pickle
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
M = gd.maps
print("profiles", list(M["profiles"].keys()))
p = M["profiles"]["Corners|Large|1"] if "Corners|Large|1" in M["profiles"] else next(iter(M["profiles"].values()))
print("profile keys", list(p.keys()), {k: (v if not isinstance(v, list) else f"list{len(v)}") for k, v in p.items()})
print("latium sample", p["latium"][:3], "cinis", M["cinis"], "egypt keys", list(M["egypt"].keys()), M["egypt"]["islands"][:3], len(M["egypt"]["islands"]))
print("source", M["source"])
SP = _SCRATCH
for si in range(3):
    def want(path):
        return path[-1] == "MapTemplate" and len(path) == 3
    for path, n in s.stream(s.Path(SP + r"\x\session_%d.xml" % si), want):
        print("SESSION", si, "kids", [(k.tag, (k.text or "")[:60] if k.text is not None else len(k.kids)) for k in n.kids if k.tag != "TemplateElement"])
        fn = n.get("Filename")
        print("  Filename:", s.utf16(fn.text) if fn is not None and fn.text else None)
        els = [k for k in n.kids if k.tag == "TemplateElement"]
        rows = []
        for el in els:
            e = el.get("Element")
            if e is None: continue
            pos = e.get("Position"); pth = e.get("MapFilePath")
            rows.append((s.u32(pos.text[:8]) if pos is not None else None, s.u32(pos.text[8:]) if pos is not None else None, s.utf16(pth.text).split("/")[-1] if pth is not None and pth.text else None, [k.tag for k in e.kids][:20]))
        print("  elements", len(rows))
        for r in rows[:50]:
            print("   ", r[:3])
        print("  element tags", rows[0][3] if rows else None)
