import json, pickle
p = json.load(open('params.json', encoding='utf-8'))
plan = json.load(open('../marcia69.v5.plan.json'))
techs = set(plan['techs'])
cnt = plan['tech_counts']
eff = {e['guid']: e for e in p['effects']}
print("TECHS in params")
for t in p['techs']:
    print(t['guid'], t['name'], t['effects'], 'rep' if t.get('isRepeatable') else '', 'RESEARCHED' if t['guid'] in techs else '-', cnt.get(str(t['guid'])))
print("META effects")
for e in p['effects']:
    if e['effectScope'].endswith('Meta') or e['effectScope'] == 'ModuleOwner':
        print(e['guid'], e['effectScope'], e.get('source'), e['name'])
print("session effects")
for e in p['effects']:
    if e['effectScope'] == 'ObjectsInSession':
        print(e['guid'], e['name'], e.get('source'), e.get('dlcUnlocks'))
for s in p['sessions']:
    print(s['guid'], s['name'], s.get('effects'))
print("plan tech_counts keys in params techs?")
for k, v in cnt.items():
    print(k, v, int(k) in {t['guid'] for t in p['techs']})
print("volcano", plan['volcano'], plan['seasons'])
