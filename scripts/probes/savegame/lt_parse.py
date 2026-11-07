import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, os, pickle
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
SP = _SCRATCH
import savegame_parser as sp
out = []
for i in range(3):
    tm, ab, ar, ap, unk = sp._parse_session_xml(SP + r"\x\session_%d.xml" % i, None)
    print("session", i, "templates", len(tm), "areas", {a: len(b) for a, b in ab.items()})
    out.append((tm, ab))
pickle.dump(out, open(SP + r"\x\lt_parse.pkl", "wb"))
