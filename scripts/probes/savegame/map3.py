import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, pickle, math
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_parser as sp
SP = _SCRATCH
allareas = pickle.load(open(SP + r"\x\areas_all.pkl", "rb"))
el = pickle.load(open(SP + r"\x\elements.pkl", "rb"))
for si in range(3):
    for a in allareas[si]:
        xs = [p["x"] for p in a["placed"]]; zs = [p["z"] for p in a["placed"]]
        if not xs: continue
        cx, cz = sum(xs) / len(xs), sum(zs) / len(zs)
        iid = (a["key"] >> 6) & 127
        # elements whose box (x..x+w) contains centroid; sizes from ISLAND_SIZES / unknown
        cands = []
        for idx, (x, z, n) in enumerate(el[si]):
            if not n: continue
            size = sp._get_island_size(n.lower())
            if size is None:
                m = 0
            else:
                m = size[0]
            cands.append((idx, n, x, z, size))
        near = sorted(((math.hypot(cx - (x + (s[0] / 2 if s else 128)), cz - (z + (s[1] / 2 if s else 128))), idx, n) for idx, n, x, z, s in cands))[:3]
        print(si, a["key"], "islandID", iid, "centroid", (round(cx), round(cz)), "nearest", [(round(d), i, n) for d, i, n in near])
