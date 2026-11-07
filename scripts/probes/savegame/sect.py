import sys
# usage: sect.py file tag [maxlines] [skip_matches]  -> print lines of first (or nth) <tag>...</tag> section
f, tag = sys.argv[1], sys.argv[2]
mx = int(sys.argv[3]) if len(sys.argv) > 3 else 200
nth = int(sys.argv[4]) if len(sys.argv) > 4 else 0
op, cl = f"<{tag}>", f"</{tag}>"
n = -1; inside = False; depth = 0; out = 0
for line in open(f, encoding="utf-8", errors="replace"):
    s = line.strip()
    if not inside:
        if s == op:
            n += 1
            if n == nth: inside = True; depth = 1; print(s); out += 1
        continue
    if s == op: depth += 1
    if s == cl:
        depth -= 1
        if depth == 0: print(s); break
    print(s[:160]); out += 1
    if out >= mx: print("..."); break
