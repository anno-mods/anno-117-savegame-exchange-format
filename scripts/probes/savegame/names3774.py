import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import re, sys, glob
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
SP = (_SCRATCH + r"\auto3774")
texts = s.load_texts(s.Path(r"C:\dev\asset-extractor\.cache-117\data\base\config\gui\texts_english.xml"))
print("SessionFileVersion lines:")
for f in sorted(glob.glob(SP + r"\session_*.xml")):
    for i, line in enumerate(open(f, encoding="utf-8", errors="replace")):
        if "<SessionFileVersion>" in line:
            print(f[-13:], line.strip()); break
        if i > 40: break
    n = 0
    tagset = {}
    for path, node in s.stream(s.Path(f), lambda p: p[-1] == "AreaInfo" and len(p) == 3):
        for key, val in s.pairs(node):
            op = val.get("OwnerProfile")
            owner = s.u32(op.text) if op is not None else None
            for k in val.kids:
                tagset[k.tag] = tagset.get(k.tag, 0) + 1
            if owner != 41:
                continue
            n += 1
            cn, g, it = val.get("CityName"), val.get("CityNameGuid"), val.get("CityNameIterator")
            gv = int.from_bytes(bytes.fromhex(g.text), "little", signed=True) if g is not None and g.text else None
            print(f[-13:], "key", s.u32(key.text), "CityName:", None if cn is None else (cn.text, s.utf16(cn.text)), "| Guid:", g.text if g is not None else None, "->", texts.get(gv), "| iter:", it.text if it is not None else None)
    print("human areas", n)
    print("AreaInfo child tags", {k: v for k, v in tagset.items() if "Name" in k or "Custom" in k or "Rename" in k})
