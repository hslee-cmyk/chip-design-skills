"""`sizing/kernel_run.py` (U4) -- 평가 커널 본체의 새 입력 두 개: S2p 기반 tol_I(계획 N3.6, 설계 40 §3.7-3, CONTRACT 14.2)와
W_request 고정 W(설계 40 §3.7 머리 'W_request가 있으면 그 소자의 W는 고정 입력', 계획 N3.5 ⑤·N3.17 LY3, D-GB7d, CONTRACT 14.3),
그리고 IC10(캐시 키가 바뀐 입력을 덮는다, 설계 40 §10.3)·결정론(CONTRACT 9절).

oracle:
- (a) 손계산 -- r4 toy LUT(conftest: ln IDu = ln I0 + B·VGS − C·VGS²/2 + LAM·VDS + VS 항, gm/ID = B − C·VGS)의 닫힌 식.
  예: 'W 고정 쓰기 소자의 좌표 = ln(ID·L/W)' 는 정의(CONTRACT 14.3·계획 N3.17 LY3)를 r4 식에 넣어 VGS 를 닫힌 식으로 푼다.
- (a) 구성으로 정답이 정해진 입력 -- S2p parent 는 test 가 손으로 쓴 `ss_dev`(gm = 그 점의 gm/ID × ID, conftest `with_hand_ss`).
  기대 gm 상한 = 손으로 쓴 gm(계획 N3.6 'gm 은 직전 봉인 스냅샷(S2p)의 ss 값').
- 피검 함수(`size_and_seal`·`dc_tolerances`·`previous_gm_id`·`normalize_w_request`)로 기대값을 만들지 않는다. 스냅샷에서 읽는 값은
  피검 결과(대조 대상)이거나 피검 블록의 입력(예: parent 의 dc_op·dc_tol_v)뿐이다.
"""
import json
import math
import os
import subprocess
import sys

import pytest

from gmid_engine import sizing as S
from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, SealViolationError
from gmid_engine.sizing import size_and_seal
from gmid_engine.sizing.kernel_run import normalize_w_request, previous_gm_id

from .conftest import (B, C, EPS, HERE, I0, LAM, SKILL_DIR, W_M, build_ctx, build_ctx_u4, circuit_cs_res, circuit_mirror,
                       detail, node_voltages, r4_ln_idu, r4_vgs_of, rel_close, theta_c, theta_mirror, theta_r4c, two,
                       with_hand_ss)

EVAL13 = (S.dc_currents, S.dc_lengths, S.dc_columns, S.dc_widths, S.dc_tolerances, S.dc_seal_node_conflict,
          S.dc_seal_vgs_match, S.dc_seal_kcl, S.dc_seal_bulk_reverse, S.dc_seal_saturation, S.dc_seal_kvl_branch,
          S.dc_seal_conduction, S.dc_seal_report)


def reset():
    for b in EVAL13:
        b.reset_stats()


def computes():
    return {b.name: b.stats().computes for b in EVAL13}


def ops(ev):
    return dict(ev.snapshot.column("device", "dc_op"))


def gm_bound(ev):
    return dict(ev.snapshot.column("device", "dc_gm_bound"))


def same_dc(a, b):
    """두 평가의 DC 결과(노드전압·소자 op·허용오차·봉인 보고)가 같다. parent 에 손 ss 를 쓴 스냅샷은 지문이 다르므로 지문 대신 쓴다."""
    for kind, field in (("node", "dc_v"), ("device", "dc_op"), ("device", "dc_tol_v"), ("device", "dc_gm_bound")):
        if a.snapshot.column(kind, field) != b.snapshot.column(kind, field):
            return False
    return a.report == b.report


def r4_grid_max_gm(kind, L, W, vds, vsb):
    """첫 평가의 gm 상한(계획 N3.6 '첫 평가는 LUT 격자 최댓값', CONTRACT 6절 tol 행 max(gm_id_curve 의 id·gm/id)·W/w_m) --
    r4 toy 의 닫힌 식을 VGS 격자 위에서 직접 최대화(vsb = 0 격자점, VDS 방향 1차라 보간 정확)."""
    from .conftest import R4_VGS
    return max(math.exp(math.log(W / L) + r4_ln_idu(kind, v, vds, vsb)) * (B - C * v) for v in R4_VGS)


