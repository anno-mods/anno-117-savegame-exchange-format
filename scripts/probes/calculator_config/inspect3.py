from common import *
r = json.load(open(SP + r"\Marcia 69 updated.changes.json", encoding="utf-8"))
t = r["trade"]
print({k: (len(v) if isinstance(v, list) else v) for k, v in t.items()})
print(t["approximate"])
for a in t["agreement"]:
    if a["status"] != "not entered":
        print(a["status"], a["island"], a["productGUID"], a["product"], "user:", [(u["from"], u["userSetAmount"], u["isDefaultSupplier"]) for u in a["user"]], "derived:", [(u["from"], u["userSetAmount"], u["isDefaultSupplier"]) for u in a["derived"]])
print("skipped")
for s in t["skipped"]:
    print(s["island"], s["productGUID"], s["product"], s["reason"][:80])
print("user only pairs", t["user_only_pairs"])
import collections
c = collections.Counter(len(a["derived"]) for a in t["agreement"] if a["status"] == "not entered")
print("suppliers per pair", c)
tot = [e for e in t["added"]]
print(collections.Counter(e["to"] for e in tot))
print(sum(1 for e in tot if e["userSetAmount"] > 0), "ordinary with min>0;", sum(1 for e in tot if not e["isDefaultSupplier"]), "ordinary")
