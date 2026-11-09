"""v52 keyword-in-context over c19c4f17 plan files. usage: kw.py OUTNAME CTX kw1 [kw2 ...]"""
import subprocess, sys, re
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-01/plan_v6386_v52/"
REV = "c19c4f17"
files = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim", "oracle-portability"]
out, ctx, kws = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
with open(D + out, "w", encoding="utf-8") as f:
    for name in files:
        t = subprocess.run(["git", "-C", W, "show", f"{REV}:docs/01-plan/features/{name}.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
        for i, line in enumerate(t, 1):
            for kw in kws:
                for m in re.finditer(re.escape(kw), line):
                    a, b = max(0, m.start() - ctx), min(len(line), m.end() + ctx)
                    f.write(f"[{name}:{i} @{m.start()} kw={kw}] ...{line[a:b]}...\n")
print("ok")
