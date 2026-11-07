import json
t = json.load(open(r'C:\dev\Anno-117-Planner\paxplanner\data\game\techs.json', encoding='utf-8'))
plan = json.load(open('../marcia69.v5.plan.json'))
tt = {x['guid']: x for x in t['techs']}
R = set(plan['techs'])
for g in (145068, 148041, 145106, 145107, 145339, 148042, 149297):
    x = tt.get(g)
    print(g, 'in techs' if x else 'NOT TECH', 'RESEARCHED' if g in R else 'no', x and (x['loca']['english'], x['unlocks'], x['effects'], x['repeatable']))
for x in t['techs']:
    for u in x.get('unlocks') or []:
        uid = u if isinstance(u, int) else (u.get('guid') if isinstance(u, dict) else u)
        if uid in (145339, 148042, 149297, 157020):
            print('tech unlocking', uid, x['guid'], x['loca']['english'], 'RESEARCHED' if x['guid'] in R else 'no')
print(json.dumps(tt[145068]['unlocks'])[:300])
# tech whose effects include calculator global effects
