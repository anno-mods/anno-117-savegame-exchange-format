"""Merge the savegame state (Marcia 69.a8s, via the plan JSON + raw save extraction) into the calculator config dump.

Inputs : data/raw/calculator_configs/Marcia 69.json (original config), data/processed/planner_plans/marcia69.v5.plan.json,
         data/processed/reports/fx_report_v5.json, data/processed/reports/trade_visits.json (all in the repository),
         OUT/params.json (dump_params.js) and OUT/save_data.pkl (extract_save.py).
Outputs: OUT/Marcia 69 updated.json, OUT/Marcia 69 updated.changes.json, OUT/Marcia 69 updated.changes.csv.
Run from any folder:  python build_config.py     (paths: see common.py)
"""
import collections
import copy
import csv
import json
import re

from common import NEW_CSV, NEW_JSON, NEW_REPORT, OUT, TRADE_VISITS, area_key, island_stores, load
from trade_derive import derive

OUT_JSON = NEW_JSON
OUT_REPORT = NEW_REPORT
OUT_CSV = NEW_CSV
OUT.mkdir(parents=True, exist_ok=True)

d, params, plan, save, rep = load()
names, stores = island_stores(d)
areas = {a["key"]: a for s in save["sessions"] for a in s}
pislands = {i["id"]: i for i in plan["islands"]}
empire = save["empire"]

# ------------------------------------------------------------------ calculator data indexes
FAC = {f["guid"]: f for f in params["factories"]}
RES = {r["guid"]: r for r in params["residenceBuildings"]}
ITEM = {i["guid"]: i for i in params["items"]}
EFF = {e["guid"]: e for e in params["effects"]}
BUFF = {b["guid"]: b for b in params["buildingBuffs"]}
FERT = {f["guid"]: f for f in params["fertilities"]}
PATRON = {p["guid"] for p in params["patrons"]}
PROD = {p["guid"]: p for p in params["products"]}
NEED = {n["guid"] for n in params["needs"]}
POPL = {p["guid"]: p for p in params["populationLevels"]}
REGION_ID = {r["guid"]: r["id"] for r in params["regions"]}
SESSION_REGION = {s["guid"]: REGION_ID[s["region"]] for s in params["sessions"]}
TECH = {t["guid"]: t for t in params["techs"]}
MODULE = {m["guid"]: m for m in params["modules"]}


def per_target_effect(e):
    """Effect.applyBuffs: 'building'-sourced and a buff that moves a factory field -> per-target slot key."""
    if e.get("source") != "building":
        return False
    for bg in e["buffs"]:
        b = BUFF.get(bg)
        if b is None:
            continue
        if (b["productivityUpgrade"] != 0 or b["workforceModifierInPercent"] != 0 or b["additionalOutputs"]
                or (b["addedFertility"] not in (0, None)) or b["fuelDurationPercent"] != 0 or b["replaceInputs"]
                or b["workforceMaintenanceFactorUpgrade"] != 0
                or (b["replaceWorkforce"] and b["replaceWorkforce"].get("oldWorkforce") not in (0, None))):
            return True
    return False


CM_PRODUCTS = {p["guid"] for p in params["products"] if p.get("isConstructionMaterial")}
CM_FACTORIES = {f["guid"] for f in params["factories"] if any(o["product"] in CM_PRODUCTS for o in f.get("outputs", []))}
NEED_BY_GUID = {x["guid"]: x for x in params["needs"]}
NEED_UNIVERSE = {}
for _reg in ("Roman", "Celtic", "Egyptian"):
    _u = set()
    for _r in params["residenceBuildings"]:
        if _reg in _r["associatedRegions"]:
            for _nl in _r["needsList"]:
                _u.add((_r["populationLevel"], _nl["need"]))
    NEED_UNIVERSE[_reg] = _u
NEEDS_DISABLED = {}
changes = []      # dicts
notes = []        # informational, not changes
new_stores = {}


