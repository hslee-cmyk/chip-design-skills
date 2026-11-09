# 원문 대조용: 계획·design·하위 계획의 지정 행/키워드 주변만 출력(읽기 전용).
import re, sys, pathlib
B = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga")
P = B / "chip-design-skills/docs/01-plan/features/gain-budget-gmid-sizing.plan.md"
HC = B / "chip-design-skills/docs/01-plan/features/headroom-chain.plan.md"
GC = B / "chip-design-skills/docs/01-plan/features/graph-consumption.plan.md"
D41 = B / "wt/design-v115/docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md"
files = {"P": P, "HC": HC, "GC": GC, "D41": D41}
# usage: F:line[:start:len] 또는 F/regex/width/max
for a in sys.argv[1:]:
    f = a[:a.index(":")] if ":" in a and "/" not in a.split(":")[0] else a.split("/")[0]
    L = files[f].read_text(encoding="utf-8").split("\n")
    if "/" in a:
        _, rx, w, mx = a.split("/")
        n = 0
        for i, l in enumerate(L, 1):
            for m in re.finditer(rx, l):
                n += 1
                if n > int(mx):
                    break
                print("[%s:%d] %s" % (f, i, l[max(0, m.start() - int(w) // 3):m.start() + int(w)]))
                print("-")
    else:
        parts = a.split(":")
        ln = int(parts[1]); st = int(parts[2]) if len(parts) > 2 else 0; le = int(parts[3]) if len(parts) > 3 else 2500
        print("[%s:%d] %s" % (f, ln, L[ln - 1][st:st + le]))
        print("-")
