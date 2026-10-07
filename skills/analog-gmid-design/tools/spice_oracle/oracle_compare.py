# -*- coding: utf-8 -*-
"""oracle_compare.py -- 엔진 예측(오라클 입력) 대 SPICE 결과 비교표(JSON + Markdown).

진입점(단독 실행):
    python oracle_compare.py <oracle_input.json> <netlist.cir> <sim.json> <out_prefix>
                             [--judge judge.json] [--sat-margin-v V]

  <netlist.cir>.meta.json(오라클 넷리스트 메타)과 sim.json(oracle_simulate.py)을 읽어
  <out_prefix>.compare.json, <out_prefix>.compare.md 를 쓴다.

공개 함수: compare(inp, meta, sim, judge) -> dict, to_markdown(result) -> str, merge_judge(inp_judge, file_judge, sat_margin)

합격 판정(summary.verdict, 사용자 확정 2026-10-07) -- free 모드에서만:
  PASS = acceptance 선언 제약 전부 만족 + ID > 0(off_current_A 가 있으면 그 값 초과)인 전 MOS 가 VDS-VDSAT >= sat_margin_V.
  FAIL = 제약 불만족 또는 포화 아닌 전도 MOS. INCOMPLETE = sat_margin_V 미설정 또는 SPICE 로 못 잰 제약. BLOCKED = 막힘.
  forced 모드는 진단용: verdict 는 막힘이 없으면 INCOMPLETE, 소자 ID·gm 차이가 허용오차를 넘으면 summary.warnings.
  노드전압·소자 op·성능의 예측-SPICE 차이와 아래 judge 값은 기록만 한다(verdict 무관).
판정 설정(judge) -- 이 파일은 숫자 기본값을 갖지 않는다. 키가 없으면 그 기록 항목은 "N/A(tol 미설정)".
  tolerances: ID_rel, VGS_abs_V, VDS_abs_V, VSB_abs_V, gm_rel, gds_rel, gm_id_rel, node_abs_V, W_rel,
              kcl_abs_A, dc_gain_db_abs, pm_deg_abs, ugf_hz_rel, f3db_hz_rel, supply_current_A_rel
  sat_margin_V: 포화 판정 VDS >= VDSAT + sat_margin_V. 없으면 영역 판정 N/A(여유 값은 보고).
  off_current_A: 선택. |ID| 가 이보다 작으면 영역 'off'(포화 여유와 무관). 없으면 off 분류 안 함(ID 판정·below_vth 로 드러남).
크기 규칙: ngspice BSIM4 의 @ 동작점 값은 소자 극성으로 정규화돼 나온다 -- PMOS 도 켜져 포화면 id, vgs, vds,
  vth, vdsat 가 양수이고 vbs = type*(Vb-Vs)(2026-10-07 실측: PMOS M1a 소스 1.55 V·바디 1.8 V 에서 vbs=-0.25,
  vgs=+0.912). 그래서 두 극성 모두 ID=id, VGS=vgs, VDS=vds, VSB=-vbs 를 그대로 쓴다(엔진 예측도 크기 규칙).
  오차 = SPICE - 예측(abs) 또는 (SPICE - 예측)/|예측|(rel).
"""
import argparse
import json
import os
import sys

# measure -> (오차 종류, tolerance 키)
MEASURES = {
    "dc_gain_db": ("abs", "dc_gain_db_abs"),
    "pm_deg": ("abs", "pm_deg_abs"),
    "ugf_hz": ("rel", "ugf_hz_rel"),
    "f3db_hz": ("rel", "f3db_hz_rel"),
    "supply_current_A": ("rel", "supply_current_A_rel"),
}
NA_TOL = "N/A(tol 미설정)"


def rel_err(s, p):
    if s is None or p is None or p == 0:
        return None
    return (s - p) / abs(p)


def abs_err(s, p):
    if s is None or p is None:
        return None
    return s - p


def judge_err(err, tol):
    if err is None:
        return "N/A"
    if tol is None:
        return NA_TOL
    return "PASS" if abs(err) <= tol else "FAIL"


