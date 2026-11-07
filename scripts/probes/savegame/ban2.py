import os as _os
from pathlib import Path as _Path
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
_CONFIG = str(_Path(__file__).resolve().parents[3] / "data" / "raw" / "calculator_configs" / "Marcia 69.json")
import sys, json, re, pickle, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.dont_write_bytecode = True
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
from paxplanner.model.gamedata import GameData
gd = GameData()
SP = _SCRATCH
allareas = pickle.load(open(SP + r"\x\areas_all.pkl", "rb"))
calc = json.load(open(_CONFIG, encoding="utf-8"))
r0 = next(iter(gd.residences.values()))
print("residence needs sample", type(r0["needs"]), str(r0["needs"])[:200])
by_key = {}
for si, areas in enumerate(allareas):
    for a in areas:
        by_key[a["key"]] = a
def needs_for(product, level):
    res = gd.residence_by_level.get(level)
    out = []
    for n in (res or {}).get("needs", []):
        g = n if isinstance(n, int) else n.get("need") or n.get("guid")
        if (gd.needs.get(g) or {}).get("product") == product:
            out.append(g)
    return out
tot = collections.Counter()
for nm in json.loads(calc["islandNames"]):
    isl = json.loads(calc[nm])
    cid, cai = isl.get("gameConnector.islandID"), isl.get("gameConnector.areaIndex")
    if cid is None: continue
    code = {3245: 1, 6627: 3, 149679: 4}[isl["session"]]
    a = by_key.get((cai << 13) | (cid << 6) | code)
    saved = set()
    for prod, lvl in a.get("paused", []):
        for n in needs_for(prod, lvl):
            saved.add((lvl, n))
    cal_off = {(int(m.group(1)), int(m.group(2))) for k, v in isl.items() if (m := re.match(r"^(\d+)\[(\d+)\]\.checked$", k)) and str(v) == "0"}
    cal_on = {(int(m.group(1)), int(m.group(2))) for k, v in isl.items() if (m := re.match(r"^(\d+)\[(\d+)\]\.checked$", k)) and str(v) == "1"}
    both = saved & cal_off
    s_only_on = saved & cal_on   # save bans, calc says supplied
    s_only_unk = saved - cal_off - cal_on
    c_only = cal_off - saved
    tot["both"] += len(both); tot["save_banned_calc_on"] += len(s_only_on); tot["save_banned_calc_unentered"] += len(s_only_unk); tot["calc_off_save_not"] += len(c_only)
    if saved or cal_off:
        print(nm, "save banned", len(saved), "calc off", len(cal_off), "| both", len(both), "save-only(calc on)", len(s_only_on), "save-only(not entered)", len(s_only_unk), "calc-only", len(c_only))
        if c_only and len(c_only) <= 12:
            print("    calc-only:", [(gd.name(l, "english"), gd.needs[n]["name"]) for l, n in sorted(c_only)])
        if s_only_on:
            print("    save banned, calc supplied:", [(gd.name(l, "english"), gd.needs[n]["name"]) for l, n in sorted(s_only_on)])
print(dict(tot))
