import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import json
G=r'C:/dev/Anno-117-Planner/paxplanner/data/game/'
plan=json.load(open((_SCRATCH + r"\marcia69.v4.plan.json"),encoding='utf-8'))
techs=json.load(open(G+'techs.json',encoding='utf-8'))
print(techs.keys() if isinstance(techs,dict) else type(techs))
T={t['guid']:t for t in techs['techs']}
t=T[37870]; print({k:(v if k not in('loca','description') else '..') for k,v in t.items()})
rel=json.load(open(G+'religion.json',encoding='utf-8'))
print(list(rel.keys()))
print(json.dumps(rel.get('balancing'))[:600])
for p in rel['patrons']:
    print(p['guid'],p['loca']['english'],'wonder',p.get('wonder'),'dom',[ (d['effect']) for d in p.get('dominantEffects',[])],'loc',[l['effect'] for l in p.get('localEffects',[])])
ef=json.load(open(G+'effects.json',encoding='utf-8'))
print(type(ef), list(ef.keys())[:5] if isinstance(ef,dict) else ef[0].keys())
