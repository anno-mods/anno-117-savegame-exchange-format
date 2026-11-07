import os as _os
_SCRATCH = _os.environ.get("ANNO_SCRATCH", ".")  # folder holding x/, auto3774/, upd/ ... (see scripts/probes/README.md)
import re, subprocess, sys, zlib
from pathlib import Path
S = Path((_SCRATCH + r"\x"))
FDB = r"C:\dev\FileDBReader\bin\Debug\net6.0\FileDBReader.exe"
def dec(p):
    subprocess.run([FDB, "decompress", "-f", p.name, "-y"], cwd=str(p.parent), capture_output=True, text=True)
    return p.with_suffix(".xml")
raw = S / "data_raw.bin"
raw.write_bytes(zlib.decompress((S / "outer" / "data.a7s").read_bytes()))
ox = dec(raw)
print(ox, ox.stat().st_size)
rx = re.compile(r"<BinaryData>([0-9A-Fa-f]+)</BinaryData>")
ing = False
n = 0
for line in open(ox, encoding="utf-8", errors="replace"):
    s = line.strip()
    if "<GameSessions>" in s: ing = True
    elif "</GameSessions>" in s: break
    if ing:
        m = rx.search(s)
        if m:
            p = S / f"session_{n}.bin"
            p.write_bytes(bytes.fromhex(m.group(1)))
            x = dec(p)
            print(x, x.stat().st_size)
            n += 1
