import re, sys
RE_LEAF = re.compile(r"^<([^>/ ]+)>(.*)</\1>$")
RE_OPEN = re.compile(r"^<([^>/ ]+)>$")
RE_EMPTY = re.compile(r"^<([^>/ ]+) ?/>$")


class N:
    __slots__ = ("tag", "text", "kids")

    def __init__(self, tag, text=None):
        self.tag = tag; self.text = text; self.kids = []

    def get(self, tag):
        for k in self.kids:
            if k.tag == tag: return k
        return None

    def all(self, tag):
        return [k for k in self.kids if k.tag == tag]

    def find(self, path):
        n = self
        for p in path.split("/"):
            n = n.get(p) if n else None
        return n


def stream(fname, want):
    """Yield (path_list, N) for every element whose tag path (list) satisfies want(path) at its close, with full subtree.
    want is called on open with the path list; returns True to capture this subtree (not nested)."""
    stack = []  # (N, capturing)
    path = []
    cap_root = None
    for line in open(fname, encoding="utf-8", errors="replace"):
        s = line.strip()
        if not s: continue
        if s.startswith("</"):
            n = stack.pop(); path.pop()
            if n is cap_root:
                cap_root = None
                yield (list(path), n)
            continue
        m = RE_LEAF.match(s)
        if m:
            if cap_root is not None:
                stack[-1].kids.append(N(m.group(1), m.group(2)))
            continue
        m = RE_OPEN.match(s)
        if m:
            n = N(m.group(1))
            if cap_root is not None:
                stack[-1].kids.append(n)
            stack.append(n); path.append(m.group(1))
            if cap_root is None and want(path):
                cap_root = n
            continue
        m = RE_EMPTY.match(s)
        if m and cap_root is not None:
            stack[-1].kids.append(N(m.group(1), ""))


def show(n, depth=0, maxdepth=6, out=None, maxkids=6):
    pad = "  " * depth
    if n.text is not None:
        print(f"{pad}{n.tag} = {n.text[:90]}")
        return
    print(f"{pad}{n.tag}  [{len(n.kids)}]")
    if depth >= maxdepth: return
    seen = 0
    for k in n.kids:
        if seen >= maxkids and k.tag == "None":
            continue
        show(k, depth + 1, maxdepth, out, maxkids)
        seen += 1
    if seen < len(n.kids) and n.kids and n.kids[0].tag == "None":
        print(f"{pad}  ... {len(n.kids)} entries")
