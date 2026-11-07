import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import sys, json, struct, collections
sys.dont_write_bytecode=True
sys.path.insert(0,_SCRATCH)
sys.path.insert(0, r"C:\dev\Anno-117-Planner")
sys.stdout.reconfigure(encoding="utf-8")
from tree import stream, show
from paxplanner.model.gamedata import GameData
gd=GameData()
def u(h): return int.from_bytes(bytes.fromhex(h),"little") if h else 0
# object id -> guid
objs={}
def wf(p): return len(p)==8 and p[-5]=="AreaManager_8513" and p[-3]=="GameObject" and p[-2]=="objects"
fe={}
for p,n in stream(r"x\session_0.xml", wf):
    objs[u(n.get("ID").text)]=u(n.get("guid").text)
    b=n.get("Building")
    if b is not None and b.get("FunctionalEffectIDs") is not None and b.get("FunctionalEffectIDs").kids:
        fe[u(n.get("ID").text)]=[u(k.text) for k in b.get("FunctionalEffectIDs").kids]
print(len(objs),"objects", len(fe),"with FunctionalEffectIDs")
for p,n in stream(r"x\session_0.xml", lambda p: len(p)==5 and p[-2]=="AreaManager_8513" and p[-1]=="AreaEffectManager"):
    E=n.get("Effects").kids
    bysrc=collections.Counter(); byeff=collections.Counter(); sc=collections.Counter(); dist=collections.defaultdict(set); end=0; ex=0
    for e in E:
        g=u(e.get("Guid").text); so=e.find("Source/ObjectID"); s=u(so.text) if so is not None else -2; d=e.get("Distance"); 
        byeff[g]+=1; bysrc[objs.get(s,-1)]+=1; sc[e.find("Scope/value/id").text]+=1; srcmissing=0
        if d is not None: dist[g].add(u(d.text))
        if e.get("EndTimestamp").text: end+=1
        for k in e.kids:
            pass
    print(len(E),"effects; with EndTimestamp",end, "scope ids",dict(sc), "unresolved sources",bysrc.get(-1))
    print("per effect guid:")
    for g,c in byeff.most_common(12): print("  ",g,gd.name(g,"english"),c,sorted(dist[g]))
    print("per source building guid:")
    for g,c in bysrc.most_common(10): print("  ",g,gd.name(g,"english"),c)
    rb=n.get("RadiusEffectRangeBuffs").kids
    print("RadiusEffectRangeBuffs",len(rb)//2)
    for i in range(0,min(len(rb),10),2):
        print("  ",u(rb[i].text),gd.name(u(rb[i].text),"english"),[(u(x.kids[0].text),u(x.kids[1].text)) if x.kids else x.text for x in rb[i+1].kids] if rb[i+1].kids else rb[i+1].text)
    le=n.get("LocalEffects"); print("LocalEffects",le and (len(le.kids),le.text))
    print("example keys on effect", [k.tag for k in E[0].kids])
    break
print({k:v for k,v in list(fe.items())[:3]})
for g in list(set(fe[k][0] for k in fe))[:3]:
    print(g, json.dumps(gd.effects.get(g) if hasattr(gd,"effects") else None)[:600])

