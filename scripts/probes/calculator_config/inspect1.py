from common import *
r = json.load(open(SP + r"\Marcia 69 updated.changes.json", encoding="utf-8"))
import re
c = collections.Counter(re.sub(r"\d+", "N", n["note"])[:90] for n in r["notes"])
for k, v in c.most_common(20): print(v, k)
by = collections.defaultdict(list)
for ch in r["changes"]:
    by[ch["category"]].append(ch)
for cat in ("buildings", "patron", "devotion", "items", "buildingEffects", "aqueduct", "modules", "needs", "discoveries"):
    print("==", cat)
    for ch in by[cat][:14]:
        print(ch["island"], ch["key"], repr(ch["old"]), "->", repr(ch["new"]), ch["note"][:70])
print("== fertility sample")
fc = collections.Counter((ch["old"], ch["new"]) for ch in by["fertility"])
print(fc)
for ch in by["fertility"][:6]: print(ch["island"], ch["key"], ch["old"], ch["new"], ch["note"])
print([ (n["island"], n["note"]) for n in r["notes"] if "effect" in n["note"] and "per-target" in n["note"]][:5])
