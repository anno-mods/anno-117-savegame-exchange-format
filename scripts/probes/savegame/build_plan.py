"""Build a Taludas Planner plan from the reduced savegame data (x/extract.json + x/lt_parse.pkl)."""
import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import json, pickle, struct, sys
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
SP = _SCRATCH
sys.path.insert(0, SP)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.path.insert(0, r"C:\dev\Anno-117-Layout-Tool")
from paxplanner.model.gamedata import GameData
from paxplanner.model.project import FactorySettings, IslandPlan, ItemSlot, Plan
import savegame_parser as sp
from tree import stream

gd = GameData()
ex = json.load(open(SP + r"\x\extract.json"))
lt = pickle.load(open(SP + r"\x\lt_parse.pkl", "rb"))

REGION_NAME = {"Roman": "Latium", "Celtic": "Albion", "Egyptian": "Aegyptus"}
SIZE_WORD = {"small": "Small", "medium": "Medium", "large": "Large", "extralarge": "XL"}


def u32(h):
    return int.from_bytes(bytes.fromhex(h), "little") if h else 0


# researched techs of the human (the MetaTechHandler with a research queue / progress)
techs, tech_counts, queue = [], {}, []
for path, n in stream(SP + r"\x\data_raw.xml", lambda p: p[-1] == "MetaTechHandler"):
    prog = n.get("TechProgress")
    if prog is not None and prog.kids:
        techs = [u32(c.text) for c in n.get("TechCompleted").kids]
        rep = n.get("TechRepeatables").kids
        tech_counts = {u32(rep[i].text): u32(rep[i + 1].text) for i in range(0, len(rep) - 1, 2)}
        queue = [u32(c.text) for c in n.get("ResearchQueue").kids]
        break
known_techs = [t for t in techs if t in gd.techs]
tech_counts = {t: c for t, c in tech_counts.items() if t in gd.techs}
queue = [t for t in queue if t in gd.techs]
print("techs", len(techs), "known", len(known_techs), "repeat", tech_counts, "queue", queue)

VILLA_TEMPLATES = {"VillaUrban", "GuestHouse"}
plan = Plan(name="Marcia 69")
plan.techs = sorted(set(known_techs) | set(tech_counts))
plan.tech_counts = tech_counts
plan.research_queue = queue
plan.dominant_patron = ex["dominant_patron"] if ex["dominant_patron"] in gd.patrons else None

report = []
for a in sorted(ex["areas"], key=lambda a: (a["sessionIndex"], a["key"])):
    key = a["key"]
    island_id, area_index, rcode = (key >> 6) & 127, key >> 13, key & 63
    session = a["sessionGuid"]
    region = gd.session_region(session)
    rname = REGION_NAME.get(region, str(region))
    counts = {int(g): c for g, c in a["counts"].items()}
    residences = {}
    for g, c in counts.items():
        if g in gd.residences:
            lvl = gd.residences[g]["populationLevel"]
            residences[lvl] = residences.get(lvl, 0) + c
    existing = {g: c for g, c in counts.items() if g in gd.factories}
    present = set(a["fertilities"]) | set(a["lode"])
    missing = sorted(f for f, rec in gd.fertilities.items() if rec.get("regions") and gd.natural_fertility(f, region) and f not in present)
    patron = a.get("patron")
    patron = patron if patron in gd.patrons else None

    # items
    item_map = ex["itemMaps"][str(a["sessionIndex"])]
    residence_items, unmapped_items = [], []
    for s in a["sockets"]:
        b = gd.buildings.get(s["building"]) or {}
        for it in s["items"]:
            rec = gd.items.get(it["item"])
            boosted = bool((item_map.get(it["ref"]) or {}).get("boosted"))
            if rec is None:
                unmapped_items.append((s["building"], it["item"], "unknown item"))
            elif b.get("template") in VILLA_TEMPLATES and rec.get("allocation") == "Villa" and set(r for r in gd.residences) & set((rec.get("effect") or {}).get("targets") or []):
                residence_items.append(ItemSlot(it["item"], boosted))
            else:
                unmapped_items.append((s["building"], it["item"], rec.get("allocation")))

    # island size from the layout tool's template matching
    size = "Large"
    size_note = "default"
    tm, ab = lt[a["sessionIndex"]]
    if key in ab and tm:
        t = sp._match_template(ab[key], [x for x in tm])
        if t:
            stem = t["name"]
            word = stem.split("_island_")[1].split("_")[0] if "_island_" in stem else ""
            if word in SIZE_WORD:
                size, size_note = SIZE_WORD[word], stem
    name = f"{rname} {island_id}" + (f".{area_index}" if area_index != 1 else "")
    isl = IslandPlan(
        name=name,
        session=session,
        id=f"a{key}",
        residences=residences,
        existing=existing,
        patron=patron,
        devotion=float(a.get("devotion") or 0),
        missing_fertilities=missing,
        residence_items=residence_items,
        island_size=size,
    )
    plan.islands.append(isl)
    report.append(dict(name=name, key=key, islandID=island_id, areaIndex=area_index, regionCode=rcode, session=session, patron=a.get("patron"),
                       devotion=a.get("devotion"), residences=residences, existing_n=sum(existing.values()), missing=missing,
                       present=sorted(present), items=len(residence_items), unmapped_items=unmapped_items, size=size_note,
                       counts=counts, residents={int(g): v for g, v in a["residents"].items()}))

out = SP + r"\marcia69.plan.json"
plan.save(__import__("pathlib").Path(out))
json.dump(report, open(SP + r"\x\report.json", "w"), indent=1)
print("wrote", out, len(plan.islands), "islands")
for r in report:
    print(r["name"], r["key"], "patron", r["patron"], "dev", r["devotion"], "res", r["residences"], "fact", r["existing_n"], "miss", r["missing"], "items", r["items"], "unmapped", len(r["unmapped_items"]), r["size"])