def rec(island, key, old, new, source, category, note=""):
    changes.append({"island": island, "key": key, "old": old, "new": new, "source": source, "category": category, "note": note})


def setkey(island, store, key, new, source, category, note="", default=None):
    """Set store[key]=new when it differs from the effective old value (stored value, else default)."""
    present = key in store
    old = store[key] if present else None
    eff_old = old if present else default
    try:
        same = (eff_old is not None) and float(eff_old) == float(new)
    except (TypeError, ValueError):
        same = eff_old == new
    if same:
        return False
    store[key] = new
    rec(island, key, old, new, source, category, note + ("" if present else (" (key was absent; default %s)" % default if default is not None else " (key was absent)")))
    return True


def same_type(oldval, newnum, as_float=False):
    """Keep the stored type: strings stay strings."""
    if isinstance(oldval, str):
        return str(int(newnum)) if float(newnum).is_integer() else str(newnum)
    return newnum


# ------------------------------------------------------------------ island matching
island_info = {}
for n in names:
    s = stores[n]
    k = area_key(s)
    if k is None:
        island_info[n] = None
        continue
    island_info[n] = {"key": k, "area": areas[k], "pl": pislands["a%d" % k], "region": SESSION_REGION[int(s["session"])]}
key_to_name = {v["key"]: n for n, v in island_info.items() if v}

