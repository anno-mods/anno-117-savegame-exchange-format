import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, struct, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream
from paxplanner.model.gamedata import GameData
gd=GameData()
d=json.load(open(r"x\extract.json")); B=json.load(open(r"research2\boost.json"))
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
a=[x for x in d["areas"] if x["key"]==8513][0]
bycount=collections.Counter(s["building"] for s in a["sockets"])
print({(b,gd.name(b,"english")):c for b,c in bycount.items()})
want={s["id"]:s for s in a["sockets"]}
def pos(h): return struct.unpack("<3f",bytes.fromhex(h))
def want_f(p): return len(p)==8 and p[-5]=="AreaManager_8513" and p[-3]=="GameObject" and p[-2]=="objects"
for p,n in stream(r"x\session_0.xml", want_f):
    i=n.get("ID").text
    if i in want:
        s=want[i]; dr=n.get("Direction")
        print("\n",s["building"],gd.name(s["building"],"english"),"id",u(i),"pos",pos(n.get("Position").text),"dir",struct.unpack("<f",bytes.fromhex(dr.text))[0] if dr is not None else 0.0, "owner?",n.get("OwnerProfile") is not None)
        sock=n.find("ItemContainer/SocketContainer/SocketItems")
        for e in sock.kids:
            iid=u(e.find("ItemReference/ID").text); g=u(e.get("GUID").text)
            im=B["items"].get(str(iid))
            print("   item",g,gd.name(g,"english"),"id",iid,"boosted",im and im["boosted"],"cond",im and im["cond"], "activation",u(e.get("ActivationTime").text))
        en=n.find("ItemContainer/SocketContainer/CurrentlyEnabledItemSocketCount")
        print("   enabledSockets",en.text if en is not None else None)
        break
