# -*- coding: utf-8 -*-
"""oracle_compare.py -- 엔진 예측(오라클 입력) 대 SPICE 결과 비교표(JSON + Markdown).

진입점(단독 실행):
    python oracle_compare.py <oracle_input.json> <netlist.cir> <sim.json> <out_prefix>
                             [--judge judge.json] [--sat-margin-v V]

  <netlist.cir>.meta.json(오라클 넷리스트 메타)과 sim.json(oracle_simulate.py)을 읽어
  <out_prefix>.compare.json, <out_prefix>.compare.md 를 쓴다.

공개 함수: compare(inp, meta, sim, judge) -> dict, to_markdown(result) -> str, merge_judge(inp_judge, file_judge, sat_margin),
          device_tolerance(inp, judge, name, key), iso_summary(rows, meta), forced_diagnosis(inp, rows, kcl),
          diagnose(free_res, forced_res), conduction_check(pred, idv), measure_value(measure, sim, item),
          measure_undefined(measure, sim, item)
[신규] C26 rout_ohm: 제약은 C9 그대로 판정, SPICE 값이 정의 불가(음의 실수부)면 'N/A(정의 불가: negative_real_part)'
       -> INCOMPLETE(PASS 불가). summary.spice_rout = sim.rout, summary.pm_loop = PM 루프 정의 기록(C12 보충·C27).
[신규 C10] pm_deg: ac.pm_undefined(개루프 RHP 극·불안정 폐루프·안정성 근거 부족)이면 'N/A(정의 불가: <이유>)' ->
       INCOMPLETE(PASS 불가). summary.stability = PM 안정성 근거 요약.
[신규] 소자별 허용오차(C16): predictions.devices[].tol 이 한 소자라도 있으면 ID·gm 판정은 소자별 값만 쓴다(스칼라 폴백 없음).
[신규] iso(C17): summary.iso = 소자별 ID 오차가 그 소자 허용오차 안인가(K3 판정), verdict 는 진단 모드라 INCOMPLETE.
[신규] Z1(C18): 넷리스트를 --omit/--short 로 바꾼 실행은 합격 판정을 하지 않는다(INCOMPLETE).
[신규] diagnosis(C19): forced 는 넷별 KCL 잔차 대 소자 tol_I 합, 게이트 공유 넷의 등가 dVGS = dID/gm 퍼짐을 기록,
       diagnose() 가 free FAIL 원인을 '경계조건 쪽'/'엔진 DC 비정합'으로 분류(기록만).

합격 판정(summary.verdict, 사용자 확정 2026-10-07, Q5 보강) -- free 모드에서만:
  PASS = acceptance 선언 제약(ratio_db 포함, C24) 전부 만족 + ID > 그 소자 문턱인 전 MOS 가 VDS-VDSAT >= sat_margin_V
         + 엔진 예측 전도 MOS 가 SPICE 에서도 ID > 그 소자 off_current_A(C23).
  FAIL = 제약 불만족, 포화 아닌 전도 MOS, 또는 SPICE 에서 꺼진 예측 전도 MOS. INCOMPLETE = sat_margin_V 미설정, SPICE 로 못 잰
  제약, 또는 전도 확인을 판정 못 한 소자(off_current_A 없음 등). BLOCKED = 막힘(C22 확산 기하 없음 포함).
[신규] C25 slew_rate_v_per_s·settle_s: 기록 행만, not_measured(정의 미정).
  forced 모드는 진단용: verdict 는 막힘이 없으면 INCOMPLETE, 소자 ID·gm 차이가 허용오차를 넘으면 summary.warnings.
  노드전압·소자 op·성능의 예측-SPICE 차이와 아래 judge 값은 기록만 한다(verdict 무관).
판정 설정(judge) -- 이 파일은 숫자 기본값을 갖지 않는다. 키가 없으면 그 기록 항목은 "N/A(tol 미설정)".
  tolerances: ID_rel, VGS_abs_V, VDS_abs_V, VSB_abs_V, gm_rel, gds_rel, gm_id_rel, node_abs_V, W_rel,
              kcl_abs_A, dc_gain_db_abs, pm_deg_abs, ugf_hz_rel, f3db_hz_rel, supply_current_A_rel
  sat_margin_V: 포화 판정 VDS >= VDSAT + sat_margin_V. 없으면 영역 판정 N/A(여유 값은 보고).
  off_current_A: 선택. |ID| 가 이보다 작으면 영역 'off'(포화 여유와 무관). 없으면 off 분류 안 함(ID 판정·below_vth 로 드러남).
크기 규칙: ngspice BSIM4 의 @ 동작점 값은 소자 극성으로 정규화돼 나온다 -- PMOS 도 켜져 포화면 id, vgs, vds,
  vth, vdsat 가 양수이고 vbs = type*(Vb-Vs)(2026-10-07 실측: PMOS M1a 소스 1.55 V·바디 1.8 V 에서 vbs=-0.25,
  vgs=+0.912). [정정 2026-10-07] 단 @id 는 소스/드레인 역할이 뒤바뀐(역방향 전도) 소자에서도 양수다(채널 전류 크기) --
  @vds 는 선언 단자 방향 부호를 유지하므로 ID = @id x sign(@vds)(signed_id), VGS=vgs, VDS=vds, VSB=-vbs(엔진 예측도 크기 규칙).
  오차 = SPICE - 예측(abs) 또는 (SPICE - 예측)/|예측|(rel).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_netlist import sense_key  # noqa: E402

# measure -> (오차 종류, tolerance 키)
MEASURES = {
    "dc_gain_db": ("abs", "dc_gain_db_abs"),
    "pm_deg": ("abs", "pm_deg_abs"),
    "cm_pm_deg": ("abs", "pm_deg_abs"),
    "ugf_hz": ("rel", "ugf_hz_rel"),
    "f3db_hz": ("rel", "f3db_hz_rel"),
    "supply_current_A": ("rel", "supply_current_A_rel"),
    "ratio_db": ("abs", "ratio_db_abs"),
    "rout_ohm": ("rel", "rout_ohm_rel"),
    # [신규 U6] .noise 대조, 오프셋 Monte-Carlo, 스윙·ICMR 스윕 (sim.noise / sim.offset_mc / sim.swing_icmr)
    "noise_th_in_v2hz": ("rel", "noise_th_in_v2hz_rel"),
    "noise_fc_in_hz": ("rel", "noise_fc_in_hz_rel"),
    "noise_excess_th": ("rel", "noise_excess_th_rel"),
    "noise_out_int_vrms": ("rel", "noise_out_int_vrms_rel"),
    "offset_in_sigma_mv": ("rel", "offset_in_sigma_mv_rel"),
    "swing_out_v": ("abs", "swing_out_v_abs"),
    "icmr_v": ("abs", "icmr_v_abs"),
    "icm_margin_v": ("abs", "icm_margin_v_abs"),
}
# measure -> (sim 블록, 그 블록 안 경로) . 값이 None 이면 측정 안 됨; 이유는 U6_UNDEFINED 가 준다
U6_MEASURES = {
    "noise_th_in_v2hz": ("noise", ("open_loop", "th_in_v2hz")),
    "noise_fc_in_hz": ("noise", ("open_loop", "fc_in_hz")),
    "noise_excess_th": ("noise", ("open_loop", "excess_th")),
    "noise_out_int_vrms": ("noise", ("closed_loop", "out_int_vrms")),
    "offset_in_sigma_mv": ("offset_mc", ("sigma_in_mV",)),
    "swing_out_v": ("swing_icmr", ("swing_out_v",)),
    "icmr_v": ("swing_icmr", ("icmr_v",)),
    "icm_margin_v": ("swing_icmr", ("icm_margin_v",)),
}
NA_TOL = "N/A(tol 미설정)"
# C25: 기록 전용 과도 measure -- SPICE 정의가 계약에 없어 재지 않는다(추측 금지). 정의가 정해지면 측정으로 바꾼다.
TRANSIENT_MEASURES = ("slew_rate_v_per_s", "settle_s")
TRANSIENT_NOT_MEASURED_REASON = (
    "β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 "
    "(gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, "
    "driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)")


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


def device_tolerance(inp, judge, name, key):
    """소자 name 의 허용오차(key = ID_rel|gm_rel). 반환 (값 또는 None, 출처 문자열).
    predictions.devices 중 하나라도 tol 을 가지면 소자별 모드 -- 그 소자의 tol[key] 만 쓰고 없으면 None(스칼라 폴백 없음).
    아무 소자도 tol 이 없으면 judge.tolerances[key] 스칼라(기존 동작)."""
    pdev = (inp.get("predictions") or {}).get("devices") or {}
    if any(isinstance(v, dict) and v.get("tol") for v in pdev.values()):
        v = ((pdev.get(name) or {}).get("tol") or {}).get(key)
        return v, ("device" if v is not None else "device(없음)")
    v = judge["tolerances"].get(key)
    return v, ("scalar" if v is not None else "none")


def measure_value(measure, sim, item):
    ac = sim.get("ac") or {}
    if measure == "supply_current_A":
        return (sim.get("rail_current_A") or {}).get(item.get("rail"))
    if measure == "ratio_db":  # C24: 같은 view(dict 동등)를 잰 결과
        for r in sim.get("ratio") or []:
            if r.get("view") == item.get("view"):
                return r.get("ratio_db")
        return None
    if measure == "rout_ohm":  # C26: 같은 감지 뷰(sense_key 동등)를 잰 결과. 정의 불가(음의 실수부)면 None
        r = _rout_entry(sim, item)
        return None if r is None else r.get("rout_ohm")
    if measure in TRANSIENT_MEASURES:  # C25: 재지 않음
        return None
    if measure in U6_MEASURES:
        blk, path = U6_MEASURES[measure]
        cur = sim.get(blk)
        for k in path:
            cur = None if not isinstance(cur, dict) else cur.get(k)
        return cur
    if measure == "cm_pm_deg":  # CM 루프(cm_output_loop): sim.cm_loop 의 PM(정의 불가면 None)
        return (sim.get("cm_loop") or {}).get("pm_deg")
    return ac.get(measure)


def _rout_entry(sim, item):
    if item.get("view") is None:
        return None
    k = sense_key(item["view"])
    for r in sim.get("rout") or []:
        if sense_key(r.get("view") or {}) == k:
            return r
    return None


def measure_undefined(measure, sim, item):
    """SPICE 값이 정의 불가인 이유(값이 None 인 까닭이 측정 실패가 아니라 정의 밖일 때). C26 rout_ohm 의
    'negative_real_part', [신규 C10] pm_deg 의 ac.pm_undefined(개루프 RHP 극·불안정 폐루프·안정성 근거 부족 -- PM 이 안정
    여유가 아님). 없으면 None. 판정 칸은 'N/A(정의 불가: <이유>)' -> 제약이면 INCOMPLETE(PASS 불가)."""
    if measure == "pm_deg":
        return (sim.get("ac") or {}).get("pm_undefined")
    if measure == "cm_pm_deg":
        cl = sim.get("cm_loop")
        return None if cl is None else cl.get("pm_undefined")
    if measure in U6_MEASURES and measure_value(measure, sim, item) is None:
        return u6_undefined(measure, sim)
    if measure == "rout_ohm":
        r = _rout_entry(sim, item)
        if r is not None and r.get("rout_ohm") is None and r.get("undefined") not in (None, "no_data"):
            return r["undefined"]
    return None


def u6_undefined(measure, sim):
    """[신규 U6] 값이 None 인 U6 measure 의 이유(측정 실패가 아니라 정의 밖일 때). 블록이 없으면 None(입력에 측정 블록이 없다 = 'SPICE 값 없음')."""
    blk = U6_MEASURES[measure][0]
    b = sim.get(blk)
    if not b:
        return None
    if blk == "noise":
        part = b.get(U6_MEASURES[measure][1][0]) or {}
        if measure == "noise_fc_in_hz" and part.get("fc_reason"):
            return f"noise_fc_{part['fc_reason']}"
        if measure == "noise_excess_th" and part.get("excess_reason"):
            return "noise_excess_input_cell_undeclared"
        return (part.get("reason") or "")[:80] or None
    if blk == "offset_mc":
        return (b.get("reason") or "")[:80] or None
    if blk == "swing_icmr":
        if measure == "icm_margin_v" and ((b.get("icmr") or {}).get("icm_margin_reason") == "input_dc_pending"):
            return "input_dc_pending"
        sub_ = b.get("swing") if measure == "swing_out_v" else b.get("icmr")
        return ((sub_ or {}).get("reason") or b.get("reason") or "")[:80] or None
    return None


CM_INEFFECTIVE = "cm_loop_ineffective"


def cm_loop_ineffective(sim):
    """[CM 사용자 결정 2026-10-08 A] 공통 모드 루프 |T_cm| 이 기준점(fstart)에서 1 이하라 0 dB 교차가 없다 = CMFB 무효 -> cm_pm_deg 제약 위반
    (엔진 search.ss_constraint_rows 의 dc_not_above_level 위반 행과 같은 판정). 개루프 RHP 극점 등 pm_undefined 가 있으면 해당 없음.
    측정이 없으면 False. 반환 bool."""
    cl = sim.get("cm_loop") or {}
    m = cl.get("measures") or {}
    return bool(m) and cl.get("pm_deg") is None and cl.get("pm_undefined") is None and m.get("ugf_hz") is None         and m.get("gain_dc", 0) <= 1


def signed_id(op_id, op_vds):
    """크기 규칙 ID(부호 포함: 선언 드레인 기준 정상 방향 전도 = 양수, 역방향 = 음수) = @id x sign(@vds).
    ngspice BSIM4 의 @id 는 소스/드레인 역할이 뒤바뀌어도 양수(채널 전류 크기)이고, @vds = type*(V(d)-V(s)) 는 선언 단자
    방향의 부호를 유지한다(2026-10-07 실측, 0 V 감지원 대조 -- README 크기 규칙). @vds = 0 이면 0, 둘 중 하나가 없으면 None."""
    if op_id is None or op_vds is None:
        return None
    return op_id * (1.0 if op_vds > 0 else (-1.0 if op_vds < 0 else 0.0))


def conduction_check(pred, idv):
    """C23: 엔진 예측 전도 소자가 SPICE 에서 꺼졌는가. 반환 (predicted_conducting, 판정 문자열).
    pred = predictions.devices[이름](없으면 None), idv = SPICE ID(크기 규칙, 부호 포함)."""
    if pred is None:
        return None, "N/A(예측 없음)"
    if pred.get("region") == "off":
        return False, "N/A(엔진 예측 off)"
    thr = pred.get("off_current_A")
    if thr is None:
        return True, "N/A(off_current_A 없음)"
    if idv is None:
        return True, "N/A(SPICE ID 없음)"
    return True, ("FAIL" if idv <= thr else "PASS")


def _mul(a, b):
    return None if a is None else a * b


def compare(inp, meta, sim, judge):
    tol = judge["tolerances"]
    margin = judge["sat_margin_V"]
    off_i = judge.get("off_current_A")
    pred = inp.get("predictions") or {}
    pdev = pred.get("devices") or {}
    rows = []
    z1_omitted = []
    for d in inp["devices"]:
        n, k = d["name"], d["kind"]
        if n not in meta["geometry"]:  # Z1 --omit 으로 넷리스트에서 뺀 소자
            z1_omitted.append(n)
            continue
        o = (sim.get("devices") or {}).get(n) or {}
        p = pdev.get(n) or {}
        g = meta["geometry"][n]
        t_id, t_id_src = device_tolerance(inp, judge, n, "ID_rel")
        t_gm, _ = device_tolerance(inp, judge, n, "gm_rel")
        gm, gds = o.get("gm"), o.get("gds")
        vgs, vds, vth, vdsat = o.get("vgs"), o.get("vds"), o.get("vth"), o.get("vdsat")
        idv = signed_id(o.get("id"), vds)  # 선언 단자 방향 부호(역방향 전도 = 음수)
        vsb = _mul(o.get("vbs"), -1.0)
        sat_m = None if vds is None or vdsat is None else vds - vdsat
        region = None if sat_m is None or margin is None else ("sat" if sat_m >= margin else "triode")
        # 전도 문턱: 소자별 off_current_A(C23, 엔진 계산) 우선, 없으면 judge.off_current_A
        thr = p.get("off_current_A") if p.get("off_current_A") is not None else off_i
        if thr is not None and idv is not None and abs(idv) < thr:
            region = "off"
        pc, cc = conduction_check(pdev.get(n), idv)
        vov = None if vgs is None or vth is None else vgs - vth
        r = {"name": n, "kind": k, "L": g["L"], "finger_w": g["finger_w"], "n_fingers": g["n_fingers"],
             "W_from_fingers": g["W_from_fingers"], "W_declared": g["W_declared"],
             "W_rel": rel_err(g["W_from_fingers"], g["W_declared"]),
             "ID_pred": p.get("ID"), "ID_spice": idv, "ID_spice_op_id": o.get("id"),
             "ID_rel": rel_err(idv, p.get("ID")),
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
        r["tol_ID_rel"], r["tol_gm_rel"], r["tol_source"] = t_id, t_gm, t_id_src
        r["off_current_A_pred"], r["conduction_threshold_A"] = p.get("off_current_A"), thr
        r["predicted_conducting"], r["conduction_check"] = pc, cc
        r["diffusion"] = g.get("diffusion")
        r["judge"] = {
            "W": judge_err(r["W_rel"], tol.get("W_rel")),
            "ID": judge_err(r["ID_rel"], t_id),
            "VGS": judge_err(r["VGS_err_V"], tol.get("VGS_abs_V")),
            "VDS": judge_err(r["VDS_err_V"], tol.get("VDS_abs_V")),
            "VSB": judge_err(r["VSB_err_V"], tol.get("VSB_abs_V")),
            "gm": judge_err(r["gm_rel"], t_gm),
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
        if it["measure"] in TRANSIENT_MEASURES:
            perf.append({**it, "spice": None, "err": None, "err_kind": None,
                         "judge": "N/A(not_measured: 과도 정의 미정 -- summary.transient)"})
            continue
        if kind is None:
            perf.append({**it, "spice": None, "err": None, "err_kind": None, "judge": "N/A(모르는 measure)"})
            continue
        e = rel_err(sv, it["value"]) if kind == "rel" else abs_err(sv, it["value"])
        und = measure_undefined(it["measure"], sim, it)
        perf.append({**it, "spice": sv, "err": e, "err_kind": kind,
                     "judge": f"N/A(정의 불가: {und})" if und else judge_err(e, tol.get(key))})

    cons = []
    for c in (inp.get("acceptance") or {}).get("constraints") or []:
        sv = measure_value(c["measure"], sim, c)
        und = measure_undefined(c["measure"], sim, c)
        if c["measure"] == "cm_pm_deg" and cm_loop_ineffective(sim):
            ok, und = "FAIL", CM_INEFFECTIVE      # CMFB 무효 = 위반 (PM 값과 무관)
        elif und:
            ok = f"N/A(정의 불가: {und})"
        elif sv is None or c.get("limit") is None:
            ok = "N/A(SPICE 값 없음)"
        elif c["op"] == ">=":
            ok = "PASS" if sv >= c["limit"] else "FAIL"
        elif c["op"] == "<=":
            ok = "PASS" if sv <= c["limit"] else "FAIL"
        else:
            ok = f"N/A(op {c['op']} 미지원)"
        cons.append({**c, "spice": sv, "judge": ok, "undefined": und})

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
    # [신규] 루프 T 가 정의 불가(Middlebrook 분모 0, sim.loop.singular)면 측정 실패가 아니다 -> 막힘 아님, PM 은
    # ac.pm_undefined = loop_probe_singular 로 N/A(정의 불가) -> PASS 불가(C10)
    if loop is not None and not loop.get("measures") and not loop.get("singular"):
        blockers.append("β 루프 측정 결과 없음(루프 넷리스트): " + " | ".join(loop.get("log_errors") or [])[:600])
    cml = sim.get("cm_loop")
    if cml is not None and not cml.get("measures") and not cml.get("singular"):
        blockers.append("CM 루프 측정 결과 없음(cmloop 넷리스트): " + " | ".join(cml.get("log_errors") or [])[:600])

    # ---- 합격 판정(사용자 확정 2026-10-07): free 모드 = 선언 제약 만족 + 전도 MOS 전부 포화 ----
    conducting = [r for r in rows if r["ID_spice"] is not None and r["ID_spice"] >
                  (r["conduction_threshold_A"] if r["conduction_threshold_A"] is not None else 0)]
    unsat = None if margin is None else [r["name"] for r in conducting
                                         if r["sat_margin_spice_V"] is None or r["sat_margin_spice_V"] < margin]
    cons_fail = [c.get("name") or c["measure"] for c in cons if c["judge"] == "FAIL"]
    cons_na = [c.get("name") or c["measure"] for c in cons if c["judge"] not in ("PASS", "FAIL")]
    # [신규 U6, 사용자 결정 B·Q10] 폐루프 불안정(Nyquist Z = N + P >= 1 또는 폐루프 과도 unstable -- limit_cycle 포함)은 pm 제약이 있든
    # 없든 FAIL 이다. 둘 다 결론을 못 낸 경우(verdict undetermined)만 이 항으로 FAIL 을 만들지 않는다(pm 제약이 N/A -> INCOMPLETE).
    stab_sum = _stability_summary(sim.get("ac") or {})
    stab_fail = bool(stab_sum and stab_sum.get("verdict") == "unstable")
    # C23: 엔진 예측 전도 소자가 SPICE 에서 꺼짐 -> FAIL, 판정 못 함 -> PASS 불가(엔진 예측 off 는 대상 밖)
    off_spice = [r["name"] for r in rows if r["conduction_check"] == "FAIL"]
    cond_na = {r["name"]: r["conduction_check"] for r in rows
               if r["conduction_check"] not in ("PASS", "FAIL", "N/A(엔진 예측 off)")}
    warnings = []
    if meta["bias"] == "forced":
        for r in rows:
            for key, t in (("ID_rel", r["tol_ID_rel"]), ("gm_rel", r["tol_gm_rel"])):
                if t is not None and r[key] is not None and abs(r[key]) > t:
                    warnings.append(f"{r['name']}: {key} {r[key]:+.3g} 가 허용오차 {t:g} 를 넘는다")
    z1 = meta.get("z1")
    if blockers:
        verdict, why = "BLOCKED", "막힘이 있어 합격 판정을 하지 않는다"
    elif meta["bias"] != "free":
        verdict, why = "INCOMPLETE", f"{meta['bias']} 는 진단 모드 -- 합격 판정은 free 모드에서만 한다"
    elif z1:
        verdict, why = "INCOMPLETE", f"Z1 제거법 진단 실행(회로 변경 omit={z1['omit']} short={z1['short']}) -- 합격 판정 안 함"
    elif cons_fail or unsat or off_spice or stab_fail:
        verdict = "FAIL"
        why = "; ".join(x for x in (f"선언 제약 불만족 {cons_fail}" if cons_fail else "",
                                     f"포화 아닌 전도 MOS {unsat}" if unsat else "",
                                     f"엔진 예측 전도인데 SPICE 에서 꺼진 MOS {off_spice}" if off_spice else "",
                                     (f"폐루프 불안정(Z = {stab_sum.get('Z')}, 과도 {stab_sum.get('transient_status')}, "
                                      f"근거 {stab_sum.get('verdict_basis')})" if stab_fail else "")) if x)
    elif margin is None or cons_na or cond_na:
        verdict = "INCOMPLETE"
        why = "; ".join(x for x in ("sat_margin_V 미설정 -- 포화 조건 판정 불가" if margin is None else "",
                                     f"SPICE 로 값을 못 얻은 제약 {cons_na}" if cons_na else "",
                                     f"전도 확인(C23)을 판정 못 한 소자 {cond_na}" if cond_na else "") if x)
    else:
        verdict, why = "PASS", "선언 제약 전부 만족, 전도 MOS 전부 포화, 엔진 예측 전도 MOS 전부 SPICE 에서도 전도"
    geo = meta.get("geometry") or {}
    jsrc = [((g.get("diffusion") or {}).get("source")) for g in geo.values()]
    summary = {"verdict": verdict, "verdict_reason": why, "warnings": warnings,
               # [사용자 결정 4] 한계 사이클 FAIL 이 '고Q 안정 회로와 구별 불가'라는 판정 한계에서 나왔을 수 있다는 표시(보고 맨 앞)
               "limit_cycle_vs_slow_decay_unresolved": (stab_sum or {}).get("limit_cycle_vs_slow_decay_unresolved"),
               "acceptance": {"constraints_failed": cons_fail, "constraints_unmeasured": cons_na,
                              "closed_loop_unstable": stab_fail,
                              "conducting_devices": len(conducting), "unsaturated_conducting": unsat,
                              "sat_margin_V": margin, "off_current_A": off_i,
                              "off_in_spice": off_spice, "conduction_not_evaluated": cond_na},
               "junction_capacitance": {"included": bool(jsrc) and all(jsrc),
                                        "by_source": {"device": jsrc.count("device"),
                                                      "process_rule": jsrc.count("process_rule"),
                                                      "none": jsrc.count(None)},
                                        "missing": sorted(n for n, g in geo.items()
                                                          if not (g.get("diffusion") or {}).get("source")),
                                        "zero_area": sorted(n for n, g in geo.items()
                                                            if (g.get("diffusion") or {}).get("source") and
                                                            not any(g["diffusion"][k] for k in ("ad", "as", "pd", "ps")))},
               "transient": {"status": "not_measured", "measures": list(TRANSIENT_MEASURES),
                             "reason": TRANSIENT_NOT_MEASURED_REASON},
               "record_counts": rec_cnt, "devices": len(rows),
               "sat_in_spice": None if margin is None else sum(1 for r in rows if r["region_spice"] == "sat"),
               "not_sat": None if margin is None else [r["name"] for r in rows if r["region_spice"] != "sat"],
               "spice_ac": sim.get("ac"), "spice_ratio": sim.get("ratio") or [],
               "spice_rout": sim.get("rout") or [],
               "pm_loop": {"pm_definition": (sim.get("ac") or {}).get("pm_definition"),
                           "feedback_passives": list(inp.get("feedback_passives") or []),
                           "feedback_passives_basis": inp.get("feedback_passives_basis"),
                           "loop_break_nets": (sim.get("ac") or {}).get("loop_break_nets"),
                           "loop_weights": (sim.get("ac") or {}).get("loop_weights")},
               "stability": stab_sum,
               "cm_loop": _cm_loop_summary(sim.get("cm_loop")),
               "u6": {k: sim.get(k) for k in ("noise", "offset_mc", "swing_icmr") if sim.get(k) is not None} or None,
               "rail_current_A": sim.get("rail_current_A")}
    ti = meta.get("topology_identity") or {"status": "unverified", "diffs": [], "notes": ["넷리스트 meta 에 C15 결과 없음"]}
    summary["topology_identity"] = {"status": ti.get("status"), "required": ti.get("required", False),
                                    "diff_count": len(ti.get("diffs") or []), "path": ti.get("topology_path")}
    summary["z1"] = None if not z1 else {**z1, "omitted_devices": z1_omitted}
    if meta["bias"] == "iso":
        summary["iso"] = iso_summary(rows, meta)
    res = {"circuit": inp.get("circuit"), "bias": meta["bias"], "lut_meta": meta["lut_meta"],
           "judge_config": judge, "notes": meta.get("notes"), "blockers": blockers,
           "summary": summary, "performance": perf, "constraints": cons, "kcl_residual": kcl,
           "devices": rows, "nodes": node_rows, "topology_identity": ti, "provenance": inp.get("provenance")}
    if meta["bias"] == "forced":
        res["diagnosis"] = forced_diagnosis(inp, rows, kcl)
    return res


def _cm_loop_summary(cl):
    """summary.cm_loop = 공통 모드 루프 PM 측정 요약(없으면 None). stability 는 DM 과 같은 형식(_stability_summary)."""
    if not cl:
        return None
    m = cl.get("measures") or {}
    return {"break_nets": cl.get("break_nets"), "pm_deg": cl.get("pm_deg"), "pm_deg_raw": cl.get("pm_deg_raw"),
            "pm_undefined": cl.get("pm_undefined"), "loop_gain_dc_db": m.get("dc_gain_db"), "loop_ugf_hz": m.get("ugf_hz"),
            "singular": cl.get("singular"), "stability": _stability_summary({"stability": cl.get("stability"),
                                                                             "pm_deg_raw": cl.get("pm_deg_raw")})}


def _stability_summary(ac):
    """[신규 C10] summary.stability = PM 안정성 근거 요약(전체는 summary.spice_ac.stability). ac 가 없으면 None."""
    st = ac.get("stability") if ac else None
    if not st:
        return None
    ny, tr = st.get("nyquist") or {}, st.get("transient") or {}
    pz = st.get("pz") or {}
    return {"pm_valid": st.get("pm_valid"), "pm_undefined": st.get("pm_undefined"), "pm_deg_raw": ac.get("pm_deg_raw"),
            "loop": st.get("loop"), "closed_loop": st.get("closed_loop"),
            "open_loop_rhp_poles": st.get("open_loop_rhp_poles"),
            "open_loop_rhp_poles_bound": st.get("open_loop_rhp_poles_bound"),
            "nyquist_encirclements_cw": ny.get("encirclements_cw"), "nyquist_reason": ny.get("reason"),
            "nyquist_refinement_rounds": (ny.get("refinement") or {}).get("rounds"),
            "pz_status": pz.get("status"), "pz_P": pz.get("P"), "pz_reason": pz.get("reason"),
            "pz_validated": pz.get("validated"), "pz_conflict": st.get("pz_conflict"),
            "Z": st.get("Z"), "verdict": st.get("verdict"), "verdict_basis": st.get("verdict_basis"),
            "conditionally_stable": st.get("conditionally_stable"),
            "low_side_gain_margin_db": st.get("low_side_gain_margin_db"),
            "transient_status": tr.get("status"), "transient_reason": tr.get("reason"),
            "early_stop": tr.get("early_stop"),
            "limit_cycle_vs_slow_decay_unresolved": st.get("limit_cycle_vs_slow_decay_unresolved"),
            "reason": st.get("reason")}


def iso_summary(rows, meta):
    """iso(K3 판정): 단독 인스턴스를 만든 소자마다 |ID_rel| <= tol_ID_rel 인가. verdict = PASS(전부 안) / FAIL(하나라도 밖) /
    INCOMPLETE(ID 값·허용오차가 없는 소자, 또는 인스턴스를 못 만든 소자가 있음)."""
    skipped = meta.get("iso_skipped") or {}
    inside, outside, na = [], [], dict(skipped)
    for r in rows:
        if r["name"] in skipped:
            continue
        if r["ID_rel"] is None or r["tol_ID_rel"] is None:
            na[r["name"]] = "ID 값 없음" if r["ID_rel"] is None else "tol_ID_rel 없음"
        elif abs(r["ID_rel"]) <= r["tol_ID_rel"]:
            inside.append(r["name"])
        else:
            outside.append(r["name"])
    verdict = "FAIL" if outside else ("INCOMPLETE" if na or not inside else "PASS")
    return {"verdict": verdict, "within_tol": inside, "outside_tol": outside, "not_judged": na,
            "rule": "|ID_spice - ID_pred|/|ID_pred| <= tol_ID_rel (device_tolerance 규칙)"}


def forced_diagnosis(inp, rows, kcl):
    """forced 진단(기록만, C19).
    (1) 넷별 KCL: 고정원 전류 |i_hold| 대 그 넷에 드레인/소스가 물린 소자들의 tol_I = |ID_pred| x tol_ID_rel 합.
        허용오차가 없는 소자가 물린 넷은 판정 안 함(within None). dc_consistent = 판정한 넷이 전부 안이면 True,
        하나라도 밖이면 False, 판정한 넷이 없으면 None.
    (2) 게이트 공유 넷(게이트에 소자 2개 이상): 소자별 등가 dVGS = (ID_spice - ID_pred)/gm_pred(엔진이 의도한 동작점의 기울기 --
        SPICE 에서 꺼진 소자의 gm 으로 나누면 값이 발산한다)와 그 퍼짐(최대-최소)."""
    by = {r["name"]: r for r in rows}
    att = {}
    for d in inp["devices"]:
        if d["name"] in by:
            for t in ("drain", "source"):
                att.setdefault(d[t], set()).add(d["name"])
    nets, exceed, judged = [], [], 0
    for k in kcl:
        devs = sorted(att.get(k["net"], ()))
        tols = [None if by[n]["ID_pred"] is None or by[n]["tol_ID_rel"] is None
                else abs(by[n]["ID_pred"]) * by[n]["tol_ID_rel"] for n in devs]
        i = k["hold_current_A"]
        if i is None or not devs or any(t is None for t in tols):
            nets.append({"net": k["net"], "hold_current_A": i, "devices": devs, "tol_I_sum_A": None, "within": None})
            continue
        tsum = sum(tols)
        ok = abs(i) <= tsum
        judged += 1
        if not ok:
            exceed.append(k["net"])
        nets.append({"net": k["net"], "hold_current_A": i, "devices": devs, "tol_I_sum_A": tsum, "within": ok})
    gates = {}
    for d in inp["devices"]:
        if d["name"] in by:
            gates.setdefault(d["gate"], []).append(d["name"])
    shared = []
    for g, devs in sorted(gates.items()):
        if len(devs) < 2:
            continue
        dv = {}
        for n in devs:
            r = by[n]
            dv[n] = (None if r["ID_spice"] is None or r["ID_pred"] is None or not r["gm_pred"]
                     else (r["ID_spice"] - r["ID_pred"]) / r["gm_pred"])
        vals = [v for v in dv.values() if v is not None]
        shared.append({"net": g, "dVGS_eq_V": dv, "spread_V": (max(vals) - min(vals)) if len(vals) >= 2 else None})
    shared.sort(key=lambda x: -(x["spread_V"] or 0))
    return {"kcl_nets": nets, "kcl_nets_judged": judged, "kcl_nets_exceeding": exceed,
            "dc_consistent": None if judged == 0 else not exceed, "gate_shared_nets": shared,
            "rule": "넷별 |i_hold| <= sum(|ID_pred| x tol_ID_rel) (드레인/소스가 그 넷에 물린 소자); dVGS_eq = dID/gm_pred"}


def diagnose(free_res, forced_res):
    """free FAIL 원인 분류(기록만, C19). 반환 dict(classification, reason, ...).
    - free 가 FAIL 이 아니면 'not_applicable'.
    - forced 결과가 없거나 막힘이면 'unknown'(분류 불가).
    - forced dc_consistent True  -> 'boundary_condition'(엔진 DC 정합, free 수렴·고임피던스 노드·경계조건 쪽)
    - forced dc_consistent False -> 'engine_dc_inconsistent'(엔진 DC 비정합 -- 엔진 쪽 결함)
    - dc_consistent None(허용오차 없음 등)이면 'unknown'."""
    fv = ((free_res or {}).get("summary") or {}).get("verdict")
    if fv != "FAIL":
        return {"classification": "not_applicable", "reason": f"free verdict {fv} -- FAIL 일 때만 분류"}
    if not forced_res or forced_res.get("blockers") or "diagnosis" not in forced_res:
        return {"classification": "unknown", "reason": "forced 결과 없음 또는 막힘 -- 분류 불가(--bias free forced 로 함께 실행)"}
    dg = forced_res["diagnosis"]
    out = {"forced_kcl_nets_exceeding": dg["kcl_nets_exceeding"], "forced_kcl_nets_judged": dg["kcl_nets_judged"],
           "gate_shared_max_spread": (dg["gate_shared_nets"][0] if dg["gate_shared_nets"] else None)}
    if dg["dc_consistent"] is True:
        out.update(classification="boundary_condition",
                   reason="forced KCL 잔차가 판정한 모든 넷에서 소자 tol_I 합 안 -- 엔진 DC 는 정합, free 수렴·경계조건 쪽 문제")
    elif dg["dc_consistent"] is False:
        out.update(classification="engine_dc_inconsistent",
                   reason=f"forced KCL 잔차가 tol_I 합을 넘는 넷 {dg['kcl_nets_exceeding']} -- 엔진 DC 비정합")
    else:
        out.update(classification="unknown", reason="판정 가능한 forced KCL 넷이 없다(소자 허용오차 없음 등)")
    return out


def _f(v, f="{:.4g}"):
    if v is None:
        return "-"
    if isinstance(v, str):
        return v
    return f.format(v)


def to_markdown(res):
    s = res["summary"]
    L = [f"### {res['circuit']} -- 엔진 예측 vs SPICE (bias={res['bias']})"]
    lcu = (s.get("stability") or {}).get("limit_cycle_vs_slow_decay_unresolved")
    if lcu:   # 보고 맨 앞(사용자 결정 4): FAIL 이 판정 한계에서 나왔을 수 있다는 표시
        L.append(f"- **limit_cycle_vs_slow_decay_unresolved**: 창 최댓값 M = {[_f(x) for x in lcu.get('M') or []]}, "
                 f"창당 변화비 = {[_f(x) for x in lcu.get('window_ratios') or []]} -- {lcu.get('reason')}")
    for w in s.get("warnings") or []:
        L.append(f"- **경고(forced)**: {w}")
    rc = s["record_counts"]
    L += [f"- 판정: **{s['verdict']}** -- {s['verdict_reason']}",
         f"- 기록용 비교(판정 무관): 허용오차 안 {rc['PASS']}, 밖 {rc['FAIL']}, N/A {rc['N/A']}",
         f"- 모델 코너/온도(LUT npz 메타): {res['lut_meta'].get('corner')}, {res['lut_meta'].get('temp_c')} C",
         f"- 판정 설정: {json.dumps(res['judge_config'], ensure_ascii=False)}",
         (f"- SPICE 포화 소자 {s['sat_in_spice']}/{s['devices']}, 포화 아님: {', '.join(s['not_sat']) or '-'}"
          if s["sat_in_spice"] is not None else "- 포화 판정: sat_margin_V 미설정(포화 여유 값만 보고)")]
    ti = res.get("topology_identity") or {}
    L.append(f"- C15 topology 연결 동일성: **{ti.get('status', 'unverified')}**"
             + (f" (차이 {len(ti.get('diffs') or [])}건)" if ti.get("diffs") else "")
             + (f" -- {'; '.join(ti.get('notes') or [])}" if ti.get("notes") else ""))
    for dd in (ti.get("diffs") or [])[:20]:
        L.append(f"  - 차이: {dd}")
    for nm, why in (ti.get("declared_not_in_topology") or {}).items():
        L.append(f"  - 비교 제외(입력 선언): {nm} -- {why}")
    acc = s.get("acceptance") or {}
    if acc.get("off_in_spice") or acc.get("conduction_not_evaluated"):
        L.append(f"- C23 전도 확인: SPICE 에서 꺼짐 {acc.get('off_in_spice') or '-'}, "
                 f"판정 못 함 {acc.get('conduction_not_evaluated') or '-'}")
    jc = s.get("junction_capacitance") or {}
    L.append(f"- C22 접합 용량(확산 기하): 포함 {jc.get('included')} -- 출처 {jc.get('by_source')}"
             + (f", 없음 {jc['missing']}" if jc.get("missing") else ""))
    for rr in s.get("spice_ratio") or []:
        L.append(f"- C24 ratio_db @ {_f(rr.get('f_hz'))} Hz: {_f(rr.get('ratio_db'))} dB "
                 f"(|H_num| {_f((rr.get('num') or {}).get('mag'))}, |H_den| {_f((rr.get('den') or {}).get('mag'))})")
    for rr in s.get("spice_rout") or []:
        v = rr.get("view") or {}
        L.append(f"- C26 rout_ohm @ {_f(rr.get('f_hz'))} Hz ({v.get('sense_mode')} {v.get('sense_p')}"
                 + (f" - {v.get('sense_n')}" if v.get("sense_n") else "") + f"): {_f(rr.get('rout_ohm'))} Ohm "
                 f"(Re {_f(rr.get('re'))}, Im {_f(rr.get('im'))})"
                 + (f" -- 정의 불가 {rr['undefined']}" if rr.get("undefined") else ""))
    sac = s.get("spice_ac") or {}
    for d in sac.get("dc_path_isolation") or []:
        L.append(f"- C27 기록(판정 아님) 입력 {d['net']}: (2πf)²·L·C = {_f(d.get('omega2_LC'))} @ {_f(d.get('f_hz'))} Hz"
                 + (" (출력 DC 되먹임 경로)" if d.get("output_feedback") else ""))
    for d in sac.get("loop_choke_ratio") or []:
        L.append(f"- C27 기록(판정 아님) β 루프 절단 넷 {d['net']}: |jωL|/|Z_node| = {_f(d.get('ratio'))} @ {_f(d.get('f_hz'))} Hz")
    pl = s.get("pm_loop") or {}
    if pl.get("feedback_passives") or pl.get("feedback_passives_basis"):
        L.append(f"- PM 루프: {pl.get('pm_definition')}, feedback_passives {pl.get('feedback_passives')} "
                 f"(규칙 {pl.get('feedback_passives_basis') or '미기재'}), 절단 넷 {pl.get('loop_break_nets')}, "
                 f"가중 {pl.get('loop_weights')}")
    cl = s.get("cm_loop")
    if cl:
        cs = cl.get("stability") or {}
        L.append(f"- CM 루프(공통 모드 CMFB) PM: {_f(cl.get('pm_deg'))} deg"
                 + (f" (정의 불가 {cl['pm_undefined']}, Bode 식 원값 {_f(cl.get('pm_deg_raw'))})" if cl.get("pm_undefined") else "")
                 + f", 절단 넷 {cl.get('break_nets')}, T_cm(0) {_f(cl.get('loop_gain_dc_db'))} dB, UGF {_f(cl.get('loop_ugf_hz'))} Hz"
                 + f", Nyquist N = {_f(cs.get('nyquist_encirclements_cw'))}, 폐루프 과도 {cs.get('transient_status')}")
    sb = s.get("stability") or {}
    if sb:
        L.append(f"- C10 PM 안정성 근거: PM {'유효' if sb.get('pm_valid') else ('정의 불가 ' + str(sb.get('pm_undefined')) if sb.get('pm_undefined') else '검사 대상 아님')}"
                 f" (Bode 식 원값 {_f(sb.get('pm_deg_raw'))} deg) -- Nyquist 시계 방향 감은 수 N = {_f(sb.get('nyquist_encirclements_cw'))}"
                 + (f"({sb['nyquist_reason']})" if sb.get("nyquist_reason") else "")
                 + f", 폐루프 과도 {sb.get('transient_status')}, 개루프 RHP 극 {_f(sb.get('open_loop_rhp_poles'))}"
                 + (f" ({sb['open_loop_rhp_poles_bound']})" if sb.get("open_loop_rhp_poles_bound") else "")
                 + f"; .pz P = {_f(sb.get('pz_P'))}({sb.get('pz_status')}{', 개루프 과도 확인 ' + str(sb['pz_validated']) if sb.get('pz_validated') is not None else ''}), Z = N + P = {_f(sb.get('Z'))}"
                 + (f" [.pz 무시: {sb['pz_conflict']}]" if sb.get("pz_conflict") else "")
                 + f" -> 안정성 판정 **{sb.get('verdict')}**({sb.get('verdict_basis')})"
                 + (" [조건부 안정" + (f", 하측 이득 여유 {_f(sb.get('low_side_gain_margin_db'))} dB" if sb.get("low_side_gain_margin_db") is not None else "") + "]"
                    if sb.get("conditionally_stable") else "")
                 + (f", 조기 종결 창 {sb['early_stop']['window']}({sb['early_stop'].get('kind')})" if sb.get("early_stop") else ""))
    u6 = s.get("u6") or {}
    nzr = u6.get("noise")
    if nzr:
        ol, cl_ = nzr.get("open_loop") or {}, nzr.get("closed_loop") or {}
        L.append(f"- U6 .noise 개루프: {ol.get('status')} -- 열잡음 입력환산 {_f(ol.get('th_in_v2hz'))} V²/Hz (f = {_f(ol.get('f_eval_hz'))} Hz), "
                 f"flicker 코너 {_f(ol.get('fc_in_hz'))} Hz{('(' + ol['fc_reason'] + ')') if ol.get('fc_reason') else ''}, "
                 f"excess {_f(ol.get('excess_th'))}" + (f" -- {ol['reason']}" if ol.get("reason") else ""))
        if nzr.get("closed_loop") is not None:
            L.append(f"- U6 .noise 폐루프 적분 출력 잡음: {_f(cl_.get('out_int_vrms'))} Vrms ([{_f(cl_.get('f_lo_hz'))}, {_f(cl_.get('f_hi_hz'))}] Hz, "
                     f"꼬리 수렴 {cl_.get('converged')}, 스위치 kT/C {((cl_.get('ktc_sampling') or {}).get('status'))})"
                     + (f" -- {cl_['reason']}" if cl_.get("reason") else ""))
    mc = u6.get("offset_mc")
    if mc:
        L.append(f"- U6 offset Monte-Carlo: {mc.get('status')} -- σ_in = {_f(mc.get('sigma_in_mV'))} mV (표본 {mc.get('n_samples')}, "
                 f"목표 상대 표준오차 {_f(mc.get('rel_resolution'))}, 평균 {_f(mc.get('mean_in_mV'))} mV, 시드 {mc.get('seed')})"
                 + (f" -- {mc['reason']}" if mc.get("reason") else ""))
    sw = u6.get("swing_icmr")
    if sw:
        L.append(f"- U6 스윙·ICMR: {sw.get('status')} -- swing_out_v {_f(sw.get('swing_out_v'))} V, icmr_v {_f(sw.get('icmr_v'))} V, "
                 f"icm_margin_v {_f(sw.get('icm_margin_v'))} V (포화 여유 {_f(sw.get('margin_V'))} V, ngspice {sw.get('ngspice_runs')} 회)"
                 + (f" -- {sw['reason']}" if sw.get("reason") else ""))
    tr = s.get("transient") or {}
    if tr:
        L.append(f"- C25 슬루·정착: {tr.get('status')} -- {tr.get('reason')}")
    if s.get("z1"):
        L.append(f"- Z1 제거법 진단 실행: omit={s['z1']['omit']} short={s['z1']['short']}")
    if s.get("iso"):
        iso = s["iso"]
        L.append(f"- iso(단독 소자, K3): **{iso['verdict']}** -- 허용오차 안 {len(iso['within_tol'])}, 밖 {iso['outside_tol']}, "
                 f"판정 못 함 {iso['not_judged']}")
    if res.get("diagnosis_free"):
        dgf = res["diagnosis_free"]
        L.append(f"- 진단(free FAIL 원인): {dgf['classification']} -- {dgf['reason']}")
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
    if ac.get("pm_crosscheck_deg") is not None or ac.get("pm_crosscheck_note"):
        L.append(f"| (참고) PM 교차 측정(폐루프 peaking 역산, 기록만) deg / peaking dB | | "
                 f"{_f(ac.get('pm_crosscheck_deg'))} / {_f(ac.get('closed_loop_peaking_db'))} | "
                 f"{_f(ac.get('pm_crosscheck_gap_deg'), '{:+.3g}')} | {ac.get('pm_crosscheck_note') or ''} |")
    for c in res["constraints"]:
        L.append(f"| 제약 {c.get('name', '')}: {c['measure']} {c['op']} {_f(c.get('limit'))} | | {_f(c['spice'])} | | {c['judge']} |")
    if res["kcl_residual"]:
        L += ["", "| forced 고정원 전류(KCL 잔차) 넷 | uA | 판정 |", "|---|---|---|"]
        for k in res["kcl_residual"]:
            L.append(f"| {k['net']} | {_f(None if k['hold_current_A'] is None else k['hold_current_A'] * 1e6)} | {k['judge']} |")
    dg = res.get("diagnosis")
    if dg:
        L += ["", f"- forced 진단: dc_consistent={dg['dc_consistent']} (판정 넷 {dg['kcl_nets_judged']}, 넘는 넷 {dg['kcl_nets_exceeding']})"]
        if dg["gate_shared_nets"]:
            L += ["", "| 게이트 공유 넷 | 등가 dVGS 퍼짐 mV | 소자별 dVGS_eq mV |", "|---|---|---|"]
            for gsn in dg["gate_shared_nets"]:
                L.append(f"| {gsn['net']} | {_f(None if gsn['spread_V'] is None else gsn['spread_V'] * 1e3)} | "
                         + ", ".join(f"{k}={_f(None if v is None else v * 1e3, '{:+.3g}')}" for k, v in gsn["dVGS_eq_V"].items())
                         + " |")
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
    ap.add_argument("--forced-compare", default=None,
                    help="[신규] 같은 입력의 forced compare.json -- free 결과에 diagnosis_free(C19)를 붙인다")
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
    if a.forced_compare and res["bias"] == "free":
        with open(a.forced_compare, encoding="utf-8") as f:
            res["diagnosis_free"] = diagnose(res, json.load(f))
    with open(a.out_prefix + ".compare.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    with open(a.out_prefix + ".compare.md", "w", encoding="utf-8") as f:
        f.write(to_markdown(res))
    print("verdict:", res["summary"]["verdict"], "--", res["summary"]["verdict_reason"])
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