def merge_judge(inp_judge, file_judge, sat_margin):
    j = {"tolerances": {}, "sat_margin_V": None, "off_current_A": None}
    for src in (inp_judge or {}, file_judge or {}):
        j["tolerances"].update(src.get("tolerances") or {})
        for k in ("sat_margin_V", "off_current_A"):
            if src.get(k) is not None:
                j[k] = src[k]
    if sat_margin is not None:
        j["sat_margin_V"] = sat_margin
    return j


def measure_value(measure, sim, item):
    ac = sim.get("ac") or {}
    if measure == "supply_current_A":
        return (sim.get("rail_current_A") or {}).get(item.get("rail"))
    return ac.get(measure)


def _mul(a, b):
    return None if a is None else a * b


def compare(inp, meta, sim, judge):
    tol = judge["tolerances"]
    margin = judge["sat_margin_V"]
    off_i = judge.get("off_current_A")
    pred = inp.get("predictions") or {}
    pdev = pred.get("devices") or {}
    rows = []
    for d in inp["devices"]:
        n, k = d["name"], d["kind"]
        o = (sim.get("devices") or {}).get(n) or {}
        p = pdev.get(n) or {}
        g = meta["geometry"][n]
        idv, gm, gds = o.get("id"), o.get("gm"), o.get("gds")
        vgs, vds, vth, vdsat = o.get("vgs"), o.get("vds"), o.get("vth"), o.get("vdsat")
        vsb = _mul(o.get("vbs"), -1.0)
        sat_m = None if vds is None or vdsat is None else vds - vdsat
        region = None if sat_m is None or margin is None else ("sat" if sat_m >= margin else "triode")
        if off_i is not None and idv is not None and abs(idv) < off_i:
            region = "off"
        vov = None if vgs is None or vth is None else vgs - vth
        r = {"name": n, "kind": k, "L": g["L"], "finger_w": g["finger_w"], "n_fingers": g["n_fingers"],
             "W_from_fingers": g["W_from_fingers"], "W_declared": g["W_declared"],
             "W_rel": rel_err(g["W_from_fingers"], g["W_declared"]),
             "ID_pred": p.get("ID"), "ID_spice": idv, "ID_rel": rel_err(idv, p.get("ID")),
             "VGS_pred": p.get("VGS"), "VGS_spice": vgs, "VGS_err_V": abs_err(vgs, p.get("VGS")),
             "VDS_pred": p.get("VDS"), "VDS_spice": vds, "VDS_err_V": abs_err(vds, p.get("VDS")),
             "VSB_pred": p.get("VSB"), "VSB_spice": vsb, "VSB_err_V": abs_err(vsb, p.get("VSB")),
             "gm_pred": p.get("gm"), "gm_spice": gm, "gm_rel": rel_err(gm, p.get("gm")),
             "gds_pred": p.get("gds"), "gds_spice": gds, "gds_rel": rel_err(gds, p.get("gds")),
             "gm_id_pred": p.get("gm_id"),
             "gm_id_spice": None if not gm or not idv else gm / idv,
             "VTH_spice": vth, "VDSAT_spice": vdsat, "vov_spice": vov,
             "below_vth_spice": None if vov is None else vov < 0,
             "sat_margin_spice_V": sat_m, "region_spice": region, "region_pred": p.get("region")}
        r["gm_id_rel"] = rel_err(r["gm_id_spice"], r["gm_id_pred"])
        r["judge"] = {
            "W": judge_err(r["W_rel"], tol.get("W_rel")),
            "ID": judge_err(r["ID_rel"], tol.get("ID_rel")),
            "VGS": judge_err(r["VGS_err_V"], tol.get("VGS_abs_V")),
            "VDS": judge_err(r["VDS_err_V"], tol.get("VDS_abs_V")),
            "VSB": judge_err(r["VSB_err_V"], tol.get("VSB_abs_V")),
            "gm": judge_err(r["gm_rel"], tol.get("gm_rel")),
            "gds": judge_err(r["gds_rel"], tol.get("gds_rel")),
            "gm_id": judge_err(r["gm_id_rel"], tol.get("gm_id_rel")),
        }
        if margin is None:
            r["judge"]["region"] = "N/A(sat_margin 미설정)"
        elif region is None or r["region_pred"] is None:
            r["judge"]["region"] = "N/A"
        else:
            r["judge"]["region"] = "PASS" if region == r["region_pred"] else "FAIL"
        rows.append(r)

    pn = pred.get("nodes") or {}
    node_rows = []
    for net in meta["nets"]:
        pv, sv = pn.get(net), (sim.get("nodes") or {}).get(net)
        e = abs_err(sv, pv)
        held = net in meta["held"] or net in meta["gate_bias"] or net in meta["inputs"]
        node_rows.append({"net": net, "V_pred": pv, "V_spice": sv, "err_V": e, "held_by_testbench": held,
                          "judge": "N/A(테스트벤치가 고정)" if held else judge_err(e, tol.get("node_abs_V"))})

    perf = []
    for it in pred.get("metrics") or []:
        kind, key = MEASURES.get(it["measure"], (None, None))
        sv = measure_value(it["measure"], sim, it)
        if kind is None:
            perf.append({**it, "spice": None, "err": None, "err_kind": None, "judge": "N/A(모르는 measure)"})
            continue
        e = rel_err(sv, it["value"]) if kind == "rel" else abs_err(sv, it["value"])
        perf.append({**it, "spice": sv, "err": e, "err_kind": kind, "judge": judge_err(e, tol.get(key))})

    cons = []
    for c in (inp.get("acceptance") or {}).get("constraints") or []:
        sv = measure_value(c["measure"], sim, c)
        if sv is None or c.get("limit") is None:
            ok = "N/A(SPICE 값 없음)"
        elif c["op"] == ">=":
            ok = "PASS" if sv >= c["limit"] else "FAIL"
        elif c["op"] == "<=":
            ok = "PASS" if sv <= c["limit"] else "FAIL"
        else:
            ok = f"N/A(op {c['op']} 미지원)"
        cons.append({**c, "spice": sv, "judge": ok})

    kcl = []
    for net, i in sorted((sim.get("hold_current_A") or {}).items(), key=lambda kv: -abs(kv[1] or 0)):
        kcl.append({"net": net, "hold_current_A": i, "judge": judge_err(i, tol.get("kcl_abs_A"))})

    # ---- 기록용 비교 집계(verdict 무관) ----
    recs = []
    for r in rows:
        recs += list(r["judge"].values())
    recs += [x["judge"] for x in node_rows if not x["held_by_testbench"]]
    recs += [x["judge"] for x in perf] + [x["judge"] for x in kcl]
    rec_cnt = {"PASS": recs.count("PASS"), "FAIL": recs.count("FAIL"),
               "N/A": sum(1 for v in recs if v not in ("PASS", "FAIL"))}
    blockers = list(meta.get("blockers") or [])
    if not sim.get("op_ok") and not sim.get("skipped"):
        blockers.append("ngspice .op 결과 없음: " + " | ".join(sim.get("log_errors") or [])[:600])
    loop = sim.get("loop")
    if loop is not None and not loop.get("measures"):
        blockers.append("β 루프 측정 결과 없음(루프 넷리스트): " + " | ".join(loop.get("log_errors") or [])[:600])

    # ---- 합격 판정(사용자 확정 2026-10-07): free 모드 = 선언 제약 만족 + 전도 MOS 전부 포화 ----
    conducting = [r for r in rows if r["ID_spice"] is not None and r["ID_spice"] > (off_i if off_i is not None else 0)]
    unsat = None if margin is None else [r["name"] for r in conducting
                                         if r["sat_margin_spice_V"] is None or r["sat_margin_spice_V"] < margin]
    cons_fail = [c.get("name") or c["measure"] for c in cons if c["judge"] == "FAIL"]
    cons_na = [c.get("name") or c["measure"] for c in cons if c["judge"] not in ("PASS", "FAIL")]
    warnings = []
    if meta["bias"] == "forced":
        for r in rows:
            for key, tkey in (("ID_rel", "ID_rel"), ("gm_rel", "gm_rel")):
                t = tol.get(tkey)
                if t is not None and r[key] is not None and abs(r[key]) > t:
                    warnings.append(f"{r['name']}: {key} {r[key]:+.3g} 가 허용오차 {t:g} 를 넘는다")
    if blockers:
        verdict, why = "BLOCKED", "막힘이 있어 합격 판정을 하지 않는다"
    elif meta["bias"] != "free":
        verdict, why = "INCOMPLETE", "forced 는 진단 모드 -- 합격 판정은 free 모드에서만 한다"
    elif cons_fail or unsat:
        verdict = "FAIL"
        why = "; ".join(x for x in (f"선언 제약 불만족 {cons_fail}" if cons_fail else "",
                                     f"포화 아닌 전도 MOS {unsat}" if unsat else "") if x)
    elif margin is None or cons_na:
        verdict = "INCOMPLETE"
        why = "; ".join(x for x in ("sat_margin_V 미설정 -- 포화 조건 판정 불가" if margin is None else "",
                                     f"SPICE 로 값을 못 얻은 제약 {cons_na}" if cons_na else "") if x)
    else:
        verdict, why = "PASS", "선언 제약 전부 만족, 전도 MOS 전부 포화"
    summary = {"verdict": verdict, "verdict_reason": why, "warnings": warnings,
               "acceptance": {"constraints_failed": cons_fail, "constraints_unmeasured": cons_na,
                              "conducting_devices": len(conducting), "unsaturated_conducting": unsat,
                              "sat_margin_V": margin, "off_current_A": off_i},
               "record_counts": rec_cnt, "devices": len(rows),
               "sat_in_spice": None if margin is None else sum(1 for r in rows if r["region_spice"] == "sat"),
               "not_sat": None if margin is None else [r["name"] for r in rows if r["region_spice"] != "sat"],
               "spice_ac": sim.get("ac"), "rail_current_A": sim.get("rail_current_A")}
    return {"circuit": inp.get("circuit"), "bias": meta["bias"], "lut_meta": meta["lut_meta"],
            "judge_config": judge, "notes": meta.get("notes"), "blockers": blockers,
            "summary": summary, "performance": perf, "constraints": cons, "kcl_residual": kcl,
            "devices": rows, "nodes": node_rows, "provenance": inp.get("provenance")}