# ------------------------------------------------------------------ per-island updates
researched = set(plan["techs"])
for n in names:
    s = stores[n]
    info = island_info[n]
    if not info:
        continue
    area, pl, region = info["area"], info["pl"], info["region"]
    store = s
    counts = area["counts"]

    # --- buildings.constructed
    for guid, f in list(FAC.items()) + list(RES.items()):
        if region not in f["associatedRegions"]:
            if counts.get(guid):
                notes.append({"island": n, "note": "save has %d of building %d (%s) that is not associated with region %s" % (counts[guid], guid, f["name"], region)})
            continue
        key = "%d.buildings.constructed" % guid
        is_cm = guid in CM_FACTORIES
        cat = "construction materials" if is_cm else "buildings"
        cmnote = "construction-material end factory (R50: planner materials count); fullyUtilizeConstructed kept" if is_cm else ""
        if guid in counts:
            new = counts[guid]
            setkey(n, store, key, same_type(store.get(key), new), "savegame", cat, cmnote)
        elif key in store and float(store[key]) != 0:
            setkey(n, store, key, same_type(store[key], 0), "savegame", cat, "type absent in the save (set to 0) " + cmnote)

    # --- patron
    p = area.get("patron")
    newp = str(p) if p else ""
    if p and p not in PATRON:
        notes.append({"island": n, "note": "patron %s is not in the calculator data" % p})
    if "selectedPatron" in store:
        if store["selectedPatron"] != newp:
            rec(n, "selectedPatron", store["selectedPatron"], newp, "savegame", "patron")
            store["selectedPatron"] = newp
    else:
        store["selectedPatron"] = newp
        rec(n, "selectedPatron", None, newp, "savegame", "patron", "key was absent")

    # --- devotion
    dv = int(area.get("devotion") or 0)
    if "devotion" in store:
        if float(store["devotion"]) != dv:
            rec(n, "devotion", store["devotion"], same_type(store["devotion"], dv), "savegame", "devotion")
            store["devotion"] = same_type(store["devotion"], dv)
    elif dv != 0:
        store["devotion"] = dv
        rec(n, "devotion", None, dv, "savegame", "devotion", "key was absent")

    # --- fertilities
    present = set(area["fertilities"]) | set(area["lode"])
    missing = set(pl["missing_fertilities"])
    for g, fe in FERT.items():
        matches = (not fe["regions"]) or region in fe["regions"]
        key = "island.fertility.%d.checked" % g
        if g in present:
            new = "1"
        elif g in missing:
            new = "0"
        else:
            continue
        setkey(n, store, key, new, "savegame", "fertility", "present in save" if new == "1" else "absent in save (planner fertility universe)", default=("1" if matches else "0"))

    # --- items / building effects / aqueduct / modules
    pf = pl["factories"]
    present_types = {g for g in counts if g in FAC}
    # item states wanted: (factory, item) -> state
    want = {}
    dup = 0
    for fs, spec in pf.items():
        fg = int(fs)
        for slot in spec["items"]:
            ig = slot["item"]
            it = ITEM.get(ig)
            if it is None:
                notes.append({"island": n, "note": "plan item %d on factory %d is not in the calculator data" % (ig, fg)})
                continue
            if fg not in it["targets"] or region not in FAC[fg]["associatedRegions"]:
                notes.append({"island": n, "note": "plan item %d is not applicable to factory %d in the calculator" % (ig, fg)})
                continue
            st = 2 if slot["boosted"] else 1
            if st == 2 and not it.get("boostBuffs"):
                st = 1
                notes.append({"island": n, "note": "item %d is boosted in the save but has no boost variant in the calculator: state 1" % ig})
            if (fg, ig) in want:
                dup += 1
                st = max(st, want[(fg, ig)])
            want[(fg, ig)] = st
    wanted_eff = set()
    for fs, spec in pf.items():
        fg = int(fs)
        for eg in list(spec["effects"]) + list(spec["building_effects"]):
            e = EFF.get(eg)
            if e is None:
                notes.append({"island": n, "note": "plan effect %d is not in the calculator data" % eg})
                continue
            if not per_target_effect(e):
                notes.append({"island": n, "note": "effect %d is not a per-target building effect in the calculator (island.effect key)" % eg, "factory": fg})
                continue
            if fg not in e.get("targets", []):
                notes.append({"island": n, "note": "effect %d does not target factory %d in the calculator" % (eg, fg)})
                continue
            wanted_eff.add((fg, eg))
    if dup:
        notes.append({"island": n, "note": "%d (factory,item) pairs appear with several boost states in the plan; the highest is used" % dup})

    pat = re.compile(r"^(\d+)\[(\d+)\]\.scaling$")
    old_slots = {}
    for key in list(store):
        m = pat.match(key)
        if m:
            old_slots[(int(m.group(1)), int(m.group(2)))] = key
    for (fg, xg), key in sorted(old_slots.items()):
        if xg in ITEM:
            new = want.get((fg, xg), 0)
            if float(store[key]) != new:
                note = "not in the plan's applied items" if new == 0 else "state from plan (0 off, 1 base, 2 boosted)"
                if new == 0 and fg not in present_types:
                    note += "; factory type not built in the save"
                setkey(n, store, key, new, "savegame" if new else "derived by rule", "items", note)
        elif xg in EFF:
            e = EFF[xg]
            new = 1 if (fg, xg) in wanted_eff else 0
            if float(store[key]) != new:
                note = "not applied by range in the save" if new == 0 else "applied by range (plan building_effects/effects)"
                if new == 0 and fg not in present_types:
                    note += "; factory type not built in the save"
                setkey(n, store, key, new, "savegame" if new else "derived by rule", "buildingEffects", note)
        else:
            notes.append({"island": n, "key": key, "note": "unknown GUID in item/effect slot key, left unchanged"})
    for (fg, ig), st in sorted(want.items()):
        key = "%d[%d].scaling" % (fg, ig)
        if (fg, ig) not in old_slots:
            setkey(n, store, key, st, "savegame", "items", "state from plan (0 off, 1 base, 2 boosted)", default=0)
    for (fg, eg) in sorted(wanted_eff):
        key = "%d[%d].scaling" % (fg, eg)
        if (fg, eg) not in old_slots:
            setkey(n, store, key, 1, "savegame", "buildingEffects", "applied by range (plan building_effects/effects)", default=0)

    for fg in sorted(present_types):
        f = FAC[fg]
        if region not in f["associatedRegions"]:
            continue
        spec = pf.get(str(fg), {})
        if f.get("aqueductProductivityBuff"):
            key = "%d.aqueductBuff.checked" % fg
            new = 1 if spec.get("aqueduct") else 0
            ov = store.get(key)
            setkey(n, store, key, same_type(ov, new) if ov is not None else new, "savegame", "aqueduct", "aqueduct distributor in range of the majority" if new else "no aqueduct in range of the majority", default=0)
        if f.get("additionalModule"):
            mg = f["additionalModule"]
            key = "%d.module[%d].checked" % (fg, mg)
            new = "1" if spec.get("silo") else "0"
            setkey(n, store, key, new, "savegame", "modules", "module owner effect on the majority" if new == "1" else "no module on the majority", default=0)

    # --- disabled needs
    dis = pl.get("disabled_needs") or {}
    dis_set = set()
    for lvl, needs in dis.items():
        for ng in needs:
            key = "%s[%d].checked" % (lvl, ng)
            dis_set.add(key)
            if int(lvl) not in POPL or ng not in NEED:
                notes.append({"island": n, "note": "disabled need %s/%d not in the calculator data" % (lvl, ng)})
            setkey(n, store, key, "0", "savegame", "needs", "need banned in the save", default="1")
    # DLC-locked needs of Latium and Albion levels: not banned in the save = on (R43), explicit value
    if region in ("Roman", "Celtic"):
        for (lvl, nd) in sorted(NEED_UNIVERSE[region]):
            dl = NEED_BY_GUID[nd].get("dlcUnlocks") or []
            if not dl:
                continue
            key = "%d[%d].checked" % (lvl, nd)
            if key in dis_set:
                continue
            dlc3 = 67904 in dl
            if key in store:
                if str(store[key]) != "1":
                    setkey(n, store, key, "1", "derived by rule", "needs", "R43: need of DLC %s not banned in the save (was off)" % ("3" if dlc3 else "/".join(map(str, dl))))
            elif dlc3:
                store[key] = "1"
                rec(n, key, None, "1", "derived by rule", "needs", "R43: DLC 3 need not banned in the save (explicit 1; key was absent)")
    NEEDS_DISABLED[n] = dis_set