@pytest.fixture(scope="module")
def mir(tmp_path_factory, r4_access):
    """circuit_mirror(r4 toy, I1 = 10 µA 선언) KernelContext. M1 diode·M3 writer, M2 dependent(parallel_vgs, 짝 M1)."""
    return build_ctx_u4(tmp_path_factory.mktemp("u4_mir"), circuit_mirror(), r4_access, element_values=(("I1", 1e-5),))[1]


@pytest.fixture(scope="module")
def sealed_c(ctx_r4c):
    """회로 C(r4) 의 봉인 점(1~9 pass)과 그 S2p parent(손 ss_dev)."""
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    assert e0.sealed is not None                                          # 전제(test_seal.py 와 같은 θ)
    return e0, with_hand_ss(e0)


# ===========================================================================
# S2p 기반 tol_I (계획 N3.6, 설계 40 §3.7-3, D-GB7 tol_I 행)
# ===========================================================================

def test_first_evaluation_uses_lut_grid_max(ctx_r4c, sealed_c):
    """parent 가 없으면 gm 상한 = LUT 격자 최대 gm × W/w_m(계획 N3.6 '첫 평가는 LUT 격자 최댓값')."""
    e0, _ = sealed_c
    gb = gm_bound(e0)
    for m, o in ops(e0).items():
        assert rel_close(gb[m], r4_grid_max_gm(o.kind, o.L, o.W, o.vds, o.vsb), 1e-9), m


def test_s2p_gm_bound_is_parent_ss_gm(ctx_r4c, sealed_c):
    """봉인 parent(ss 있음)에서 좌표 하나만 바꾼 후보(전류 같음): gm 상한 = parent 의 ss gm(계획 N3.6 문언 그대로 -- 같은 전류라
    CONTRACT 14.2 의 'gm/ID_prev × 이번 ID' 와 같은 값). 격자 최대보다 훨씬 작다(봉인 3 이 실제로 판정하게 되는 이유)."""
    e0, parent = sealed_c
    e1 = size_and_seal(ctx_r4c, theta_r4c(v1=0.62), parent=parent)
    o0, o1 = ops(e0), ops(e1)
    assert o1["M1"] != o0["M1"] and all(o1[m].current == o0[m].current for m in o0)       # 전제: DC 점은 바뀌고 전류는 같음
    ss = dict(parent.snapshot.column("device", "ss_dev"))
    gb = gm_bound(e1)
    for m in o0:
        assert abs(gb[m] - ss[m].gm) <= 4 * EPS * ss[m].gm, (m, gb[m], ss[m].gm)
        assert gb[m] < 1e-3 * r4_grid_max_gm(o1[m].kind, o1[m].L, o1[m].W, o1[m].vds, o1[m].vsb)


def test_s2p_gm_bound_scales_with_candidate_current(ctx_r4c, sealed_c):
    """CONTRACT 14.2 주장: 전류가 바뀐 후보는 gm 상한 = parent 의 gm/ID × 이번 후보 ID(전류 2배 -> 2배). 손으로 쓴 ss 의
    gm/ID = op.gm_id 라 기대값 = op.gm_id(parent) × 2e-5."""
    e0, parent = sealed_c
    e2 = size_and_seal(ctx_r4c, theta_r4c(i2=2e-5), parent=parent)
    gb = gm_bound(e2)
    for m, o in ops(e0).items():
        assert ops(e2)[m].current == 2e-5
        assert rel_close(gb[m], o.gm_id * 2e-5, 8 * EPS), m


def test_unsealed_parent_falls_back_to_grid_max(ctx_c):
    """parent 가 봉인되지 않았으면(VDSAT 열 없는 toy -> 봉인 7 undefined) ss 가 있어도 쓰지 않는다 -> 격자 최대
    (계획 N3.6 'S2p = 직전 **봉인** 스냅샷'). 기대값 = conftest Oracle.gm_bound(toy 닫힌 식)."""
    from .conftest import Oracle
    ctx = ctx_c[2]
    e0 = size_and_seal(ctx, theta_c())
    assert e0.sealed is None                                               # 전제
    parent = with_hand_ss(e0)
    e1 = size_and_seal(ctx, theta_c(x1=Oracle.ln_idu("nmos", 0.62, 0.9, 0.0)), parent=parent)
    gb = gm_bound(e1)
    for m, o in ops(e1).items():
        assert rel_close(gb[m], Oracle.gm_bound(o.kind, o.L, o.vds, o.vsb, o.W), 1e-9), m


