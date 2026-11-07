old_tr = json.loads(d["tradeRoutes"])
new_tr = copy.deepcopy(old_tr)
plan_ids = list(pislands)
weights, edges, diag = derive(save, plan_ids, skip_noships=True)
plan_amount = {}
for i in plan["islands"]:
    for p, sb in i["supplied_by"].items():
        plan_amount[(i["id"], int(p))] = sb

# ---- recorded visits: measured rates (net tons received per minute, window = first entry of the route .. last entry of the save)
VIS_ALL = json.load(open(SP + r"\trade\visits.json", encoding="utf-8"))
VIS = [x for x in VIS_ALL if x["trader"] == 41]
T_END = max(x["t"] for x in VIS_ALL)
T_START = min(x["t"] for x in VIS)
route_start = {}
for x in VIS:
    route_start[x["route"]] = min(route_start.get(x["route"], 10 ** 18), x["t"])


def window_min(rid):
    return max((T_END - route_start.get(rid, T_START)) / 60000.0, 1.0)


recv_net = collections.defaultdict(float)      # (rid, island key, product) -> positive net tons
island_net = collections.defaultdict(float)    # (rid, island key, product) -> signed net tons
for x in VIS:
    for g in x["goods"]:
        island_net[(x["route"], x["island"], g[0])] += g[1]
        if g[1] > 0:
            recv_net[(x["route"], x["island"], g[0])] += g[1]

measured = collections.defaultdict(float)      # (supplier 'a<key>', receiver 'a<key>', product) -> t/min
capacity = collections.defaultdict(float)
by_route_recv = collections.defaultdict(float)
for (rid, s_, r_, p_), w_ in edges.items():
    by_route_recv[(rid, r_, p_)] += w_
for (rid, s_, r_, p_), w_ in edges.items():
    tot = by_route_recv[(rid, r_, p_)] or 1.0
    got = recv_net.get((rid, int(r_[1:]), p_), 0.0)
    measured[(s_, r_, p_)] += got * (w_ / tot) / window_min(rid)
    capacity[(s_, r_, p_)] += w_ / window_min(rid)

# ---- goods without a pure source on a route: roles from the signs of the recorded nets (negative = gave, positive = received)
meas_only = []
for rid, dg in sorted(diag.items()):
    for p_ in dg["no_source"]:
        nets = {k_: v_ for (r2, k_, p2), v_ in island_net.items() if r2 == rid and p2 == p_ and ("a%d" % k_) in pislands}
        sup = {k_: -v_ for k_, v_ in nets.items() if v_ < 0}
        rcv = {k_: v_ for k_, v_ in nets.items() if v_ > 0}
        if not sup or not rcv:
            dg.setdefault("no_source_unresolved", []).append(p_)
            continue
        tot_s = sum(sup.values())
        for rk, rv in rcv.items():
            for sk, sv in sup.items():
                key = ("a%d" % sk, "a%d" % rk, p_)
                weights.setdefault(("a%d" % rk, p_), {}).setdefault("a%d" % sk, 0.0)
                weights[("a%d" % rk, p_)]["a%d" % sk] += sv
                measured[key] += rv * (sv / tot_s) / window_min(rid)
                meas_only.append((rid, key))
meas_only_pairs = {k for _, k in meas_only}

producers = collections.defaultdict(set)    # product -> factory guids
for f in FAC.values():
    for o in f.get("outputs", []):
        producers[o["product"]].add(f["guid"])


def local_producer(isl, product):
    info = island_info[isl]
    for g in producers.get(product, ()):
        if info["area"]["counts"].get(g):
            return g
    return None


def island_default(isl, product):
    return stores[isl].get("%d.defaultSupplier.type" % product)


# default-supplier chains (trade routes only)
default_from = {}     # (to_island, product) -> from_island
for r in old_tr:
    if r["isDefaultSupplier"]:
        default_from[(r["to"], r["productGUID"])] = r["from"]


def would_cycle(frm, to, product):
    cur = frm
    cnt = 0
    while True:
        nxt = default_from.get((cur, product))
        if nxt is None:
            return False
        if nxt == to:
            return True
        cur = nxt
        cnt += 1
        if cnt > 1000:
            return True


old_by_pair = collections.defaultdict(list)
for r in old_tr:
    old_by_pair[(r["to"], r["productGUID"])].append(r)