# ------------------------------------------------------------------ discoveries
gl = json.loads(d["globalEffects"])
ss = json.loads(d["sessionSettings"])
counts_t = {int(k): v for k, v in plan["tech_counts"].items()}
on_off = []
for tg, t in TECH.items():
    for eg in t["effects"]:
        key = "%d.scaling" % eg
        if t.get("isRepeatable"):
            new = counts_t.get(tg, 0)
        else:
            new = 1 if tg in researched else 0
        old = gl.get(key)
        if old is None or float(old) != new:
            if old is not None and float(old) > 0 and new == 0:
                on_off.append((key, t["name"]))
            ov = same_type(old, new) if old is not None else new
            rec("(global)", "globalEffects/" + key, old, ov, "savegame", "discoveries",
                "%s: %s" % (t["name"], "repeat count %d" % new if t.get("isRepeatable") else ("researched" if new else "not researched")))
            gl[key] = ov
untech = [k for k in gl if int(k.split(".")[0]) not in {e for t in TECH.values() for e in t["effects"]}]
notes.append({"island": "(global)", "note": "global effects without a discovery counterpart, unchanged: %s" % untech})

vol_levels = {"145095": 145068, "148043": 148041, "145099": None}
level = 1 + 2 + (2 if 145106 in researched else 0)    # volcano defaultMaximumFactor 2, Volcanic Soil level 5 tech
for eg, unlock in vol_levels.items():
    key = "session.3245.effect.%s.scaling" % eg
    unlocked = unlock is None or unlock in researched
    new = level if unlocked else 0
    old = ss.get(key)
    if old is None or float(old) != new:
        if old is not None and float(old) > 0 and new == 0:
            on_off.append((key, "volcano"))
        ov = same_type(old, new) if old is not None else str(new)
        rec("(session)", "sessionSettings/" + key, old, ov, "derived by rule", "discoveries", "volcano effect, level %d" % level)
        ss[key] = ov
