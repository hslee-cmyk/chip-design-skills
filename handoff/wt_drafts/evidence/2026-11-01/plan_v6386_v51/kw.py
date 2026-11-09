"""Keyword hits with context in plan files at ef911010 (validation 51). usage: kw.py <ctx> <kw1> [kw2 ...]  (regex)"""
import subprocess, sys, re, os
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = os.path.dirname(os.path.abspath(__file__))
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-trim", "oracle-portability"]
ctx = int(sys.argv[1]); kws = sys.argv[2:]
tag = re.sub(r"[^A-Za-z0-9_]+", "_", "_".join(kws))[:60]
res = []
for f in FILES:
    txt = subprocess.run(["git", "-C", W, "show", f"ef911010:docs/01-plan/features/{f}.plan.md"], capture_output=True, check=True).stdout.decode("utf-8")
    lines = txt.split("\n")
    for kw in kws:
        rx = re.compile(kw)
        for i, ln in enumerate(lines, 1):
            for m in rx.finditer(ln):
                s = max(0, m.start() - ctx); e = min(len(ln), m.end() + ctx)
                res.append(f"[{f}:{i}] <{kw}> ...{ln[s:e]}...")
with open(os.path.join(OUT, f"kw_{tag}.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(res))
print(len(res), "hits ->", f"kw_{tag}.txt")
