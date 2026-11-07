import sys, re, collections
f = sys.argv[1]; D = int(sys.argv[2]); pat = sys.argv[3] if len(sys.argv) > 3 else None
st = []
cnt = collections.Counter()
ex = {}
for line in open(f, encoding="utf-8", errors="replace"):
    s = line.strip()
    if s.startswith("</"):
        if st: st.pop()
        continue
    m = re.match(r"<([^>/ ]+)>(.*)</\1>$", s)
    if m:
        p = "/".join(re.sub(r"_\d+$", "_N", x) for x in st[:D]) + "/" + re.sub(r"_\d+$", "_N", m.group(1))
        if len(st) < D: cnt[p] += 1; ex.setdefault(p, m.group(2)[:60])
        continue
    m = re.match(r"<([^>/ ]+)>$", s)
    if m:
        st.append(m.group(1))
        if len(st) <= D:
            p = "/".join(re.sub(r"_\d+$", "_N", x) for x in st)
            cnt[p] += 1
    elif s.endswith("/>"):
        pass
for p, c in sorted(cnt.items()):
    if pat is None or re.search(pat, p):
        print(c, p, ex.get(p, ""))
