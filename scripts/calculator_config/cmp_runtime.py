"""Compare the calculator runtime values of the original and the updated config (output of run_calc.js).

    python cmp_runtime.py [runtime.json]        default OUT/runtime.json
"""
import json
import sys

from common import OUT

r = json.load(open(sys.argv[1] if len(sys.argv) > 1 else OUT / "runtime.json", encoding="utf-8"))
o, n = r[0]["result"]["islands"], r[1]["result"]["islands"]
cols = ["constructedFactories", "constructedResidences", "requiredFactories", "residents", "itemsOn", "aqueductOn", "modulesOn", "fertilityOff", "needsOff", "tradeIn", "tradeOut"]
print("island", *cols)
for k in o:
    print(k[:22].ljust(22), *["%s>%s" % (o[k].get(c), n[k].get(c)) if o[k].get(c) != n[k].get(c) else str(o[k].get(c)) for c in cols])
print([ (k, o[k].get("patron"), n[k].get("patron")) for k in o if o[k].get("patron") != n[k].get("patron")][:3])