nile = "session.149679.effect.155616.scaling"
new_nile = 1  # seasons enabled in the save (Aegyptus session present)
if float(ss.get(nile, 0)) != new_nile:
    rec("(session)", "sessionSettings/" + nile, ss.get(nile), str(new_nile), "derived by rule", "discoveries", "Nile flood seasons")
    ss[nile] = str(new_nile)

# ------------------------------------------------------------------ trade routes
old_tr = json.loads(d["tradeRoutes"])
new_tr = copy.deepcopy(old_tr)
plan_ids = list(pislands)
weights, edges, diag = derive(save, plan_ids, skip_noships=True)
plan_amount = {}
for i in plan["islands"]:
    for p, sb in i["supplied_by"].items():
        plan_amount[(i["id"], int(p))] = sb

# ---- recorded visits: measured rates (net tons received per minute, window = first entry of the route .. last entry of the save)
VIS_ALL = json.load(open(TRADE_VISITS, encoding="utf-8"))
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

trade = {"derived_pairs": 0, "added": [], "skipped": [], "agreement": [], "user_only_pairs": [], "ordinary_added": [], "measured_only_added": [], "local_kept": [], "flags_set": []}
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
        locals_ = sorted(g for g in producers.get(product, ()) if island_info[to]["area"]["counts"].get(g))
        # R51: the island's own default supplier choice stays; a non-factory default (null, passive trade, extra good) is a user choice
        if dtype != "factory" or not locals_:
            reason = "island default supplier type %s kept (user choice)" % dtype
            trade["agreement"].append(dict(base, status="differs", user=[{"defaultSupplier.type": dtype}]))
            trade["local_kept"].append({"island": to, "productGUID": product, "reason": reason, "local_factories": locals_})
            rec(to, "tradeRoutes:%d" % product, dtype, json.dumps(dsum), "unchanged", "tradeRoutes", reason + "; derived import not applied")
            continue
        ddef = next(x for x in derived if x["isDefaultSupplier"])
        if would_cycle(ddef["from"], to, product):
            trade["skipped"].append(dict(base, reason="default supplier %s -> %s closes a cycle in the supplier chain" % (ddef["from"], to)))
            continue
        flag_ok = True
        for g in locals_:
            fk = "%d.buildings.fullyUtilizeConstructed" % g
            if fk in stores[to] and str(stores[to][fk]) != "1":
                trade["local_kept"].append({"island": to, "productGUID": product, "reason": "fullyUtilizeConstructed of factory %d is set to %s by the user" % (g, stores[to][fk]), "local_factories": locals_})
                rec(to, fk, stores[to][fk], "1", "unchanged", "local producers", "R51 would set fully utilized; user value kept")
                flag_ok = False
        trade["agreement"].append(dict(base, status="not entered", user=[]))
        default_from[(to, product)] = ddef["from"]
        for g in locals_:
            fk = "%d.buildings.fullyUtilizeConstructed" % g
            if fk in stores[to] and str(stores[to][fk]) != "1":
                continue
            setkey(to, stores[to], fk, "1", "derived by rule", "local producers",
                   "R51: island produces product %d itself (%d built) and imports the rest; local producer fully utilized" % (product, island_info[to]["area"]["counts"][g]),
                   default=(1 if (FAC[g]["outputs"][0]["product"] in CM_PRODUCTS) else 0))
            trade["flags_set"].append({"island": to, "factory": g, "product": product})
        for x in derived:
            entry = {"productGUID": product, "from": x["from"], "to": to, "userSetAmount": 0, "isDefaultSupplier": x["isDefaultSupplier"]}
            new_tr.append(entry)
            trade["added"].append(entry)
            trade["ordinary_added"].append(dict(entry, basis="R51: no amount; default import covers demand minus the fully utilized local production", why="local producer"))
            rec(to, "tradeRoutes:%d:%s>%s" % (product, entry["from"], entry["to"]), None, json.dumps(entry), "derived by rule", "tradeRoutes",
                "R51 local-producer pair; %s; no minimum amount" % ("default supplier (import of the remaining demand)" if entry["isDefaultSupplier"] else "ordinary route, minimum 0"))
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

