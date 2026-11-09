"""v58 extra checks at 106cd524: history fragments, E-06 ownership, T_b, N6.39 근거, cycle rerun (base graph REV 65377396 + LA-1a edges re-read from 106cd524), q8 ngcc facts."""
import re, subprocess, runpy
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6387"
D = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-03/plan_v6387_v58/"
E = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/"
s = lambda r, p: subprocess.run(["git", "-C", W, "show", f"{r}:{p}"], capture_output=True).stdout.decode("utf-8")
g = s("106cd524", "docs/01-plan/features/gain-budget-gmid-sizing.plan.md").split("\n")
h = s("106cd524", "docs/01-plan/features/gain-budget-gmid-sizing.history.md")
gh = s("106cd524", "docs/01-plan/features/graph-consumption.history.md")
o = open(D + "checks_out.txt", "w", encoding="utf-8")
for frag in ("Status 줄(v6.38.6 승인 판)", "v6.38.7 첫째 커밋", "출발점 L 칸 = DEC-71 (4)(b) 함수 READS", "(i) 출발점 L 칸 = 이득 요구 역산**: DEC-71 (4)(b) 역산 함수 하나", "L 역산 toy -- 이득 요구가 최소 L bin", "(a) 이득 L 하한 블록 목표 = found_db 비례 g_i^(1) 필드 READS"):
    o.write(f"history has <{frag}>: {frag in h}\n")
o.write(f"GC history 0.14.7 row: {'0.14.7' in gh}\n\n")
for i, l in enumerate(g, 1):
    for m in re.finditer(r"E-06", l):
        o.write(f"[E-06 P:{i}] ...{l[max(0,m.start()-160):m.end()+200]}...\n")
o.write("\n")
for i, l in enumerate(g, 1):
    if "T_b" in l:
        m = l.find("T_b"); o.write(f"[T_b P:{i}] ...{l[max(0,m-120):m+140]}...\n")
o.write("\n")
o.write(f"P2506: {g[2505][:900]}\n\n")
o.write(f"P2516: {g[2515][:500]}\n\n")
l = g[2007]; o.write(f"P2008?: {l[:200]}\n")
for i in range(2000, 2020):
    if g[i-1].startswith("10.") or "(g) N6.35" in g[i-1]:
        j = g[i-1].find("(g)"); o.write(f"P{i} (g): {g[i-1][j:j+260]}\n")
l = g[1973]; j = l.find("(g)"); o.write(f"P1974 (g): {l[j:j+500]}\n\n")
# cycle
base = runpy.run_path(D + "merge_order_cycle_copy.py", run_name="v58")
G, fc, anc = base["E"], base["find_cycle"], base["anc"]
row_a = next(x for x in g if x.startswith("| LA-1a(층 0 출발점")); row_l = next(x for x in g if x.startswith("| LA-1(층 0 손계산 조립"))
pre = row_a.split(" | ")[2]
for frag in ("XRUN-F1 card B", "IT-1 + IT-2 통합 병합", "card WB-1", "UB-1 + NL-1", "headroom-chain HC-S", "card TB-1", "headroom-chain HC-1 + graph-consumption GC-8", "EO-1 코드 의존"):
    o.write(f"LA-1a 선행 칸 <{frag}>: {frag in pre}\n")
o.write(f"LA-1 선행 칸 card LA-1a: {'card LA-1a' in row_l.split(' | ')[2]}\n")
for a, b in [(p, "LA-1a") for p in ("cardB", "IT-1+IT-2", "WB-1", "UB-1", "HC-S", "TB-1", "HC-1", "GC-8")] + [("LA-1a", "LA-1"), ("LA-1", "DE-1"), ("DE-1", "SB-1"), ("LA-1", "OS-2"), ("LA-1", "LA-2")]:
    G[a].add(b)
a1, _ = anc("LA-1a", G); a2, _ = anc("LA-1", G)
o.write(f"cycle: {fc(G) or '없음'}; LA-1a anc {len(a1)}, LA-1 anc {len(a2)}, subset {a1 <= a2}; UB-1 in LA-1 anc before: {'UB-1' in a2}\n\n")
q = open(E + "2026-11-02/q8_target_gain_candidates.md", encoding="utf-8").read().split("\n")
for i, l in enumerate(q, 1):
    if re.search(r"ngcc|nmcnr", l) and re.search(r"found_db|L 칸|108\.6|정의 불능|원소", l):
        o.write(f"[q8:{i}] {l[:420]}\n")
o.close(); print("ok")