def test_stale_ss_field_not_used(ctx_r4c, sealed_c):
    """parent 의 ss gm/ID 가 그 점의 dc_op.gm_id 와 맞지 않으면(옛 점의 필드) 그 소자는 격자 최대로 -- 계획 N3.6 의 'S2p 의 ss'
    는 그 봉인 점의 값이어야 한다. M1 만 1.5 배로 어긋나게 쓰고 M2 는 정합."""
    e0, _ = sealed_c
    parent = with_hand_ss(e0, gm_scale={"M1": 1.5})
    e1 = size_and_seal(ctx_r4c, theta_r4c(v1=0.62), parent=parent)
    o1, gb = ops(e1), gm_bound(e1)
    assert rel_close(gb["M1"], r4_grid_max_gm("nmos", o1["M1"].L, o1["M1"].W, o1["M1"].vds, o1["M1"].vsb), 1e-9)
    assert rel_close(gb["M2"], ops(e0)["M2"].gm_id * ops(e0)["M2"].current, 8 * EPS)


def test_previous_gm_id_values(ctx_c, sealed_c):
    """`previous_gm_id`: 봉인 parent -> ((소자, ss.gm / dc_op.current), ...) 이름순; 미봉인·None -> ()."""
    e0, parent = sealed_c
    got = previous_gm_id(parent)
    assert [m for m, _ in got] == sorted(ops(e0))
    for m, g in got:
        assert rel_close(g, ops(e0)[m].gm_id, 4 * EPS)
    assert previous_gm_id(None) == ()
    assert previous_gm_id(with_hand_ss(size_and_seal(ctx_c[2], theta_c()))) == ()
    assert [m for m, _ in previous_gm_id(with_hand_ss(e0, gm_scale={"M2": 0.5}))] == ["M1"]


@pytest.fixture(scope="module")
def ctx_passive_r4(tmp_path_factory, r4_access):
    """회로 A(r4, M1 bulk gnd) + engine Rz(out, m)·Cz(m, gnd) -> θ ss_resistance·capacitance(CONTRACT 4.4 r5, DEC-92)."""
    doc = circuit_cs_res(bulk_m1="gnd")
    doc["topology_name"] = "u4_passive_r4"
    doc["passive_elements"] += [two("Rz", "resistor", "out", "m"), two("Cz", "capacitor", "m", "gnd")]
    return build_ctx(tmp_path_factory.mktemp("u4_pas"), doc, r4_access,
                     element_values=(("Cz", None), ("R1", None), ("Rz", None)), engine_elements=("Cz", "Rz"))[2]


def theta_passive_r4(vgs=0.6, cz=1e-12, rz=1e4, i=1e-5, r=9e4):
    return {("L", "M1"): 1e-6, ("ln_idu", "M1"): r4_ln_idu("nmos", vgs, 1.8 - i * r, 0.0), ("current", "R1"): i,
            ("resistance", "R1"): r, ("capacitance", "Cz"): cz, ("ss_resistance", "Rz"): rz}


def test_passive_only_child_of_first_evaluation_reuses(ctx_passive_r4):
    """DEC-92(CONTRACT 7절 r5) + 14.2: 첫 평가(봉인, ss 있음)를 parent 로 수동소자 θ 만 바꾸면 DC 블록 computes 0, DC 결과·보고 같음."""
    e0 = size_and_seal(ctx_passive_r4, theta_passive_r4())
    assert e0.sealed is not None
    p0 = with_hand_ss(e0)
    reset()
    e1 = size_and_seal(ctx_passive_r4, theta_passive_r4(cz=2e-12), parent=p0)
    assert sum(computes().values()) == 0, computes()
    assert same_dc(e1, e0)


