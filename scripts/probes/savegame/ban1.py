import os as _os
from pathlib import Path as _Path
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
_CONFIG = str(_Path(__file__).resolve().parents[3] / "data" / "raw" / "calculator_configs" / "Marcia 69.json")
import sys, json, re, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
X = SP + r"\x\session_0.xml"
KEY = 10177
def want(p):
    return len(p) == 5 and p[-2] == "AreaManager_%d" % KEY and p[-1] == "AreaResidenceConsumptionManager"
for path, n in s.stream(s.Path(X), want):
    pd = n.get("ProductData")
    kids = pd.kids
    print("ProductData entries", len(kids) // 2)
    paused = collections.defaultdict(dict)
    shown = 0
    for i in range(0, len(kids) - 1, 2):
        prod = s.u32(kids[i].text)
        info = kids[i + 1].get("PopulationPauseInfo")
        if info is None: continue
        ks = info.kids
        for j in range(0, len(ks) - 1, 2):
            lvl = s.u32(ks[j].text); val = ks[j + 1].text
            paused[prod][lvl] = val
        if shown < 2:
            print("sample", prod, [(k.tag, k.text) for k in ks][:12]); shown += 1
    flagged = {(p, l): v for p, d in paused.items() for l, v in d.items() if v not in ("00", "", None)}
    print("non-zero pause flags", len(flagged), collections.Counter(flagged.values()))
    for (p, l), v in sorted(flagged.items())[:40]:
        print(gd.name(p, "english"), "level", gd.name(l, "english"), v)
calc = json.load(open(_CONFIG, encoding="utf-8"))
isl = json.loads(calc["Cinis"])
off = [(int(m.group(1)), int(m.group(2))) for k, v in isl.items() if (m := re.match(r"^(\d+)\[(\d+)\]\.checked$", k)) and str(v) == "0"]
print("calc Cinis unchecked needs", [(gd.name(l, "english"), gd.name(nd, "english"), (gd.needs.get(nd) or {}).get("product")) for l, nd in off])
