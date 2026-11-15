"""Vendor the schema and the conformance fixtures into a consumer repository.

    python scripts/vendor.py --dest <path> [--check]

Copies schema/ and fixtures/ of this checkout into <path> and writes <path>/VERSION
(the git commit of this checkout, plus the nearest tag when there is one).
With --check nothing is written: the script exits 1 when the copy in <path> differs
from this checkout (a missing, extra or changed file) or when VERSION is missing.
The script uses only the standard library.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = ("schema", "fixtures")


def git(*args):
    try:
        out = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True)
    except OSError:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def version_text():
    commit = git("rev-parse", "HEAD") or "uncommitted"
    tag = git("describe", "--tags", "--abbrev=0")
    dirty = " (working tree modified)" if git("status", "--porcelain") else ""
    lines = ["commit: " + commit + dirty]
    if tag:
        lines.append("tag: " + tag)
    return "\n".join(lines) + "\n"


def list_files(base):
    out = set()
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            out.add(os.path.relpath(os.path.join(dirpath, name), base).replace(os.sep, "/"))
    return out


def check(dest):
    problems = []
    if not os.path.exists(os.path.join(dest, "VERSION")):
        problems.append("VERSION missing")
    for part in PARTS:
        src, dst = os.path.join(ROOT, part), os.path.join(dest, part)
        want = list_files(src)
        have = list_files(dst) if os.path.isdir(dst) else set()
        for rel in sorted(want - have):
            problems.append("missing: %s/%s" % (part, rel))
        for rel in sorted(have - want):
            problems.append("extra: %s/%s" % (part, rel))
        for rel in sorted(want & have):
            if not filecmp.cmp(os.path.join(src, rel), os.path.join(dst, rel), shallow=False):
                problems.append("differs: %s/%s" % (part, rel))
    return problems


def copy(dest):
    for part in PARTS:
        dst = os.path.join(dest, part)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(ROOT, part), dst)
    with open(os.path.join(dest, "VERSION"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(version_text())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dest", required=True, help="target directory in the consumer repository")
    ap.add_argument("--check", action="store_true", help="fail when the copy differs; write nothing")
    args = ap.parse_args()
    if args.check:
        problems = check(args.dest)
        for p in problems:
            print(p)
        print("vendored copy matches" if not problems else "vendored copy differs")
        return 1 if problems else 0
    os.makedirs(args.dest, exist_ok=True)
    copy(args.dest)
    print("vendored schema and fixtures into " + args.dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