def _f(v, f="{:.4g}"):
    if v is None:
        return "-"
    if isinstance(v, str):
        return v
    return f.format(v)


def to_markdown(res):
    s = res["summary"]
    L = [f"### {res['circuit']} -- 엔진 예측 vs SPICE (bias={res['bias']})"]
    for w in s.get("warnings") or []:
        L.append(f"- **경고(forced)**: {w}")
    rc = s["record_counts"]
    L += [f"- 판정: **{s['verdict']}** -- {s['verdict_reason']}",
         f"- 기록용 비교(판정 무관): 허용오차 안 {rc['PASS']}, 밖 {rc['FAIL']}, N/A {rc['N/A']}",
         f"- 모델 코너/온도(LUT npz 메타): {res['lut_meta'].get('corner')}, {res['lut_meta'].get('temp_c')} C",
         f"- 판정 설정: {json.dumps(res['judge_config'], ensure_ascii=False)}",
         (f"- SPICE 포화 소자 {s['sat_in_spice']}/{s['devices']}, 포화 아님: {', '.join(s['not_sat']) or '-'}"
          if s["sat_in_spice"] is not None else "- 포화 판정: sat_margin_V 미설정(포화 여유 값만 보고)")]
    for b in res["blockers"]:
        L.append(f"- 막힘: {b}")
    for n in res.get("notes") or []:
        L.append(f"- {n}")
    for w in (res.get("provenance") or {}).get("warnings") or []:
        L.append(f"- 입력 경고(어댑터): {w}")
    ac = s.get("spice_ac") or {}
    L += ["", "| 성능 | 예측 | SPICE | 차이 | 판정 |", "|---|---|---|---|---|"]
    for p in res["performance"]:
        L.append(f"| {p['measure']} ({p.get('name', '')}) | {_f(p['value'])} | {_f(p['spice'])} | "
                 f"{_f(p['err'], '{:+.3g}') if p['err_kind'] == 'abs' else _f(p['err'], '{:+.1%}')} | {p['judge']} |")
    L.append(f"| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | {_f(ac.get('dc_gain_db'))} / {_f(ac.get('ugf_hz'))} / "
             f"{_f(ac.get('pm_deg'))} / {_f(ac.get('f3db_hz'))} | | |")
    L.append(f"| (참고) PM 정의 {ac.get('pm_definition')}: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | "
             f"{_f(ac.get('loop_gain_dc_db'))} / {_f(ac.get('loop_ugf_hz'))} / {_f(ac.get('pm_open_loop_deg'))} | | |")
    for c in res["constraints"]:
        L.append(f"| 제약 {c.get('name', '')}: {c['measure']} {c['op']} {_f(c.get('limit'))} | | {_f(c['spice'])} | | {c['judge']} |")
    if res["kcl_residual"]:
        L += ["", "| forced 고정원 전류(KCL 잔차) 넷 | uA | 판정 |", "|---|---|---|"]
        for k in res["kcl_residual"]:
            L.append(f"| {k['net']} | {_f(None if k['hold_current_A'] is None else k['hold_current_A'] * 1e6)} | {k['judge']} |")
    L += ["", "| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["devices"]:
        um = lambda v: None if v is None else v * 1e6  # noqa: E731
        L.append(f"| {r['name']} | {_f(um(r['L']))} | {_f(um(r['finger_w']))} x {r['n_fingers']} | "
                 f"{_f(um(r['ID_pred']))}/{_f(um(r['ID_spice']))} | {_f(r['ID_rel'], '{:+.1%}')} | "
                 f"{_f(r['VGS_pred'], '{:.3f}')}/{_f(r['VGS_spice'], '{:.3f}')} | {_f(r['VDS_pred'], '{:.3f}')}/{_f(r['VDS_spice'], '{:.3f}')} | "
                 f"{_f(r['VSB_pred'], '{:.3f}')}/{_f(r['VSB_spice'], '{:.3f}')} | {_f(r['VDSAT_spice'], '{:.3f}')} | "
                 f"{_f(r['sat_margin_spice_V'], '{:+.3f}')} | {r['region_spice']} | {_f(r['gm_rel'], '{:+.1%}')} | {_f(r['gds_rel'], '{:+.1%}')} |")
    L += ["", "| 넷 | 예측 V | SPICE V | 차 | 판정 |", "|---|---|---|---|---|"]
    for n in res["nodes"]:
        L.append(f"| {n['net']} | {_f(n['V_pred'], '{:.4f}')} | {_f(n['V_spice'], '{:.4f}')} | {_f(n['err_V'], '{:+.4f}')} | {n['judge']} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="엔진 예측 대 SPICE 비교표")
    ap.add_argument("oracle_input")
    ap.add_argument("netlist")
    ap.add_argument("sim_json")
    ap.add_argument("out_prefix")
    ap.add_argument("--judge", default=None, help="판정 설정 JSON(tolerances, sat_margin_V)")
    ap.add_argument("--sat-margin-v", type=float, default=None)
    a = ap.parse_args(argv)
    with open(a.oracle_input, encoding="utf-8") as f:
        inp = json.load(f)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from oracle_netlist import validate_input
    errs = validate_input(inp)
    if errs:
        print("입력이 oracle_input.schema.json 위반 -- 거부(비교표를 쓰지 않음):")
        for e in errs:
            print("  ", e)
        return 2
    with open(a.netlist + ".meta.json", encoding="utf-8") as f:
        meta = json.load(f)
    with open(a.sim_json, encoding="utf-8") as f:
        sim = json.load(f)
    fj = None
    if a.judge:
        with open(a.judge, encoding="utf-8") as f:
            fj = json.load(f)
    res = compare(inp, meta, sim, merge_judge(inp.get("judge"), fj, a.sat_margin_v))
    with open(a.out_prefix + ".compare.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(a.out_prefix + ".compare.md", "w", encoding="utf-8") as f:
        f.write(to_markdown(res))
    print("verdict:", res["summary"]["verdict"], "--", res["summary"]["verdict_reason"])
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
