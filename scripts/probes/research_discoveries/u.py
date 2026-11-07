import os as _os
from pathlib import Path as _Path
_CONFIG = str(_Path(__file__).resolve().parents[3] / "data" / "raw" / "calculator_configs" / "Marcia 69.json")
import json
G='C:/dev/Anno-117-Planner/paxplanner/data/game/'
rel=json.load(open(G+'religion.json',encoding='utf-8')); P={p['guid']:p for p in rel['patrons']}
gs=json.load(open(_CONFIG,encoding='utf-8'))
for n in json.loads(gs['islandNames'])+['All Islands']:
    o=json.loads(gs[n]) if isinstance(gs[n],str) else gs[n]
    pt=o.get('selectedPatron')
    if not pt: continue
    pt=int(pt); dev=float(o.get('devotion',0))
    for le in P[pt]['localEffects']:
        sc=0
        for m in le['milestones']:
            if dev>=m['devotion']: sc=m['buffScaling']
        c=o.get('island.effect.%d.scaling'%le['effect'])
        print(n,P[pt]['loca']['english'],dev,le['effect'],'planner',sc,'calc',c, 'OK' if str(c)==str(sc) or (c is None and sc==0) else 'DIFF')
