"""Streaming reader for the one-tag-per-line XML that FileDBReader writes for Anno 117 savegames.

stream(path, want) yields (path_list, node) for every element whose tag path satisfies want(path_list); the
node carries its full subtree. Values are hex strings exactly as FileDBReader writes them.
"""

import re

RE_LEAF = re.compile(r"^<([^>/ ]+)>(.*)</\1>$")
RE_OPEN = re.compile(r"^<([^>/ ]+)>$")
RE_EMPTY = re.compile(r"^<([^>/ ]+) ?/>$")


class Node:
    __slots__ = ("tag", "text", "kids")

    def __init__(self, tag, text=None):
        self.tag = tag
        self.text = text
        self.kids = []

    def get(self, tag):
        for kid in self.kids:
            if kid.tag == tag:
                return kid
        return None

    def find(self, path):
        node = self
        for part in path.split("/"):
            node = node.get(part) if node is not None else None
        return node


def stream(fname, want):
    """Yield (path, node) for each outermost element accepted by want(path) once it is closed."""
    stack = []
    path = []
    cap_root = None
    with open(fname, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            if text.startswith("</"):
                node = stack.pop()
                path.pop()
                if node is cap_root:
                    cap_root = None
                    yield list(path), node
                continue
            match = RE_LEAF.match(text)
            if match:
                if cap_root is not None:
                    stack[-1].kids.append(Node(match.group(1), match.group(2)))
                continue
            match = RE_OPEN.match(text)
            if match:
                node = Node(match.group(1))
                if cap_root is not None:
                    stack[-1].kids.append(node)
                stack.append(node)
                path.append(match.group(1))
                if cap_root is None and want(path):
                    cap_root = node
                continue
            match = RE_EMPTY.match(text)
            if match and cap_root is not None:
                stack[-1].kids.append(Node(match.group(1), ""))


def u(hex_text):
    """Unsigned little endian integer from a hex string (empty -> 0)."""
    return int.from_bytes(bytes.fromhex(hex_text), "little") if hex_text else 0


def i32(hex_text):
    """Signed little endian integer from a hex string (empty -> 0)."""
    return int.from_bytes(bytes.fromhex(hex_text), "little", signed=True) if hex_text else 0
