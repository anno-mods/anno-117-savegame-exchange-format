import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, pickle, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
areas = pickle.load(open(SP + r"\x\areas_s2.pkl", "rb"))
a = next(x for x in areas if x["key"] == 8708)
by = {p["id"]: p for p in a["placed"]}
X = SP + r"\x\session_2.xml"
def want(p):
    return len(p) == 5 and p[-2] == "AreaManager_8708" and p[-1] == "AreaEffectManager"
for path, n in s.stream(s.Path(X), want):
    cache = n.get("StreetConnectionCache")
    kids = cache.kids
    print("entries", len(kids))
    ent = {}
    i = 0
    while i < len(kids) - 1:
        k, v = kids[i], kids[i + 1]
        ent[k.text] = [c.text for c in v.kids] if v.kids else []
        i += 2
    print("keys", len(ent), "sample sizes", sorted(len(v) for v in ent.values())[-5:])
    lib = "2201000004220000"
    print("library key present", lib in ent, "listed under others:", sum(lib in v for v in ent.values()))
    kinds = collections.Counter()
    for k in ent:
        p = by.get(k)
        kinds[gd.name(p["building"], "english") if p else "?"] += 1
    print("key building types", kinds.most_common(12))
    if lib in ent:
        reached = ent[lib]
        prod = [p for p in a["placed"] if p["building"] in gd.factories]
        print("library list size", len(reached), "production in list", sum(p["id"] in set(reached) for p in prod), "of", len(prod))
        print("production NOT in list:", [(gd.name(p["building"], "english"), p["id"]) for p in prod if p["id"] not in set(reached)])
