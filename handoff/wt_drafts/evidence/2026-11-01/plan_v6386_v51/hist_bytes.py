"""History lossless check a4d87f1a -> ef911010 (validation 51): byte-line opcodes must be insert-only; old bytes == new bytes minus inserted lines.
Also per-commit numstat for history files. Output: hist_bytes_out.txt"""
import subprocess, difflib, os, hashlib
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = os.path.dirname(os.path.abspath(__file__))
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-trim", "oracle-portability"]
def show(rev, p):
    return subprocess.run(["git", "-C", W, "show", f"{rev}:{p}"], capture_output=True, check=True).stdout
res = []
for f in FILES:
    p = f"docs/01-plan/features/{f}.history.md"
    a = show("a4d87f1a", p); b = show("ef911010", p)
    al = a.split(b"\n"); bl = b.split(b"\n")
    sm = difflib.SequenceMatcher(None, al, bl, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
    kinds = sorted(set(o[0] for o in ops))
    kept = []
    for t, i1, i2, j1, j2 in sm.get_opcodes():
        if t == "equal":
            kept.extend(bl[j1:j2])
    recon = b"\n".join(kept)
    res.append(f"{f}: old {len(a)}B {hashlib.sha256(a).hexdigest()[:12]} new {len(b)}B; ops={kinds} n={len(ops)}; old==new-minus-inserts: {recon == a}; crlf old {a.count(b'\\r\\n')} new {b.count(b'\\r\\n')}")
for c in ["b17957d3", "fe53f211", "ef911010"]:
    out = subprocess.run(["git", "-C", W, "diff", "--numstat", f"{c}~1", c, "--", "docs/01-plan/features/"], capture_output=True, check=True).stdout.decode()
    res.append(f"--- numstat {c}~1..{c}\n{out}")
with open(os.path.join(OUT, "hist_bytes_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(res))
