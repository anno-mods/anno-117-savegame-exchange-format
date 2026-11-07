import re, sys, json
sys.stdout.reconfigure(encoding="utf-8")
D = r"C:\dev\Anno-117-Planner\paxplanner\data\game"
for f in ("buffs.json", "effects.json", "techs.json", "buildings.json", "season_wiki.json"):
    txt = open(D + "\\" + f, encoding="utf-8").read()
    for m in list(re.finditer(r"[Ii]rrigat", txt))[:12]:
        a = max(0, m.start() - 140); b = min(len(txt), m.end() + 140)
        print(f, "...", txt[a:b].replace("\n", " "))
    print("-----")