derived_pairs_keys = {(key_to_name[int(r[1:])], p) for (r, p) in weights if int(r[1:]) in key_to_name}
trade["user_only_pairs"] = sorted({(r["to"], r["productGUID"]) for r in old_tr} - derived_pairs_keys)

# ------------------------------------------------------------------ needs that stay off (analysis)
imports_to = collections.defaultdict(set)
for _r in new_tr:
    imports_to[_r["to"]].add(_r["productGUID"])
kept_off = []
for n in names:
    info = island_info[n]
    if not info:
        continue
    s = stores[n]
    region, area = info["region"], info["area"]
    dis_set = NEEDS_DISABLED.get(n, set())
    counts = area["counts"]
    resid = collections.Counter()
    for r_ in params["residenceBuildings"]:
        if region in r_["associatedRegions"]:
            resid[r_["populationLevel"]] += counts.get(r_["guid"], 0)
    outside = []
    for key, v in s.items():
        m = re.match(r"^(\d+)\[(\d+)\]\.checked$", key)
        if not m or str(v) != "0" or key in dis_set:
            continue
        lvl, nd = int(m.group(1)), int(m.group(2))
        if (lvl, nd) not in NEED_UNIVERSE[region]:
            outside.append(key)
            continue
        need = NEED_BY_GUID.get(nd, {})
        prod = need.get("needProduct")
        reasons = []
        if need.get("dlcUnlocks"):
            reasons.append("DLC-locked need still off (region %s)" % region)
        elif need.get("isBuilding"):
            reasons.append("need for a public building")
        else:
            local = any(counts.get(f) for f in producers.get(prod, ()))
            if not producers.get(prod):
                reasons.append("good without producer in the data")
            elif not any(region in FAC[f]["associatedRegions"] for f in producers[prod]):
                reasons.append("good cannot be produced in the island's region (import only)")
            elif not local and prod not in imports_to[n]:
                reasons.append("good neither produced nor imported on the island")
        if resid[lvl] == 0:
            reasons.append("tier has no residences on the island")
        if not reasons:
            reasons.append("switched off by the user (good is available)")
        grp = reasons[0].split(" (")[0] if len(reasons) == 1 else reasons[0].split(" (")[0] + " + " + reasons[1]
        kept_off.append({"island": n, "region": region, "key": key, "reason": grp})
        rec(n, key, "0", "0", "unchanged", "needs, kept off", grp)
    if outside:
        kept_off.append({"island": n, "region": region, "key": "(%d keys)" % len(outside), "reason": "level or need not part of the island's region (no effect)", "count": len(outside)})
        rec(n, "(%d need keys of other regions' levels)" % len(outside), "0", "0", "unchanged", "needs, kept off", "level or need not part of the island's region (no effect)")
kept_summary = collections.defaultdict(collections.Counter)
for k in kept_off:
    kept_summary[k["reason"]][k["island"]] += k.get("count", 1)
trade["needs_kept_off"] = {r_: dict(c_) for r_, c_ in kept_summary.items()}

# ------------------------------------------------------------------ serialise
def js(o):
    return json.dumps(o, indent=4, ensure_ascii=False)


out = {}
for k, v in d.items():
    if k in stores:
        out[k] = js(stores[k])
    elif k == "tradeRoutes":
        out[k] = js(new_tr)
    elif k == "globalEffects":
        out[k] = js(gl)
    elif k == "sessionSettings":
        out[k] = js(ss)
    else:
        out[k] = v
open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js(out))

# ------------------------------------------------------------------ route diagnostics
trade["routes_total"] = len(diag)
trade["routes_with_flows"] = sum(1 for x in diag.values() if x["edges"])
trade["flow_edges_pairs"] = len(weights)
def ids_of(pred):
    return sorted(r for r, x in diag.items() if pred(x))
