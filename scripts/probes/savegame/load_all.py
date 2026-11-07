import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, pickle
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool\tools\savegame_to_planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
import savegame_to_planner as s
SP = _SCRATCH
out = [s.read_session(s.Path(SP + r"\x\session_%d.xml" % i)) for i in range(3)]
pickle.dump(out, open(SP + r"\x\areas_all.pkl", "wb"))
print("done", [len(a) for a in out])
