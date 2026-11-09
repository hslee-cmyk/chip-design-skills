"""v52 strict stale classification (same rule as v51 stale_strict.py) at ef911010 and c19c4f17, plus offset-strategy.
C hits (no record marker, no negation word within +-90 chars) are written for c19c4f17; hits whose 120-char
context also exists at ef911010 are tagged OLD (carried over), else NEW (introduced or changed by c19c4f17)."""
import subprocess, re
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-01/plan_v6386_v52/"
FILES = ["gain-budget-gmid-sizing", "graph-consumption", "headroom-chain", "offset-trim", "oracle-portability", "offset-strategy"]
KW = [r"dc_conduction_floor", r"dc_off_current", r"\+ ?tol_VDsat", r"VDsat \+ tol", r"VDSAT \+ tol", r"− ?tol_VDsat", r"\(gm/ID\)·tol_V",
      r"I_off ≤", r"I_off >", r"ε·ID", r"반전 수준 하한", r"g = s[^|]{0,60}꺼짐", r"floor", r"dc_window_def", r"stage2_judgment",
      r"잡음 수준", r"\[0, I_off\]", r"단조성 구간", r"gain_ss_db", r"2단계", r"둘째 단계", r"\bR0\b", r"전도 여유", r"전도 행",
      r"off_current_A", r"V_on", r"off 유지 경계", r"\bU-69\b", r"\bP-7\b", r"_peak_floor", r"\|ID\| ≤ tol_I", r"선언 영역 대조", r"꺼짐 판정",
      r"\+tol", r"두 단계", r"확정 지목", r"confirmed_range"]
REC = re.compile(r"\[정정됨|결정 기록\]|\[대체됨|\[철회|\[삭제")
NEG = re.compile(r"옛|삭제|대체|철회|대상 소멸|기각|지운|두지 않|쓰지 않|않는다|없음|폐기|소멸|정정|읽기 0|호출 0|하지 않")

def hits(rev):
    res = []; summ = {}
    for f in FILES:
        txt = subprocess.run(["git", "-C", W, "show", f"{rev}:docs/01-plan/features/{f}.plan.md"], capture_output=True, check=True).stdout.decode("utf-8")
        for i, ln in enumerate(txt.split("\n"), 1):
            rec = bool(REC.search(ln))
            for kw in KW:
                for m in re.finditer(kw, ln):
                    s, e = m.start(), m.end()
                    win = ln[max(0, s-90):e+90]
                    cls = "R" if rec else ("N" if NEG.search(win) else "C")
                    summ.setdefault((f, kw), {"R": 0, "N": 0, "C": 0})[cls] += 1
                    if cls == "C":
                        res.append((f, i, kw, ln[max(0, s-60):e+60], ln[max(0, s-300):e+300]))
    return res, summ

old, so = hits("ef911010")
new, sn = hits("c19c4f17")
oldctx = {(f, kw, c) for f, i, kw, c, _ in old}
with open(D + "stale52_out.txt", "w", encoding="utf-8") as fh:
    for f, i, kw, c, big in new:
        tag = "OLD" if (f, kw, c) in oldctx else "NEW"
        fh.write(f"[{tag}] [{f}:{i}] <{kw}> ...{big}...\n")
with open(D + "stale52_summary.txt", "w", encoding="utf-8") as fh:
    keys = sorted(set(so) | set(sn))
    for k in keys:
        a = so.get(k, {"R": 0, "N": 0, "C": 0}); b = sn.get(k, {"R": 0, "N": 0, "C": 0})
        fh.write(f"{k[0]}\t{k[1]}\tef: R={a['R']} N={a['N']} C={a['C']}\tc19: R={b['R']} N={b['N']} C={b['C']}\n")
print(len(old), len(new), sum(1 for f, i, kw, c, _ in new if (f, kw, c) not in oldctx))
