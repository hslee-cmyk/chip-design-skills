# O-268/O-269 집계 (o268_measure.jsonl 만 읽는다 -- 엔진 호출 0). 결과 = o268_summary.json (회로별 행 + n/N).
import json, pathlib

HERE = pathlib.Path(__file__).parent
rows = [json.loads(l) for l in (HERE / "o268_measure.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
latest = {}
for r in rows:
    latest[r["circuit"]] = r          # 같은 회로가 여러 번이면 마지막 줄


def inside(v, lo, hi):
    if v is None or lo is None or hi is None:
        return None
    return lo <= v <= hi


out = []
for c in sorted(latest):
    r = latest[c]; s = r["spec"]; e = r.get("engine") or {}
    sup = s["supplies_v"]; mid = s["rail_mid_v"]
    mode = s["input_dc_mode"]
    declared = None
    if mode.startswith("net:"):
        declared = sup.get(mode[4:])
    elif mode.startswith("value:"):
        declared = float(mode[6:])
    fb_elems = bool(s["feedback_elements"])
    fb_empty = s["feedback_mode"].startswith("empty_list")
    measured = e.get("phase") == "done"
    dirs = {n: p for n, p in (e.get("ports") or {}).items() if p.get("direction")}
    ins = [n for n, p in dirs.items() if p["direction"] == "input"]
    icm = e.get("icm_config") or {}
    w_icm = (icm.get("vcm_lo"), icm.get("vcm_hi"))
    kw = e.get("kernel_w4_window") or {}
    roots = [n for n in ins if n in kw]
    w_k = (min(kw[n]["lo"] for n in roots), max(kw[n]["hi"] for n in roots)) if roots else (None, None)
    lo_rail, hi_rail = (min(sup.values()), max(sup.values())) if sup else (None, None)

    def branch(feedback_rule):
        if declared is not None:
            return "선언", declared
        if feedback_rule:
            return "피드백 -> 출력 스윙 중심", None          # 정의 자리 없음(card DE-1 미구현)
        return "레일 중앙값", mid

    brA = branch(fb_elems)                   # 해석 A: feedback.elements 비지 않음만 피드백 구성
    brB = branch(fb_elems or fb_empty)       # 해석 B: elements [] (beta=1 규칙)도 피드백 구성
    row = {
        "circuit": c, "input_dc_mode": mode, "declared_v": declared, "feedback_mode": s["feedback_mode"],
        "feedback_elements": s["feedback_elements"], "swing_icmr_constraints": s["swing_icmr_constraints"],
        "spec_keys_swing_icmr": s["spec_keys_swing_icmr"],
        "rail_mid_v": mid, "rails": [lo_rail, hi_rail], "measured": measured,
        "unmeasured_reason": None if measured else (r.get("unmeasured") or e.get("phase") or "no_engine") ,
        "engine_error_tail": (e.get("error") or "")[-400:] or None,
        "start_status": e.get("start_status"), "bounds_used": e.get("bounds_used"),
        "v_cm_start": e.get("v_cm_start"), "v_out_start": e.get("v_out_start"),
        "input_ports": {n: dirs[n]["role"] for n in ins}, "input_writers": e.get("input_writers"),
        "kernel_w4_window_inputs": {n: kw[n] for n in roots}, "icm_config": icm or None,
        "ls_swing_reference": e.get("ls_swing_report_reference"),
        "out_swing_window_plan_def": "정의 자리 없음(card DE-1 착수 전, master 생산자 0)",
        "mid_in_icm_window": inside(mid, *w_icm) if measured else None,
        "mid_in_kernel_w4": inside(mid, *w_k) if measured else None,
        "mid_in_rails": inside(mid, lo_rail, hi_rail),
        "declared_in_icm_window": inside(declared, *w_icm) if (measured and declared is not None) else None,
        "start_vcm_eq_mid": (abs(e["v_cm_start"] - mid) < 1e-9) if (measured and e.get("v_cm_start") is not None and mid is not None) else None,
        "branch_A": brA[0], "value_A": brA[1], "value_A_in_icm": inside(brA[1], *w_icm) if measured else None,
        "branch_B": brB[0], "value_B": brB[1], "value_B_in_icm": inside(brB[1], *w_icm) if measured else None,
        "peak_rss_gb": r.get("peak_rss_gb"), "wall_s": r.get("wall_s"), "min_free_gb": r.get("min_free_gb"),
    }
    out.append(row)


def count(key, val):
    return sum(1 for x in out if x[key] == val)


N = len(out)
agg = {
    "N": N,
    "measured": count("measured", True),
    "input_dc_declared": sum(1 for x in out if x["declared_v"] is not None),
    "feedback_elements_declared": sum(1 for x in out if x["feedback_elements"]),
    "feedback_empty_list": sum(1 for x in out if x["feedback_mode"].startswith("empty_list")),
    "feedback_pending_or_missing": sum(1 for x in out if not x["feedback_mode"].startswith(("empty_list", "declared"))),
    "out_swing_centre_defined": 0,
    "mid_in_icm_window": count("mid_in_icm_window", True), "mid_out_icm_window": count("mid_in_icm_window", False),
    "mid_in_kernel_w4": count("mid_in_kernel_w4", True),
    "start_vcm_eq_mid": count("start_vcm_eq_mid", True),
    "A": {b: sum(1 for x in out if x["branch_A"] == b) for b in ("선언", "피드백 -> 출력 스윙 중심", "레일 중앙값")},
    "A_value_in_icm": count("value_A_in_icm", True), "A_value_out_icm": count("value_A_in_icm", False),
    "B": {b: sum(1 for x in out if x["branch_B"] == b) for b in ("선언", "피드백 -> 출력 스윙 중심", "레일 중앙값")},
    "B_value_in_icm": count("value_B_in_icm", True), "B_value_out_icm": count("value_B_in_icm", False),
}
(HERE / "o268_summary.json").write_text(json.dumps({"agg": agg, "rows": out}, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(agg, ensure_ascii=False))
for x in out:
    print(x["circuit"], x["input_dc_mode"], x["feedback_mode"], "meas" if x["measured"] else x["unmeasured_reason"],
          "vcm0", x["v_cm_start"], "icm", (x["icm_config"] or {}).get("vcm_lo"), (x["icm_config"] or {}).get("vcm_hi"),
          "kw", x["kernel_w4_window_inputs"], "A", x["branch_A"], x["value_A"], x["value_A_in_icm"], "B", x["branch_B"], x["value_B"], x["value_B_in_icm"])
