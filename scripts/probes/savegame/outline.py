import sys, re
# print tag outline up to depth D, collapsing repeated siblings; line-based (FileDB xml is one tag per line)
f, D = sys.argv[1], int(sys.argv[2])
maxlines = int(sys.argv[3]) if len(sys.argv) > 3 else 400
depth = 0
out = 0
seen = {}
for line in open(f, encoding="utf-8", errors="replace"):
    s = line.strip()
    if s.startswith("</"):
        depth -= 1
        continue
    m = re.match(r"<([^>/ ]+)>(.*)</\1>$", s)
    if m:
        if depth <= D:
            print("  " * depth + s[:120]); out += 1
    elif re.match(r"<[^/][^>]*>$", s):
        key = (depth, s)
        if depth <= D:
            print("  " * depth + s); out += 1
        depth += 1
    elif s.endswith("/>"):
        if depth <= D: print("  " * depth + s[:120]); out += 1
    if out > maxlines: break
