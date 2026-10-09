"""`ls_swing` -- 설계 40 §3.8-8 `swing_out_v`·`icmr_v`·`icm_margin_v`, 41 §4.6(J-E), 체크리스트 D-SW·D-ICM·D-J5, 계획 N3.8 경로 합,
metrics CONTRACT 10.5.

규칙(계약 10.5·10.9 (1)): 채널 엣지 NMOS V_d − V_s ≥ sat, PMOS V_s − V_d ≥ sat(`linear` 제외), VGS 엣지 V_g − V_s = polarity·|VGS| 는
source 가 레일이 아닌 소자와 diode(g = d)에만, 모든 노드 [rail_min, rail_max], 단일 swing = 2·min 반폭, 차동 출력 쌍 = 4·min 반폭,
icmr = min hi − max lo(빈 창 음수), margin = min(V_icm − lo, hi − V_icm), 입력 DC 미선언이면 V_icm = 해의 입력 넷 전압 + `required_input_cm_v`.

oracle:
* (a) 손 toy 경로 합(이 파일 각 test docstring 에 산수) -- 작성자 toy 와 다른 수치로 다시 유도.
* (b) 같은 차분 제약계를 scipy `linprog`(HiGHS 선형계획)으로 노드마다 min/max -- Bellman–Ford 와 다른 방법.
* ngspice `.dc` 대조는 하지 않았다: `SatDevice` 의 sat·|VGS| 는 봉인 점에서 고정된 입력값이라 소자 모델 스윕(점마다 VDSAT 이 바뀐다)과
  같은 양이 아니다(계약 10.9 (2) '선형화와 경로 합 차이' -- 판정은 오라클 D-OR5 몫).
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.optimize import linprog

from gmid_engine.metrics import SatDevice, SwingIcmr, ls_swing

from .conftest import codes

RAILS = (("gnd", 0.0), ("vdd", 1.8))


def n(label, d, g, s, vgs, sat, **kw):
    return SatDevice(label, 1, d, g, s, vgs, sat, **kw)


def p(label, d, g, s, vgs, sat, **kw):
    return SatDevice(label, -1, d, g, s, vgs, sat, **kw)


def lp_bounds(devices, rails, nets):
    """(b) 독립 선형계획: 같은 제약을 손으로 다시 적어 노드마다 min·max."""
    names = sorted(set(nets) | {x for m in devices for x in (m.d, m.g, m.s)} | {r for r, _ in rails})
    idx = {k: i for i, k in enumerate(names)}
    rail = dict(rails)
    lo_r, hi_r = min(rail.values()), max(rail.values())
    a_ub, b_ub, a_eq, b_eq = [], [], [], []
    for m in devices:
        if not m.linear:
            row = np.zeros(len(names))
            hi_net, lo_net = (m.d, m.s) if m.polarity > 0 else (m.s, m.d)
            row[idx[lo_net]], row[idx[hi_net]] = 1.0, -1.0          # V_lo − V_hi ≤ −sat
            a_ub.append(row)
            b_ub.append(-m.sat_v)
        if m.s not in rail or m.g == m.d:
            row = np.zeros(len(names))
            row[idx[m.g]], row[idx[m.s]] = 1.0, -1.0
            a_eq.append(row)
            b_eq.append(m.polarity * m.vgs_v)
    bounds = [(rail[k], rail[k]) if k in rail else (lo_r, hi_r) for k in names]
    out = {}
    for k in nets:
        c = np.zeros(len(names))
        c[idx[k]] = 1.0
        kw = dict(A_ub=np.array(a_ub) if a_ub else None, b_ub=b_ub or None, A_eq=np.array(a_eq) if a_eq else None,
                  b_eq=b_eq or None, bounds=bounds, method="highs")
        lo = linprog(c, **kw)
        hi = linprog(-c, **kw)
        out[k] = (lo.fun if lo.status == 0 else None, -hi.fun if hi.status == 0 else None)
    return out


def bounds_of(got):
    return {k: (lo, hi) for k, lo, hi in got.bounds}


# ---------------------------------------------------------------- (a) 손 toy

CS = (n("M1", "out", "in", "gnd", 0.6, 0.15), p("M2", "out", "vbp", "vdd", 0.7, 0.3))


def test_cs_current_source_load():
    """CS + PMOS 전류원: out ∈ [0.15, 1.8 − 0.3 = 1.5], V_o = 1.0 -> 반폭 min(0.5, 0.85) = 0.5 -> swing 1.0.
    입력 in 은 gate 뿐(소스 레일·diode 아님 -> VGS 엣지 없음): 창 [0, 1.8], icmr 1.8, 선언 V_icm 0.6 -> margin 0.6."""
    got = ls_swing(CS, RAILS, (("out", 1.0), ("in", 0.6)), ("out",), ("in",), False, 0.6)
    assert isinstance(got, SwingIcmr) and got.undefined == ()
    assert got.swing_out_v == pytest.approx(1.0, abs=1e-12)
    assert got.out_ranges == (("out", pytest.approx(0.15), pytest.approx(1.5), 1.0),)
    assert got.icmr_v == pytest.approx(1.8, abs=1e-12) and got.window == (0.0, 1.8)
    assert got.icm_margin_v == pytest.approx(0.6, abs=1e-12)
    assert got.input_dc == "declared" and got.required_input_cm_v is None and got.v_icm == 0.6


def test_cascode_raises_low_bound():
    """캐스코드 Mc(d out, g vb, s x; VGS 0.7, sat 0.25) 위 입력 M1(d x, sat 0.2): x ≥ 0.2, out ≥ x + 0.25 ≥ 0.45;
    vb = x + 0.7 ≤ 1.8 -> x ≤ 1.1, vb ≥ 0.9. 부하 PMOS sat 0.3 -> out ≤ 1.5. V_o 0.9 -> 반폭 min(0.6, 0.45) -> swing 0.9."""
    devs = (n("M1", "x", "in", "gnd", 0.6, 0.2), n("Mc", "out", "vb", "x", 0.7, 0.25), p("Ml", "out", "vbp", "vdd", 0.7, 0.3))
    got = ls_swing(devs, RAILS, (("out", 0.9), ("in", 0.6)), ("out",), ("in",), False, 0.6)
    b = bounds_of(got)
    assert b["out"] == (pytest.approx(0.45), pytest.approx(1.5))
    assert b["x"] == (pytest.approx(0.2), pytest.approx(1.1))
    assert b["vb"] == (pytest.approx(0.9), pytest.approx(1.8))
    assert got.swing_out_v == pytest.approx(0.9, abs=1e-12)


def test_nmos_follower_and_input_window():
    """NMOS follower M1(d vdd, g in, s out; VGS 0.55, sat 0.2) + 싱크 M2(sat 0.12): out ≥ 0.12, out ≤ 1.8 − 0.55 = 1.25
    (gate 상한이 레일) 과 ≤ 1.8 − 0.2 = 1.6 중 1.25. 입력 in = out + 0.55 ∈ [0.67, 1.8] -> icmr 1.13.
    V_o 0.7 -> 반폭 min(0.55, 0.58) -> swing 1.1. 입력 DC 미선언(SP-2 대기): V_icm = 봉인 해 in 전압 1.25 ->
    margin min(1.25 − 0.67, 1.8 − 1.25) = 0.55, required_input_cm_v = (1.25, 0.67, 1.8), input_dc pending."""
    devs = (n("M1", "vdd", "in", "out", 0.55, 0.2), n("M2", "out", "vb", "gnd", 0.6, 0.12))
    got = ls_swing(devs, RAILS, (("out", 0.7), ("in", 1.25)), ("out",), ("in",))
    assert got.out_ranges[0][1:3] == (pytest.approx(0.12), pytest.approx(1.25))
    assert got.swing_out_v == pytest.approx(1.1, abs=1e-12)
    assert got.window == (pytest.approx(0.67), pytest.approx(1.8))
    assert got.icmr_v == pytest.approx(1.13, abs=1e-12)
    assert got.icm_margin_v == pytest.approx(0.55, abs=1e-12)
    assert got.input_dc == "pending"
    assert got.v_icm == 1.25
    assert got.required_input_cm_v == (1.25, pytest.approx(0.67), pytest.approx(1.8))


def test_differential_pair_four_times_min_half_width():
    """차동쌍 M1/M2(s t; VGS 0.65, sat 0.15), 꼬리 M3(d t, sat 0.2), PMOS 부하(sat 0.25): t ≥ 0.2, out ≥ t + 0.15 ≥ 0.35,
    out ≤ 1.55. 입력 = t + 0.65 ≥ 0.85, t ≤ min(1.8 − 0.65, 1.55 − 0.15) = 1.15 -> 입력 ≤ 1.8. 출력 DC 0.95/0.9 ->
    반폭 min(0.6, 0.55) = 0.55 -> 차동 4·0.55 = 2.2. icmr = 1.8 − 0.85 = 0.95."""
    devs = (n("M1", "om", "ip", "t", 0.65, 0.15), n("M2", "op", "im", "t", 0.65, 0.15), n("M3", "t", "vb", "gnd", 0.6, 0.2),
            p("M4", "om", "vbp", "vdd", 0.7, 0.25), p("M5", "op", "vbp", "vdd", 0.7, 0.25))
    nv = (("om", 0.95), ("op", 0.9), ("ip", 1.0), ("im", 1.0))
    got = ls_swing(devs, RAILS, nv, ("op", "om"), ("ip", "im"), True, 1.0)
    assert got.swing_out_v == pytest.approx(2.2, abs=1e-12)
    assert got.icmr_v == pytest.approx(0.95, abs=1e-12)
    assert got.icm_margin_v == pytest.approx(0.15, abs=1e-12)                 # min(1.0 − 0.85, 1.8 − 1.0)
    single = ls_swing(devs, RAILS, nv, ("op", "om"), ("ip", "im"), False, 1.0)
    assert single.swing_out_v == pytest.approx(1.1, abs=1e-12)                # 차동 표지 없으면 2·min


def test_two_polarity_input_empty_window_negative():
    """두 극성 입력이 같은 gate(파일럿 입력단 모양): NMOS M1(d a, g in, s tn; VGS 0.7) + 싱크(sat 0.5) -> in ≥ 1.2,
    PMOS M2(d b, g in, s tp; |VGS| 0.7) + 소스(sat 0.5) -> tp ≤ 1.3, in = tp − 0.7 ≤ 0.6 -> 창 [1.2, 0.6], icmr −0.6(음수 그대로)."""
    devs = (n("M1", "a", "in", "tn", 0.7, 0.1), n("Mn", "tn", "vbn", "gnd", 0.6, 0.5),
            p("M2", "b", "in", "tp", 0.7, 0.1), p("Mp", "tp", "vbp", "vdd", 0.7, 0.5))
    got = ls_swing(devs, RAILS, (("a", 0.9), ("in", 0.9)), ("a",), ("in",), False, 0.9)
    assert got.window == (pytest.approx(1.2), pytest.approx(0.6))
    assert got.icmr_v == pytest.approx(-0.6, abs=1e-12)
    assert got.icm_margin_v == pytest.approx(-0.3, abs=1e-12)


def test_linear_device_has_no_channel_edge():
    devs = (n("M1", "out", "in", "gnd", 0.6, 0.15, linear=True), p("M2", "out", "vbp", "vdd", 0.7, 0.3))
    got = ls_swing(devs, RAILS, (("out", 1.0), ("in", 0.6)), ("out",), ("in",), False, 0.6)
    assert got.out_ranges[0][1] == pytest.approx(0.0, abs=1e-15)                # 하한 = 레일
    assert got.swing_out_v == pytest.approx(1.0, abs=1e-12)                     # min(0.5, 1.0)·2


def test_resolution_follows_binding_side():
    """분해능 = 구속 쪽 엣지 허용오차 누적(계약 10.5): CS toy 에서 위쪽(0.5) 이 구속 -> M2 sat_tol 0.02 -> swing_res 2·0.02.
    입력 창은 레일뿐이라 icmr 누적 0."""
    devs = (n("M1", "out", "in", "gnd", 0.6, 0.15, sat_tol_v=0.01), p("M2", "out", "vbp", "vdd", 0.7, 0.3, sat_tol_v=0.02))
    got = ls_swing(devs, RAILS, (("out", 1.0), ("in", 0.6)), ("out",), ("in",), False, 0.6)
    assert got.swing_resolution == pytest.approx(0.04, abs=1e-15)
    assert got.icmr_resolution == pytest.approx(0.0, abs=1e-15)
    follower = (n("M1", "vdd", "in", "out", 0.55, 0.2, sat_tol_v=0.01, vgs_tol_v=0.03),
                n("M2", "out", "vb", "gnd", 0.6, 0.12, sat_tol_v=0.005))
    got = ls_swing(follower, RAILS, (("out", 0.7), ("in", 1.25)), ("out",), ("in",))
    assert got.icmr_resolution == pytest.approx(0.005 + 0.03, abs=1e-15)       # in 하한 = 싱크 sat + VGS, 상한 = 레일
    missing = (n("M1", "out", "in", "gnd", 0.6, 0.15), p("M2", "out", "vbp", "vdd", 0.7, 0.3, sat_tol_v=0.02))
    assert ls_swing(missing, RAILS, (("out", 1.0), ("in", 0.6)), ("out",), ("in",), False, 0.6).swing_resolution is not None
    lo_bound = (n("M1", "out", "in", "gnd", 0.6, 0.15), p("M2", "out", "vbp", "vdd", 0.7, 0.3, sat_tol_v=0.02))
    assert ls_swing(lo_bound, RAILS, (("out", 0.3), ("in", 0.6)), ("out",), ("in",), False, 0.6).swing_resolution is None


# ---------------------------------------------------------------- (b) 선형계획 대조

TOYS = {
    "cs": (CS, ("out", "in")),
    "cascode": ((n("M1", "x", "in", "gnd", 0.6, 0.2), n("Mc", "out", "vb", "x", 0.7, 0.25), p("Ml", "out", "vbp", "vdd", 0.7, 0.3)),
                ("out", "x", "vb", "in")),
    "follower_stack": ((n("M1", "vdd", "in", "a", 0.55, 0.2), p("M2", "gnd", "a", "b", 0.62, 0.18), n("M3", "b", "vbn", "gnd", 0.6, 0.11),
                        p("M4", "a", "vbp", "vdd", 0.7, 0.21)), ("a", "b", "in")),
    "telescopic": ((n("M1", "x1", "ip", "t", 0.65, 0.12), n("M2", "x2", "im", "t", 0.65, 0.12), n("Mt", "t", "vb", "gnd", 0.6, 0.2),
                    n("Mc1", "om", "vc", "x1", 0.7, 0.13), n("Mc2", "op", "vc", "x2", 0.7, 0.13),
                    p("Mp1", "om", "vbp", "vdd", 0.7, 0.22), p("Mp2", "op", "vbp", "vdd", 0.7, 0.22)),
                   ("om", "op", "x1", "t", "vc", "ip")),
}


@pytest.mark.parametrize("name", sorted(TOYS))
def test_bounds_match_linear_program(name):
    devs, nets = TOYS[name]
    nv = tuple((k, 0.9) for k in nets)
    got = ls_swing(devs, RAILS, nv, (nets[0],), (nets[-1],), False, 0.9)
    ref = lp_bounds(devs, RAILS, nets)
    b = bounds_of(got)
    for k in nets:
        assert b[k][0] == pytest.approx(ref[k][0], abs=1e-12), (k, b[k], ref[k])
        assert b[k][1] == pytest.approx(ref[k][1], abs=1e-12), (k, b[k], ref[k])


# ---------------------------------------------------------------- 정의 불가·불변

def test_undefined_codes_shared_by_three_metrics():
    for args, want in (((CS, RAILS, (("out", 1.0),), (), ("in",)), "no_output_port"),
                       ((CS, RAILS, (("out", 1.0),), ("out",), ()), "no_input_port"),
                       (((n("M1", "out", "in", "gnd", 0.6, None),), RAILS, (("out", 1.0), ("in", 0.6)), ("out",), ("in",)),
                        "sat_unavailable"),
                       ((CS, RAILS, (("out", 1.0),), ("out",), ("in",)), "node_v_missing")):
        got = ls_swing(*args)
        assert (got.swing_out_v, got.icmr_v, got.icm_margin_v) == (None, None, None)
        assert {(u.quantity, u.code) for u in got.undefined} == {(q, want) for q in ("swing_out_v", "icmr_v", "icm_margin_v")}


def test_sat_unavailable_ignored_for_linear_device():
    devs = (n("M1", "out", "in", "gnd", 0.6, None, linear=True), p("M2", "out", "vbp", "vdd", 0.7, 0.3))
    assert ls_swing(devs, RAILS, (("out", 1.0), ("in", 0.6)), ("out",), ("in",), False, 0.6).undefined == ()


def test_name_bijection_and_order_invariance():
    devs, _ = TOYS["telescopic"]
    nv = (("om", 1.0), ("op", 1.0), ("ip", 1.1), ("im", 1.1))
    a = ls_swing(devs, RAILS, nv, ("op", "om"), ("ip", "im"), True, 1.1)
    m = {"om": "q9", "op": "a1", "ip": "zz", "im": "b0", "x1": "c", "x2": "y", "t": "k", "vb": "e", "vc": "f", "vbp": "g",
         "gnd": "rail_lo", "vdd": "rail_hi"}
    devs2 = tuple(SatDevice("D" + str(i), d.polarity, m[d.d], m[d.g], m[d.s], d.vgs_v, d.sat_v) for i, d in enumerate(reversed(devs)))
    b = ls_swing(devs2, (("rail_hi", 1.8), ("rail_lo", 0.0)), tuple((m[k], v) for k, v in reversed(nv)), ("a1", "q9"),
                 ("zz", "b0"), True, 1.1)
    assert (b.swing_out_v, b.icmr_v, b.icm_margin_v) == pytest.approx((a.swing_out_v, a.icmr_v, a.icm_margin_v), abs=1e-12)


def test_deterministic():
    devs, _ = TOYS["telescopic"]
    args = (devs, RAILS, (("om", 1.0), ("op", 1.0), ("ip", 1.1), ("im", 1.1)), ("op", "om"), ("ip", "im"), True)
    assert ls_swing(*args) == ls_swing(*args)
