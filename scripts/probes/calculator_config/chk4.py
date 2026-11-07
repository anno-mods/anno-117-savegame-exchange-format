from common import *
raw = open(OLD, "rb").read()
print(raw[:60], raw.count(b"\r\n"), raw.count(b"\n"), raw[-20:])
txt = raw.decode("utf-8")
print("nonascii", sum(1 for ch in txt if ord(ch) > 127), "backslash-u", txt.count("\\u"))
d = json.loads(txt)

def js(o, indent=4):
    return json.dumps(o, indent=indent, ensure_ascii=False)

# round trip test
out = {}
for k, v in d.items():
    out[k] = v
re1 = js(out)
print("outer identical", re1 == txt, len(re1), len(txt))
# inner
bad = []
for k, v in d.items():
    if isinstance(v, str) and v[:1] in "{[":
        try:
            o = json.loads(v)
        except Exception:
            continue
        for ind in (4, None):
            s = json.dumps(o, indent=ind, ensure_ascii=False) if ind else json.dumps(o, separators=(",", ":"), ensure_ascii=False)
            if s == v:
                break
        else:
            bad.append(k)
        if ind != 4:
            print("inner style", k, "compact" if ind is None else ind)
print("inner roundtrip failures", bad)
