import os as _os
from pathlib import Path as _Path
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
_CONFIG = str(_Path(__file__).resolve().parents[3] / "data" / "raw" / "calculator_configs" / "Marcia 69.json")
import json,subprocess,collections
G=r'C:/dev/Anno-117-Planner/paxplanner/data/game/'
L=lambda n: json.load(open(G+n+'.json',encoding='utf-8'))
calc=json.loads(subprocess.check_output(['node','-e','global.window={};eval(require("fs").readFileSync("C:/dev/anno-117-calculator/js/params.js","utf8"));console.log(JSON.stringify({e:window.params.effects.map(x=>[x.guid,x.locaText&&x.locaText.english||x.name,x.effectScope,x.source,x.targetsIsAllProduction]),t:window.params.techs}))'],encoding='utf-8'))
ce={e[0]:e for e in calc['e']}
plan=json.load(open((_SCRATCH + r"\marcia69.v4.plan.json"),encoding='utf-8'))
techs=L('techs')['techs']; T={t['guid']:t for t in techs}
rel=L('religion'); P={p['guid']:p for p in rel['patrons']}
# calc techs vs planner
print('== calc techs vs planner plan')
gs=json.load(open(_CONFIG,encoding='utf-8'))
ge=json.loads(gs['globalEffects'])
for t in calc['t']:
    eff=t['effects']
    print(t['guid'],t['locaText']['english'],'rep' if t['isRepeatable'] else '', 'effects',eff,'calc global',[ge.get(str(e)+'.scaling') for e in eff],'| plan has tech',t['guid'] in plan['techs'],'count',plan['tech_counts'].get(str(t['guid'])),'| planner relevantEffects',T.get(t['guid'],{}).get('relevantEffects'))
print('== planner techs with relevantEffects NOT in calc techs, researched in plan')
ct={t['guid'] for t in calc['t']}
n=0
for g in plan['techs']:
    t=T.get(g)
    if t and t.get('relevantEffects') and g not in ct:
        print(g,t['loca']['english'],t['relevantEffects'],[ce.get(e,[0,'NOT IN CALC'])[1] for e in t['relevantEffects']]); n+=1
print(n)
print('== planner techs with relevantEffects, not in calc techs, ALL (count)',sum(1 for t in techs if t.get('relevantEffects') and t['guid'] not in ct))
print('== calc effects by scope/source')
c=collections.Counter((e[2],e[3]) for e in calc['e']); print(c)
print('== calc effects source tech/global scopes not tied to calc techs')
tech_eff={e for t in calc['t'] for e in t['effects']}
for e in calc['e']:
    if e[3]=='tech' and e[0] not in tech_eff: print('tech-source effect without calc tech',e)
# patrons dominant/wonder in calc
for pg,p in P.items():
    print(p['loca']['english'],'wonder',p.get('wonder'),p.get('wonder') in ce,'dom',[d['effect'] in ce for d in p['dominantEffects']],[d['effect'] for d in p['dominantEffects']])
