import json
v = json.load(open(r'C:\dev\Anno-117-Planner\paxplanner\data\game\volcano.json', encoding='utf-8'))
for c in v:
    print({k: (x if not isinstance(x, (list, dict)) else '...') for k, x in c.items()})
    print('effects', c['effects'])
    print('lode', c.get('lode'))
s = json.load(open(r'C:\dev\Anno-117-Planner\paxplanner\data\game\seasons.json', encoding='utf-8'))
for c in s:
    print({k: (x if not isinstance(x, (list, dict)) else '...') for k, x in c.items()})
    print('unlocks', c.get('unlocks'))
    for se in c['seasons']: print(se)
t = json.load(open(r'C:\dev\Anno-117-Planner\paxplanner\data\game\techs.json', encoding='utf-8'))
plan = json.load(open('../marcia69.v5.plan.json'))
tt = {x['guid']: x for x in t['techs']}
print(len(plan['techs']))
names = lambda g: (tt[g].get('loca') or {}).get('english')
for g in v[0]['effects']:
    print(g)
for g in (v[0].get('maximumIncreaseTech'),):
    print('maxInc', g, g in plan['techs'], names(g) if g in tt else None)
for x in t['techs']:
    for e in x.get('effects', []) if isinstance(x.get('effects'), list) else []:
        pass
print(list(tt[plan['techs'][0]].keys()))
