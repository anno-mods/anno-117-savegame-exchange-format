import json
G=r'C:/dev/Anno-117-Planner/paxplanner/data/game/'
ef=json.load(open(G+'effects.json',encoding='utf-8'))
for i in ['183157','155840','156267','157072','159339','166443','99072','68757','107937','145095','145099','155616','27983','43598','43600','82017']:
    e=ef.get(i); 
    if not e: print(i,'NOT in planner effects'); continue
    print(i,{k:(v if k not in('loca','description','lines') else '') for k,v in e.items()} if len(json.dumps(e))<700 else json.dumps({k:e[k] for k in e if k in('sources','scope','duration','name')})[:500])
