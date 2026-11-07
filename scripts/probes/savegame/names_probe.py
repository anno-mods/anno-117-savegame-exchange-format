import os as _os
from pathlib import Path as _Path
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
_CONFIG = str(_Path(__file__).resolve().parents[3] / "data" / "raw" / "calculator_configs" / "Marcia 69.json")
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
SP = _SCRATCH
txt = open(r"C:\dev\asset-extractor\.cache-117\data\base\config\gui\texts_english.xml", encoding="utf-8").read()
tab = {int(a): b for a, b in re.findall(r"<LineId>(-?\d+)</LineId>\s*<Text>([^<]*)</Text>", txt)}
print(len(tab))
ex = json.load(open(SP + r"\x\extract.json"))
calc = json.load(open(_CONFIG, encoding="utf-8"))
names = {}
for n in json.loads(calc["islandNames"]):
    i = json.loads(calc[n])
    names[(i["session"], i.get("gameConnector.islandID"), i.get("gameConnector.areaIndex"))] = n
hit = 0
for a in ex["areas"]:
    h = a["cityNameGuid"]
    v = int.from_bytes(bytes.fromhex(h), "little", signed=True)
    k = a["key"]
    r = tab.get(v)
    c = names.get((a["sessionGuid"], (k >> 6) & 127, k >> 13))
    print(k, v, r, c, r == c, a["cityNameIterator"])
    hit += r == c
print(hit)
