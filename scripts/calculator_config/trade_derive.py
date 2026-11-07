"""Re-derive the per-route trade flows (same rule as savegame_to_planner.derive_trade) with route diagnostics.

`derive(save, plan_ids)` returns (weights, edges, diag); build_config.py imports it. Run as a script it compares the
result with the planner trade report (fx_report_v5.json) and prints differences.
"""
import collections

from common import load


def derive(save, plan_ids, skip_noships=False):
    empire = save["empire"]
    areas = {a["key"]: a for s in save["sessions"] for a in s}
    ids = set(plan_ids)  # 'a<key>'
    weights = {}          # (receiver, product) -> {supplier: weight}
    edges = collections.defaultdict(float)   # (rid, supplier, receiver, product) -> weight
    diag = {}
    for rid, route in empire["routes"].items():
        stations = route["stations"]
        roles = []
        for st in stations:
            prods = {}
            for sl in st["slots"]:
                e = prods.setdefault(sl["product"], {"load": 0, "unload": 0, "amount": 0.0})
                if sl["load"]:
                    e["load"] += 1
                else:
                    e["unload"] += 1
                    e["amount"] += sl["amount"] or 0
            roles.append(prods)
        dg = {"id": rid, "name": route["name"], "ships": route["ships"], "stations": len(stations),
              "relay": False, "multi_source": False, "sink_twice": False, "nonplayer": False, "no_source": [],
              "edges": 0, "products": set(), "self": False}
        if skip_noships and route["ships"] == 0:
            dg["noships_skipped"] = True
            diag[rid] = dg
            continue
        areas_in = [st["area"] for st in stations]
        if any(("a%d" % a) not in ids for a in areas_in):
            dg["nonplayer"] = True
        for prods in roles:
            for p, e in prods.items():
                if e["load"] and e["unload"]:
                    dg["relay"] = True
        for product in {p for prods in roles for p in prods}:
            sources = [i for i, prods in enumerate(roles) if product in prods and prods[product]["load"] and not prods[product]["unload"]]
            sinks = [i for i, prods in enumerate(roles) if product in prods and prods[product]["unload"]]
            if len(sources) > 1:
                dg["multi_source"] = True
            if len({areas_in[i] for i in sinks}) < len(sinks):
                dg["sink_twice"] = True
            if not sources:
                dg["no_source"].append(product)
                continue
            for r in sinks:
                prods = roles[r]
                supplier = stations[max((s for s in sources if s < r), default=sources[-1])]["area"]
                receiver = stations[r]["area"]
                if supplier == receiver:
                    dg["self"] = True
                    continue
                if ("a%d" % supplier) not in ids or ("a%d" % receiver) not in ids:
                    continue
                visits = max(1, len((areas.get(receiver) or {}).get("visits", {}).get(rid, [])))
                w = visits * prods[product]["amount"]
                weights.setdefault(("a%d" % receiver, product), {}).setdefault("a%d" % supplier, 0.0)
                weights[("a%d" % receiver, product)]["a%d" % supplier] += w
                edges[(rid, "a%d" % supplier, "a%d" % receiver, product)] += w
                dg["edges"] += 1
                dg["products"].add(product)
        diag[rid] = dg
    return weights, edges, diag


if __name__ == "__main__":
    d, params, plan, save, rep = load()
    ids = [i["id"] for i in plan["islands"]]
    w, e, diag = derive(save, ids)
    ref = {(i["island"], i["product"]): i["weights"] for i in rep["trade"]["imports"]}
    print("mine", len(w), "script", len(ref), "equal", w == ref)
    for k in set(w) | set(ref):
        if w.get(k) != ref.get(k):
            print("DIFF", k, w.get(k), ref.get(k))
    for rid in (66, 73):
        print(diag.get(rid))
    print(sum(1 for x in diag.values() if x["edges"]), "routes with edges of", len(diag))