trade["approximate"] = {
    "relay_stops": ids_of(lambda x: x["relay"]),
    "several_sources_same_product": ids_of(lambda x: x["multi_source"]),
    "same_sink_visited_twice": ids_of(lambda x: x["sink_twice"]),
    "non_player_station": ids_of(lambda x: x["nonplayer"]),
    "good_without_source": ids_of(lambda x: x["no_source"]),
    "no_ships": ids_of(lambda x: x["ships"] == 0),
    "no_flows": ids_of(lambda x: x["edges"] == 0),
}
trade["on_off_changes"] = on_off

counts_by_cat = collections.Counter(c["category"] for c in changes if c["source"] != "unchanged")
counts_by_island = collections.Counter(c["island"] for c in changes if c["source"] != "unchanged")
matrix = collections.defaultdict(dict)
for c in changes:
    if c["source"] != "unchanged":
        matrix[c["island"]][c["category"]] = matrix[c["island"]].get(c["category"], 0) + 1
by_source = collections.Counter(c["source"] for c in changes)

def nz(prefix_pat, st):
    return sum(1 for n_, s_ in st.items() for k, v in s_.items() if re.match(prefix_pat, k) and float(v or 0) > 0)
old_stores = {n_: json.loads(d[n_]) for n_ in names}
stat = {}
def slots(st, kind, minv):
    tot = 0
    for n_ in names:
        if not island_info[n_]:
            continue
        for k, v in st[n_].items():
            m = re.match(r"^(\d+)\[(\d+)\]\.scaling$", k)
            if m and ((int(m.group(2)) in ITEM) == (kind == "item")) and float(v) >= minv:
                tot += 1
    return tot
cur_stores = {n_: stores[n_] for n_ in names}
stat["item_slots_on"] = {"old": slots(old_stores, "item", 1), "new": slots(cur_stores, "item", 1)}
stat["item_slots_boosted"] = {"old": slots(old_stores, "item", 2), "new": slots(cur_stores, "item", 2)}
stat["building_effect_slots_on"] = {"old": slots(old_stores, "effect", 1), "new": slots(cur_stores, "effect", 1)}
for label, pat in (("aqueduct_on", r"^\d+\.aqueductBuff\.checked$"), ("modules_on", r"^\d+\.module\[\d+\]\.checked$")):
    stat[label] = {"old": nz(pat, {n_: old_stores[n_] for n_ in names if island_info[n_]}), "new": nz(pat, {n_: stores[n_] for n_ in names if island_info[n_]})}
report = {"output": OUT_JSON.name,"summary": {"changes": sum(counts_by_cat.values()), "by_category": counts_by_cat, "by_island": counts_by_island,
                                          "by_island_and_category": matrix, "by_source": by_source, "state_counts_old_vs_new": stat,
                                          "unchanged_rows": sum(1 for c in changes if c["source"] == "unchanged"),
                                          "effects_on_to_off": on_off}, "trade": trade, "notes": notes, "changes": changes}
json.dump(report, open(OUT_REPORT, "w", encoding="utf-8"), indent=2, ensure_ascii=False, default=lambda o: dict(o))
with open(OUT_CSV, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["island", "key", "old", "new", "source", "category", "note"])
    for c in changes:
        w.writerow([c["island"], c["key"], "" if c["old"] is None else c["old"], c["new"], c["source"], c["category"], c["note"]])
print(json.dumps({"by_category": counts_by_cat, "by_island": counts_by_island, "on_off": on_off}, indent=1, default=dict))
print("trade: derived pairs", trade["derived_pairs"], "added", len(trade["added"]), "skipped", len(trade["skipped"]),
      collections.Counter(s["reason"].split("(")[0].split(" closes")[0] for s in trade["skipped"]))
print("agreement", collections.Counter(a["status"] for a in trade["agreement"]), "notes", len(notes))
