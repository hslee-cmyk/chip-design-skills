"""v58 strict residue grep at 106cd524 (6 plans): every hit with +-260 chars. Decision-table rows (gb 306-431) tagged REC.
Reader classifies manually. Output resid58_out.txt"""
import subprocess, re
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6387"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/plan_v6387_v58/resid58_out.txt"
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim", "oracle-portability"]
KW = [r"범위 15 \(a\)", r"LA-1 범위 15(?! \([b-h]\))", r"gain_target_first", r"g_i\^\(1\)", r"gain_l_bounds", r"u9_value_not_certified", r"A_max 미상", r"격자 폴백",
      r"미룬 결정 \(8\)", r"결정 \(8\)", r"DEC-71 \(4\)\(b\)", r"L 역산 함수", r"역산 함수", r"출발점 L 칸", r"이득 L 하한", r"1회차 원소 미정", r"최선 앵커"]
with open(OUT, "w", encoding="utf-8") as h:
    for f in FILES:
        t = subprocess.run(["git", "-C", W, "show", f"106cd524:docs/01-plan/features/{f}.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
        for i, l in enumerate(t, 1):
            rec = f.startswith("gain") and 306 <= i <= 431
            for kw in KW:
                for m in re.finditer(kw, l):
                    w = l[max(0, m.start() - 260):m.end() + 260]
                    tag = "REC" if rec else ("MOVED" if ("LA-1a" in w or "O-217" in w or "O-218" in w) else "CAND")
                    h.write(f"[{tag}] [{f}:{i}] <{kw}> ...{w}...\n\n")
print("ok")
