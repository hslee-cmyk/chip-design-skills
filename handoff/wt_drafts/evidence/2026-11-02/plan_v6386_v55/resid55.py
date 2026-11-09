"""v55 strict residue grep at fc27ea69: places that still attribute LA-1a-moved items to LA-1.
Class: OK if the 300-char window mentions LA-1a or O-214 or '옛'; else CAND (read manually)."""
import subprocess, re
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-02/plan_v6386_v55/resid55_out.txt"
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim", "oracle-portability"]
KW = [r"LA-1 범위 6", r"범위 15 \(d\)", r"범위 6\(P4\)", r"범위 6 P4", r"완료 조건 9 \(e\)", r"10 \(g\)", r"P4 toy", r"sf 봉인 재현",
      r"R6 블록[^|]{0,40}card LA-1(?!a)", r"card LA-1(?!a)[^|]{0,40}R6", r"layer0_start", r"_halton_probe", r"centre_start", r"_box_centre",
      r"R7 (matching·잡음 )?가드[^|]{0,60}LA-1(?!a)", r"DEC-71 \(4\)\(b\)", r"L 역산", r"출발 회귀", r"R-a", r"R6 창", r"LA-1 때 writer"]
out = []; cnt = {}
for f in FILES:
    t = subprocess.run(["git", "-C", W, "show", f"fc27ea69:docs/01-plan/features/{f}.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
    for i, l in enumerate(t, 1):
        for kw in KW:
            for m in re.finditer(kw, l):
                w = l[max(0, m.start() - 300):m.end() + 300]
                ok = ("LA-1a" in w) or ("O-214" in w) or ("옛" in l[max(0, m.start() - 60):m.start()])
                c = "OK" if ok else "CAND"
                cnt[(f, kw, c)] = cnt.get((f, kw, c), 0) + 1
                if c == "CAND":
                    out.append(f"[{f}:{i}] <{kw}> ...{l[max(0, m.start() - 250):m.end() + 250]}...")
with open(OUT, "w", encoding="utf-8") as h:
    for k, v in sorted(cnt.items()):
        h.write(f"{k[0]}\t{k[1]}\t{k[2]}={v}\n")
    h.write("\n" + "\n".join(out) + "\n")
print(len(out))