trade = {"derived_pairs": 0, "added": [], "skipped": [], "agreement": [], "user_only_pairs": [], "ordinary_added": [], "measured_only_added": []}
for (rcv, product), sup in sorted(weights.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    if int(rcv[1:]) not in key_to_name:
        continue
    to = key_to_name[int(rcv[1:])]
    trade["derived_pairs"] += 1
    order = sorted(sup.items(), key=lambda kv: (kv[1], kv[0]))
    total = sum(w for _, w in order) or 1.0
    amounts = plan_amount.get((rcv, product), {})
    derived = []
    for i, (sid, w) in enumerate(order):
        frm = key_to_name[int(sid[1:])]
        is_def = i == len(order) - 1
        amt = 0 if is_def else float(amounts.get(sid, 0) if amounts.get(sid, 0) and amounts.get(sid) > 0 else 0)
        derived.append({"productGUID": product, "from": frm, "to": to, "userSetAmount": amt, "isDefaultSupplier": is_def, "weight": w, "sid": sid})
    dsum = [{k: v for k, v in x.items() if k not in ("weight", "sid")} for x in derived]
    base = {"island": to, "productGUID": product, "product": PROD.get(product, {}).get("name"), "derived": dsum,
            "weights": {key_to_name[int(a[1:])]: w for a, w in sup.items()}}
    if product not in PROD:
        trade["skipped"].append(dict(base, reason="product not in calculator data"))
        continue
    existing = old_by_pair.get((to, product), [])
    if existing:
        dset = {x["from"] for x in derived}
        oset = {x["from"] for x in existing}
        odef = next((x["from"] for x in existing if x["isDefaultSupplier"]), None)
        ddef = next(x["from"] for x in derived if x["isDefaultSupplier"])
        status = "match" if (dset == oset and odef == ddef) else "differs"
        trade["agreement"].append(dict(base, status=status, user=existing))
        rec(to, "tradeRoutes:%d" % product, json.dumps(existing), json.dumps(dsum), "unchanged", "tradeRoutes",
            "user entries kept; derived alternative (%s)" % status)
        continue
    dtype = island_default(to, product)
    lp = local_producer(to, product)
    if lp is not None or dtype in ("passive_trade", "extra_good"):
        # the island keeps its own default supplier; every route is ordinary with a minimum amount above 0
        why = ("local producer (factory %d), default supplier type %s kept" % (lp, dtype)) if lp is not None else ("user default supplier type %s kept" % dtype)
        trade["agreement"].append(dict(base, status="not entered", user=[]))
        for x in derived:
            key3 = (x["sid"], rcv, product)
            m_ = measured.get(key3, 0.0)
            if m_ > 0:
                amt, basis = m_, "measured from recorded visits" + (" (roles from recorded net signs, route has no pure source)" if key3 in meas_only_pairs else "")
            else:
                amt, basis = capacity.get(key3, 0.0), "capacity rate visits x unload amount / window (no usable record; planner demand cap not available)"
            amt = round(amt, 4)
            if amt <= 0:
                amt, basis = 0.0001, "minimum placeholder (no record and no capacity)"
            entry = {"productGUID": product, "from": x["from"], "to": to, "userSetAmount": amt, "isDefaultSupplier": False}
            new_tr.append(entry)
            trade["added"].append(entry)
            trade["ordinary_added"].append(dict(entry, basis=basis, why=why))
            if key3 in meas_only_pairs:
                trade["measured_only_added"].append(entry)
            rec(to, "tradeRoutes:%d:%s>%s" % (product, entry["from"], entry["to"]), None, json.dumps(entry), "derived by rule", "tradeRoutes",
                "R37 ordinary route; %s; minimum %s t/min: %s" % (why, amt, basis))
        continue
    # cycle check on the default edge, in file order
    ddef = next(x for x in derived if x["isDefaultSupplier"])
    if would_cycle(ddef["from"], to, product):
        trade["skipped"].append(dict(base, reason="default supplier %s -> %s closes a cycle in the supplier chain" % (ddef["from"], to)))
        continue
    default_from[(to, product)] = ddef["from"]
    trade["agreement"].append(dict(base, status="not entered", user=[]))
    for x in derived:
        entry = {"productGUID": x["productGUID"], "from": x["from"], "to": x["to"], "userSetAmount": x["userSetAmount"], "isDefaultSupplier": x["isDefaultSupplier"]}
        new_tr.append(entry)
        trade["added"].append(entry)
        if (x["sid"], rcv, product) in meas_only_pairs:
            trade["measured_only_added"].append(entry)
        rec(to, "tradeRoutes:%d:%s>%s" % (product, entry["from"], entry["to"]), None, json.dumps(entry), "derived by rule", "tradeRoutes",
            "R37%s; %s; weight %s of %s" % ("; roles from recorded net signs (route has no pure source)" if (x["sid"], rcv, product) in meas_only_pairs else "",
                                            "default supplier" if entry["isDefaultSupplier"] else "ordinary route, minimum = weight share of the planner demand", x["weight"], total))

