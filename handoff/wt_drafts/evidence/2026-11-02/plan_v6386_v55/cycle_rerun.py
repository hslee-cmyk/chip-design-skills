"""v55 independent rerun of la1a_merge_cycle logic; output to this folder only (author files untouched).
Base graph = icmr4_cand_files/merge_order_cycle.py (REV 65377396 fragment asserts; run_name != __main__ so it writes nothing on success).
Extra checks: LA-1a edges are re-read from fc27ea69 card table rows (LA-1a / LA-1) by fragment assert."""
import runpy, subprocess, sys
BASE = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-01/icmr4_cand_files/merge_order_cycle.py"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-11-02/plan_v6386_v55/cycle_rerun_out.txt"
W = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6386"
g = runpy.run_path(BASE, run_name="v55")
E, find_cycle, anc = g["E"], g["find_cycle"], g["anc"]
txt = subprocess.run(["git", "-C", W, "show", "fc27ea69:docs/01-plan/features/gain-budget-gmid-sizing.plan.md"], capture_output=True).stdout.decode("utf-8").split("\n")
row_a = next(l for l in txt if l.startswith("| LA-1a(층 0 출발점"))
row_l = next(l for l in txt if l.startswith("| LA-1(층 0 손계산 조립"))
pre_a = row_a.split(" | ")[2]
checks = {"cardB": "XRUN-F1 card B", "IT-1+IT-2": "IT-1 + IT-2 통합 병합", "WB-1": "card WB-1", "UB-1": "UB-1 + NL-1",
          "HC-S": "headroom-chain HC-S", "TB-1": "card TB-1", "HC-1": "headroom-chain HC-1 + graph-consumption GC-8"}
log = []
for k, frag in checks.items():
    log.append(f"LA-1a 선행 칸에 '{frag}': {frag in pre_a}")
log.append(f"LA-1a 선행 칸에 'EO-1'이 병합 선행으로: {'SPICE 다리 선행 EO-1만' in pre_a} (SPICE 다리만 표기)")
log.append(f"LA-1 선행 칸에 'card LA-1a': {'card LA-1a' in row_l.split(' | ')[2]}")
cy0 = find_cycle({k: set(v) for k, v in E.items()})
NEW = [(p, "LA-1a") for p in ("cardB", "IT-1+IT-2", "WB-1", "UB-1", "HC-S", "TB-1", "HC-1", "GC-8")]
NEW += [("LA-1a", "LA-1"), ("LA-1", "DE-1"), ("DE-1", "SB-1"), ("LA-1", "OS-2"), ("LA-1", "LA-2")]
for a, b in NEW:
    E[a].add(b)
cy = find_cycle(E)
a1, _ = anc("LA-1a", E)
a2, _ = anc("LA-1", E)
log += [f"기존 순환: {cy0 or '없음'}", f"더한 뒤 순환: {cy or '없음'}",
        f"LA-1a 조상({len(a1)}): {', '.join(sorted(a1))}", f"LA-1 조상({len(a2)}): {', '.join(sorted(a2))}",
        f"LA-1a ⊆ LA-1 조상: {a1 <= a2}", f"LA-1이 LA-1a 조상: {'LA-1' in a1}", f"OP-5 ∈ LA-1a 조상: {'OP-5' in a1}",
        f"EO-1 ∈ LA-1a 조상: {'EO-1' in a1}", f"SF-1 ∈ LA-1a 조상: {'SF-1' in a1}", f"DE-1 ∈ LA-1a 조상: {'DE-1' in a1}"]
open(OUT, "w", encoding="utf-8").write("\n".join(log) + "\n")
print("\n".join(log))
