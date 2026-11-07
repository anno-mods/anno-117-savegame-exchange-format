"""Reduce the decoded savegame XML (<scratch>/x/session_N.xml) to a compact JSON of what the plan needs.
Read-only on the savegame; works on the already decoded copies."""
import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import json, re, struct, sys
sys.dont_write_bytecode = True
SP = _SCRATCH
sys.path.insert(0, SP)
from tree import stream


def u32(h):
    return int.from_bytes(bytes.fromhex(h), "little") if h else 0


def f32(h):
    return struct.unpack("<f", bytes.fromhex(h))[0] if h else 0.0


def kv_pairs(node):
    """FileDB map: kids alternate key leaf / value node."""
    ks = node.kids
    return [(ks[i], ks[i + 1]) for i in range(0, len(ks) - 1, 2)]


# session GUIDs in file order
guids = []
inside = False
for line in open(SP + r"\x\data_raw.xml", encoding="utf-8", errors="replace"):
    s = line.strip()
    if s == "<GameSessions>":
        inside = True
    elif s == "</GameSessions>":
        break
    elif inside:
        m = re.match(r"<SessionGUID>([0-9A-F]+)</SessionGUID>", s)
        if m:
            guids.append(u32(m.group(1)))
print("session guids", guids)

# empire-wide religion (outer XML): participant 41
dominant = None
for path, n in stream(SP + r"\x\data_raw.xml", lambda p: p[-1] == "ParticipantPatronInfos"):
    for k, v in kv_pairs(n.get("Data")):
        if u32(k.text) == 41:
            a = v.get("ActiveDominantPatronGuid")
            dominant = u32(a.text) if a is not None and a.text else None
            pats = {}
            for pk, pv in kv_pairs(v.get("Patrons")):
                cd = pv.get("CumulativeDevotion")
                pats[u32(pk.text)] = u32(cd.text) if cd is not None else 0
    break
print("dominant", dominant, "cumulative devotion per patron", pats)

out = {"sessions": guids, "dominant_patron": dominant, "patron_cumulative_devotion": pats, "areas": []}

for si in range(len(guids)):
    X = SP + r"\x\session_%d.xml" % si
    human = {}
    items = {}
    areas = {}

    def want(p):
        if p[-1] == "AreaInfo" and len(p) == 3:
            return True
        if p[-1] == "ItemMap" and len(p) == 4:
            return True
        if len(p) == 5 and p[-2].startswith("AreaManager_") and p[-1] in ("AreaObjectManager", "AreaReligionManager"):
            return int(p[-2].split("_")[1]) in human
        return False

    for path, n in stream(X, want):
        if n.tag == "AreaInfo":
            for k, v in kv_pairs(n):
                key = int(u32(k.text))
                op = v.get("OwnerProfile")
                if op is not None and u32(op.text) == 41:
                    fert = v.get("Fertility")
                    lode = v.find("LimitedLodeComponent/LimitedLodeFertilities")
                    human[key] = {
                        "key": key,
                        "fertilities": sorted(u32(c.text) for c in fert.kids) if fert is not None else [],
                        "lode": sorted(u32(c.text) for c in lode.kids) if lode is not None else [],
                        "cityNameGuid": v.get("CityNameGuid").text if v.get("CityNameGuid") is not None else None,
                        "cityNameIterator": u32(v.get("CityNameIterator").text) if v.get("CityNameIterator") is not None else None,
                    }
        elif n.tag == "ItemMap":
            for k, v in kv_pairs(n):
                g = v.get("GUID")
                b = v.get("IsBoosted")
                items[k.text] = {"guid": u32(g.text) if g is not None else None, "boosted": bool(b is not None and b.text == "01")}
        elif n.tag == "AreaReligionManager":
            a = int(path[-1].split("_")[1])
            pg = n.get("PatronGuid")
            dv = n.get("Devotion")
            fr = n.get("DevotionFraction")
            human[a]["patron"] = u32(pg.text) if pg is not None and pg.text else None
            human[a]["devotion"] = u32(dv.text) if dv is not None and dv.text else 0
            human[a]["devotionFraction"] = f32(fr.text) if fr is not None and fr.text else 0.0
            human[a]["islandEffectIds"] = [u32(c.text[:8]) for c in n.get("IslandEffectIDs").kids] if n.get("IslandEffectIDs") is not None else []
            human[a]["wonderEffectIds"] = [u32(c.text[:8]) for c in n.get("WonderEffectIDs").kids] if n.get("WonderEffectIDs") is not None else []
        elif n.tag == "AreaObjectManager":
            a = int(path[-1].split("_")[1])
            objs = n.find("GameObject/objects")
            counts = {}
            residents = {}
            socket = []
            for o in (objs.kids if objs is not None else []):
                g = o.get("guid")
                if g is None:
                    continue
                guid = u32(g.text)
                if o.get("OwnerProfile") is not None and u32(o.get("OwnerProfile").text) != 41:
                    continue
                counts[guid] = counts.get(guid, 0) + 1
                r = o.get("Residence7")
                if r is not None and r.get("ResidentCount") is not None:
                    residents[guid] = residents.get(guid, 0.0) + f32(r.get("ResidentCount").text)
                ic = o.find("ItemContainer/SocketContainer/SocketItems")
                if ic is not None and ic.kids:
                    socket.append({"building": guid, "id": u32(o.get("ID").text[:8]) if False else o.get("ID").text,
                                   "items": [{"item": u32(s.get("GUID").text), "ref": (s.find("ItemReference/ID").text if s.find("ItemReference/ID") is not None else None)} for s in ic.kids if s.get("GUID") is not None]})
            human[a]["counts"] = counts
            human[a]["residents"] = residents
            human[a]["sockets"] = socket
    for key, h in human.items():
        h["sessionIndex"] = si
        h["sessionGuid"] = guids[si]
        h["itemMap"] = {}
        out["areas"].append(h)
    out.setdefault("itemMaps", {})[str(si)] = items
    print("session", si, "human areas", sorted(human), "items", len(items))

json.dump(out, open(SP + r"\x\extract.json", "w"))
