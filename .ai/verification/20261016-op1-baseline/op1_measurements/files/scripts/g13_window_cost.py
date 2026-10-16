"""G-13: per-window cost of the C10 closed-loop transient in the baseline (this machine, sequential, no other ngspice load).
For every sim.json with ac.stability.transient: windows_run, windows_planned, early stop or not; wall = mtime(stab log/txt) - mtime(stab.cir)
(same method as oracle_config 'first value' -- file time difference). Cost model for an adapter without tran_early_stop:
 (가) one full run to tstop: K_planned * c ; (나) rerun per window j=1..K with tstop extended: c*K(K+1)/2 (upper bound K = planned,
 or K = windows the early-stop run used when the verdict comes at that window)."""
import glob, json, os
B = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/baseline"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_scratch_op1/results/g13_window_cost.json"
rows = []
for p in glob.glob(B + "/**/*.sim.json", recursive=True):
    try:
        s = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    ac = s.get("ac")
    if not isinstance(ac, dict):
        continue
    st = ac.get("stability") or {}
    t = st.get("transient") if isinstance(st, dict) else None
    if not isinstance(t, dict) or not t.get("netlist"):
        continue
    d = os.path.dirname(p)
    cir = os.path.join(d, t["netlist"])
    ends = [x for x in (os.path.join(d, t.get("file") or ""), os.path.splitext(cir)[0] + ".log") if os.path.isfile(x)]
    if not os.path.isfile(cir) or not ends:
        continue
    wall = max(os.path.getmtime(x) for x in ends) - os.path.getmtime(cir)
    plan = t.get("plan") or {}
    k_run, k_plan = t.get("windows_run"), plan.get("windows_planned") or plan.get("windows")
    if not k_run:
        continue
    c = wall / k_run
    rows.append({"file": os.path.relpath(p, B), "status": t.get("status"), "windows_run": k_run, "windows_planned": k_plan,
                 "early_stopped": bool(k_plan and k_run < k_plan), "wall_s": wall, "c_s_per_window": c,
                 "cost_now_s": wall, "cost_A_full_s": c * (k_plan or k_run),
                 "cost_B_rerun_to_verdict_s": c * k_run * (k_run + 1) / 2, "cost_B_rerun_to_plan_s": c * (k_plan or k_run) * ((k_plan or k_run) + 1) / 2})
rows.sort(key=lambda r: -r["c_s_per_window"])
agg = {"n": len(rows), "n_early_stopped": sum(r["early_stopped"] for r in rows),
       "c_max": max((r["c_s_per_window"] for r in rows), default=None),
       "sum_now_s": sum(r["cost_now_s"] for r in rows), "sum_A_s": sum(r["cost_A_full_s"] for r in rows),
       "sum_B_verdict_s": sum(r["cost_B_rerun_to_verdict_s"] for r in rows), "sum_B_plan_s": sum(r["cost_B_rerun_to_plan_s"] for r in rows)}
json.dump({"aggregate": agg, "rows": rows}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(agg)
for r in rows[:12]:
    print(round(r["c_s_per_window"], 3), r["status"], r["windows_run"], r["windows_planned"], round(r["wall_s"], 2), r["file"])