def test_passive_only_child_of_s2p_evaluation_reuses(ctx_passive_r4):
    """DEC-92 재사용 계약(CONTRACT 7절 r5 '수동소자 θ 만 다른 θ 를 parent 에서 부르면 dc 블록 전부 computes 0, 결과는 parent 와
    같은 봉인 상태')은 parent 가 **첫 평가가 아닐 때**도 성립해야 한다(FD 기준점은 보통 탐색 중간 점이다). 사슬: e0(봉인) -> e1 =
    좌표 하나 바꾼 후보(parent = e0 + ss, 그래서 e1 의 tol_I 는 S2p 값) -> e2 = e1 에서 수동소자 θ 만 바꾼 후보(parent = e1 + ss).
    e2 의 DC 입력은 e1 과 모두 같으므로 DC 블록 computes 0, DC 결과(노드전압·op·허용오차)·보고가 e1 과 같아야 한다(CONTRACT 14.2 가 '새 dc_op 전체가
    parent 의 것과 같으면 ... DEC-92 재사용을 지킨다' 고 주장하는 경우)."""
    ctx = ctx_passive_r4
    e0 = size_and_seal(ctx, theta_passive_r4())
    e1 = size_and_seal(ctx, theta_passive_r4(vgs=0.62), parent=with_hand_ss(e0))
    assert e1.sealed is not None
    p1 = with_hand_ss(e1)
    reset()
    e2 = size_and_seal(ctx, theta_passive_r4(vgs=0.62, cz=2e-12), parent=p1)
    assert sum(computes().values()) == 0, {k: v for k, v in computes().items() if v}
    assert same_dc(e2, e1)


# ===========================================================================
# W_request 고정 W (D-GB7d, 설계 40 §3.7, 계획 N3.5 ⑤·N3.17 LY3)
# ===========================================================================

def test_w_request_writer_fixes_w_and_rewrites_coordinate(mir):
    """쓰기 소자 M3(pmos, gate 넷 in 의 writer)에 W = 1e-5 요청: DeviceOp.W = 요청값 정확히, 좌표 ln IDu = ln(ID·L/W) 로 V(in) 이
    정해진다 -- V(in) = 1.8 − VSG, VSG = r4 닫힌 식 역산(ln(1e-5·1e-6/1e-5), VSD = 1.8 − V(out) = 0.9, VSB 0). θ 의 ln_idu(M3) 는
    무시된다(다른 값을 줘도 노드전압 비트 동일)."""
    th = theta_mirror()
    ev = size_and_seal(mir, th, w_request={"M3": 1e-5})
    o, V = ops(ev), node_voltages(ev.snapshot)
    assert o["M3"].W == 1e-5
    vsg = r4_vgs_of("pmos", math.log(1e-5 * 1e-6 / 1e-5), 0.9, 0.0)
    assert abs(V["out"] - 0.9) <= 1e-12
    assert abs(V["in"] - (1.8 - vsg)) <= 1e-9
    assert abs(o["M3"].ln_idu - math.log(1e-5 * 1e-6 / 1e-5)) <= 1e-12
    th2 = dict(th)
    th2[("ln_idu", "M3")] = r4_ln_idu("pmos", 0.8, 0.9, 0.0)
    ev2 = size_and_seal(mir, th2, w_request={"M3": 1e-5})
    assert ev2.snapshot.column("node", "dc_v") == ev.snapshot.column("node", "dc_v")


def test_w_request_diode_writer(mir):
    """diode 쓰기 소자 M1 에 W = 2e-5: V(nb) = VGS 가 VGS = 역산(ln(ID·L/W), VDS = VGS) 의 근(1변수, 독립 bisection). 오차 ≤ 그
    SCC 의 수렴 tol(5.4 1변수 구간 bisection)."""
    ev = size_and_seal(mir, theta_mirror(), w_request={"M1": 2e-5})
    target = math.log(1e-5 * 1e-6 / 2e-5)
    lo, hi = 0.0, 1.8
    for _ in range(200):                                     # h(v) = v − vgs_of(target, vds = v) 단조 증가
        mid = 0.5 * (lo + hi)
        if mid - r4_vgs_of("nmos", target, mid, 0.0) > 0:
            hi = mid
        else:
            lo = mid
    v_star = 0.5 * (lo + hi)
    log = {e.nodes: e for e in ev.snapshot.value("graph", S.DC_KEY, "dc_scc_log")}[("nb",)]
    assert abs(node_voltages(ev.snapshot)["nb"] - v_star) <= log.tol
    assert ops(ev)["M1"].W == 2e-5


