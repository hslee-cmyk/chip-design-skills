"""Strict stale-definition classification (validation 51).
Per keyword hit at ef911010: class R = line carries a row/paragraph record marker ('[정정됨' or '결정 기록]' or '[대체됨');
class N = keyword within +-90 chars of a negation/replacement word (옛|삭제|대체|철회|대상 소멸|기각|지운|두지 않|쓰지 않|않는다|없음|폐기|소멸|정정);
class C = neither -> candidate canonical-like residue (read manually).
Output: stale_strict_out.txt (C hits with +-300 chars), stale_strict_summary.txt (counts)."""
import subprocess, re, os
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
OUT = os.path.dirname(os.path.abspath(__file__))
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-trim", "oracle-portability"]
KW = [r"dc_conduction_floor", r"dc_off_current", r"\+ ?tol_VDsat", r"VDsat \+ tol", r"VDSAT \+ tol", r"− ?tol_VDsat", r"\(gm/ID\)·tol_V",
      r"I_off ≤", r"I_off >", r"ε·ID", r"반전 수준 하한", r"g = s[^|]{0,60}꺼짐", r"floor", r"dc_window_def", r"stage2_judgment",
      r"잡음 수준", r"\[0, I_off\]", r"단조성 구간", r"gain_ss_db", r"2단계", r"둘째 단계", r"\bR0\b", r"전도 여유", r"전도 행",
      r"off_current_A", r"V_on", r"off 유지 경계", r"\bU-69\b", r"\bP-7\b", r"_peak_floor", r"\|ID\| ≤ tol_I", r"선언 영역 대조", r"꺼짐 판정"]
REC = re.compile(r"\[정정됨|결정 기록\]|\[대체됨|\[철회|\[삭제")
NEG = re.compile(r"옛|삭제|대체|철회|대상 소멸|기각|지운|두지 않|쓰지 않|않는다|없음|폐기|소멸|정정|읽기 0|호출 0|하지 않")
summ = {}; outc = []
for f in FILES:
    txt = subprocess.run(["git", "-C", W, "show", f"ef911010:docs/01-plan/features/{f}.plan.md"], capture_output=True, check=True).stdout.decode("utf-8")
    for i, ln in enumerate(txt.split("\n"), 1):
        rec = bool(REC.search(ln))
        for kw in KW:
            for m in re.finditer(kw, ln):
                s, e = m.start(), m.end()
                win = ln[max(0, s-90):e+90]
                cls = "R" if rec else ("N" if NEG.search(win) else "C")
                summ.setdefault((f, kw), {"R": 0, "N": 0, "C": 0})[cls] += 1
                if cls == "C":
                    outc.append(f"[{f}:{i}] <{kw}> ...{ln[max(0,s-300):e+300]}...")
with open(os.path.join(OUT, "stale_strict_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(outc))
with open(os.path.join(OUT, "stale_strict_summary.txt"), "w", encoding="utf-8") as fh:
    for (f, kw), d in sorted(summ.items()):
        fh.write(f"{f}\t{kw}\tR={d['R']}\tN={d['N']}\tC={d['C']}\n")
print(len(outc), "C hits")
