import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
p = (_SCRATCH + r"\upd\build_config.py")
t = open(p, encoding="utf-8").read()
a = t.index('old_tr = json.loads(d["tradeRoutes"])')
b = t.index("derived_pairs_keys =")
new = open(p.replace("build_config.py", "trade_block.py"), encoding="utf-8").read()
open(p, "w", encoding="utf-8").write(t[:a] + new + t[b:])
print("spliced", a, b)