def test_w_request_dependent_keeps_coordinate(mir):
    """종속 소자 M2(parallel_vgs) 에 W = 3e-5: 좌표·노드전압은 요청 없을 때의 닫힌 식 그대로(V(out) = 0.9, V(nb) = M1 좌표의 diode
    근 0.6 -- θ 구성), DeviceOp.W = 요청값, idu_forward = exp(ln IDu(V(nb), 0.9, 0))."""
    ev = size_and_seal(mir, theta_mirror(), w_request={"M2": 3e-5})
    V, o = node_voltages(ev.snapshot), ops(ev)
    log = {e.nodes: e for e in ev.snapshot.value("graph", S.DC_KEY, "dc_scc_log")}[("nb",)]
    assert abs(V["nb"] - 0.6) <= log.tol and abs(V["out"] - 0.9) <= 1e-12
    assert o["M2"].W == 3e-5
    assert rel_close(o["M2"].idu_forward, math.exp(r4_ln_idu("nmos", V["nb"], 0.9, 0.0)), 1e-9)


def test_w_request_dependent_mismatch_judged_by_seal_3(mir):
    """종속 소자의 요청 W 가 그 전류에 맞는 W 의 2배면 순방향 전류 = 2·ID -> 노드 out 의 KCL 잔차 = ID = 1e-5 A(닫힌 식: 순방향
    IDu × 2W_nat/L = 2·ID). S2p parent(봉인 + ss)가 있으면 tol_I = tol_V × max(gm(M2), gm(M3)) = tol_V × (B − C·0.6)·ID 라 봉인 3
    위반(CONTRACT 14.3 '종속 소자의 ID 어긋남은 봉인 3 이 판정한다', 계획 N3.6 tol_I). margin = 잔차 / tol_I."""
    th = theta_mirror()
    e0 = size_and_seal(mir, th)
    assert e0.sealed is not None
    parent = with_hand_ss(e0)
    V0 = node_voltages(e0.snapshot)
    w_nat = 1e-5 * 1e-6 / math.exp(r4_ln_idu("nmos", V0["nb"], 0.9, 0.0))
    assert rel_close(ops(e0)["M2"].W, w_nat, 1e-9)                       # 전제: 요청 없을 때 W
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(mir, th, parent=parent, w_request={"M2": 2 * w_nat})
    d = detail(ei.value)
    assert d["item"] == 3 and d["nodes"] == ("out",)
    tol_v = dict(e0.snapshot.column("device", "dc_tol_v"))["M2"]
    gm_max = max((B - C * 0.6) * 1e-5, (B - C * 0.7) * 1e-5)
    assert rel_close(ei.value.record.margin, 1e-5 / (tol_v * gm_max), 1e-5)


def test_w_request_forms_equivalent(mir):
    """{MOS: W} 와 ((MOS, W), ...)(순서 무관) 은 같은 입력(CONTRACT 14.3)."""
    a = size_and_seal(mir, theta_mirror(), w_request={"M3": 1e-5, "M2": 3e-5})
    b = size_and_seal(mir, theta_mirror(), w_request=(("M2", 3e-5), ("M3", 1e-5)))
    c = size_and_seal(mir, theta_mirror(), w_request=(("M3", 1e-5), ("M2", 3e-5)))
    assert a.snapshot.fp == b.snapshot.fp == c.snapshot.fp
    assert normalize_w_request(mir, {"M3": 1e-5, "M1": 2e-5}) == (("M1", 2e-5), ("M3", 1e-5))


def test_empty_w_request_same_as_none(mir):
    """요청이 없으면 블록 입력이 종래와 같다(CONTRACT 14.3): w_request=() 와 {} 와 생략이 같은 스냅샷."""
    a = size_and_seal(mir, theta_mirror())
    b = size_and_seal(mir, theta_mirror(), w_request={})
    c = size_and_seal(mir, theta_mirror(), w_request=())
    assert a.snapshot.fp == b.snapshot.fp == c.snapshot.fp


@pytest.mark.parametrize("bad", [{"I1": 1e-6}, {"ZZ": 1e-6}, {"M1": 0.0}, {"M1": -1e-6}, {"M1": float("nan")},
                                 {"M1": float("inf")}, {"M1": float("-inf")}])
