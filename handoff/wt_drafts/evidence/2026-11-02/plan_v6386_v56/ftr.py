"""v56: '기능 기준'/'증분 DC 이득' occurrences at 84e4ec99 not near O-215/선택/상대/옛 markers (decision rows gb 306-440 skipped)."""
import re, subprocess
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-02/plan_v6386_v56/ftr_out.txt"
o = open(OUT, "w", encoding="utf-8")
for name in ("gain-budget-gmid-sizing", "oracle-portability", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim"):
    t = subprocess.run(["git", "-C", W, "show", f"84e4ec99:docs/01-plan/features/{name}.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
    for i, l in enumerate(t, 1):
        if name.startswith("gain") and 306 <= i <= 440:
            continue
        for m in re.finditer(r"기능 기준|증분 DC 이득", l):
            w = l[max(0, m.start() - 200):m.end() + 200]
            if any(k in w for k in ("O-215", "선택", "상대", "옛")):
                continue
            o.write(f"{name}:{i} ...{w}\n\n")
o.close()
print("ok")
