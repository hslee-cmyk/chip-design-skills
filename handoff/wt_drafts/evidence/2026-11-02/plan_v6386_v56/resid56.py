"""v56 residue grep at 84e4ec99 (6 plans). CAND = window (+-300) lacks O-215 / 영역 행 / 선택 / 옛 / 철회 / 대상 소멸 markers (ICMR set),
or lacks LA-1a/O-214/M55-2/유지 markers (start-path set). Decision-table rows (gb 306-440) tagged REC."""
import subprocess, re
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-02/plan_v6386_v56/resid56_out.txt"
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-strategy", "offset-trim", "oracle-portability"]
ICMR = [r"기능 기준", r"4/13", r"ICMR[^|]{0,60}정의 불능", r"정의 불능[^|]{0,40}ICMR", r"점별 증분 DC 이득", r"gain_ss_db[^|]{0,40}ICMR", r"O-206", r"O-211"]
ICMR_OK = ("O-215", "영역 행", "선택", "옛", "철회", "대상 소멸", "상대 항", "상대 저하")
START = [r"_repair", r"layer0_start", r"최소형", r"층 0 점 없음 경로", r"성능 판정 보류", r"진단 비지배"]
START_OK = ("LA-1a", "O-214", "M55-2", "유지", "옛", "대상 소멸")
out = []; cnt = {}
for f in FILES:
    t = subprocess.run(["git", "-C", W, "show", f"84e4ec99:docs/01-plan/features/{f}.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
    for i, l in enumerate(t, 1):
        rec = f.startswith("gain") and 306 <= i <= 440
        for group, kws, oks in (("ICMR", ICMR, ICMR_OK), ("START", START, START_OK)):
            for kw in kws:
                for m in re.finditer(kw, l):
                    w = l[max(0, m.start() - 300):m.end() + 300]
                    c = "REC" if rec else ("OK" if any(o in w for o in oks) else "CAND")
                    cnt[(f, group, kw, c)] = cnt.get((f, group, kw, c), 0) + 1
                    if c == "CAND":
                        out.append(f"[{f}:{i}] <{group}:{kw}> ...{l[max(0, m.start() - 220):m.end() + 220]}...")
with open(OUT, "w", encoding="utf-8") as h:
    for k, v in sorted(cnt.items()):
        h.write("\t".join(k) + f"={v}\n")
    h.write("\n" + "\n\n".join(out) + "\n")
print(len(out))