def test_w_request_rejects(mir, bad):
    """MOS 가 아닌 이름(이상원 I1)·S1 에 없는 이름·비양수·비유한 W -> ValueError(호출 계약 위반, 후보 실패가 아님)."""
    with pytest.raises(ValueError) as ei:
        size_and_seal(mir, theta_mirror(), w_request=bad)
    assert not isinstance(ei.value, CANDIDATE_FAILURE_CLASSES)
    with pytest.raises(ValueError):
        normalize_w_request(mir, bad)


# ===========================================================================
# IC10 -- 캐시 키가 바뀐 입력을 덮는다 (설계 40 §10.3 IC10, 계획 N3.5 SC-b·SC-d)
# ===========================================================================

def test_ic10_w_request_change_not_served_from_parent(mir):
    """같은 θ, parent = 요청 없는 평가, 바뀐 것은 W_request 하나 -> dc_widths 다시 계산, W = 새 요청값(옛 값 미반환)."""
    th = theta_mirror()
    e0 = size_and_seal(mir, th)
    reset()
    e1 = size_and_seal(mir, th, parent=e0, w_request={"M2": 3e-5})
    assert computes()["dc_widths"] == 1
    assert ops(e1)["M2"].W == 3e-5 != ops(e0)["M2"].W
    reset()
    e2 = size_and_seal(mir, th, parent=e1, w_request={"M2": 4e-5})
    assert computes()["dc_widths"] == 1 and ops(e2)["M2"].W == 4e-5


def test_ic10_parent_ss_change_not_served_from_cache(ctx_r4c, sealed_c):
    """같은 θ 후보, parent 둘(같은 DC 점, ss gm 만 다름: 정합 / M1 1.5 배 어긋남) -> 허용오차 입력이 다르므로 dc_tolerances 가 다시
    계산되고 gm 상한이 다르다(옛 값 미반환)."""
    e0, p_ok = sealed_c
    p_stale = with_hand_ss(e0, gm_scale={"M1": 1.5})
    th = theta_r4c(v1=0.62)
    a = size_and_seal(ctx_r4c, th, parent=p_ok)
    reset()
    b = size_and_seal(ctx_r4c, th, parent=p_stale)
    assert computes()["dc_tolerances"] == 1
    assert gm_bound(a)["M1"] != gm_bound(b)["M1"] and gm_bound(a)["M2"] == gm_bound(b)["M2"]


# ===========================================================================
# 결정론 (CONTRACT 9절) -- U4 경로(L 동치류·OrderHints·W_request·S2p·국소 봉인)
# ===========================================================================

_SCRIPT = r'''
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import conftest as C
from gmid_engine.sizing import OrderHints, size_and_seal, size_and_seal_local, theta_name
tmp = Path(tempfile.mkdtemp())
acc = C.new_access(C.write_r4_lut(tmp / "lut"))
lc = (C.LClassStub("M1", ("M2", "M1")),)
_, ctx = C.build_ctx_u4(tmp / "m", C.circuit_mirror(), acc, l_classes=lc, order_hints=OrderHints(independent=("M2",)),
                        element_values=(("I1", 1e-5),))
th = C.theta_mirror()
del th[("L", "M2")]
th[("ln_idu", "M2")] = th.pop(("ln_idu", "M1"))
e0 = size_and_seal(ctx, th)
e1 = size_and_seal(ctx, th, parent=C.with_hand_ss(e0), w_request={"M3": 1e-5})
cols = ["0", "1"]                                   # circuit_mirror 의 기둥 id 둘(S1 graph.columns)
loc = size_and_seal_local(ctx, {theta_name(k, v): x for (k, v), x in th.items()}, {}, frozenset(cols))
print(json.dumps([ctx.base.fp, e0.snapshot.fp, e1.snapshot.fp, repr(loc)]))
'''


def test_determinism_hashseed_u4_paths(tmp_path):
    script = tmp_path / "det_u4.py"
    script.write_text(_SCRIPT, encoding="utf-8")
    outs = []
    for seed in ("0", "1", "4242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, str(script), str(SKILL_DIR), str(HERE)], capture_output=True, text=True,
                           env=env, timeout=300)
        assert r.returncode == 0, r.stderr[-3000:]
        outs.append(json.loads(r.stdout.strip().splitlines()[-1]))
    assert outs[0] == outs[1] == outs[2]
