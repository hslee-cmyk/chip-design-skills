"""`sizing/kernel_run.py` (U4, U17 ①) -- 평가 커널 본체: tol_I 의 gm(설계 40 v1.6 §3.7-3·§2.4.11, U17 ①)과
W_request 고정 W(설계 40 §3.7 머리 'W_request가 있으면 그 소자의 W는 고정 입력', 계획 N3.5 ⑤·N3.17 LY3, D-GB7d, CONTRACT 14.3),
그리고 IC10(캐시 키가 바뀐 입력을 덮는다, 설계 40 §10.3)·결정론(CONTRACT 9절).

[U17 ①] tol_I = tol_V × 순환 블록 소자 gm 최댓값, gm = 후보 자기 동작점의 `device.dc_gm`(= ID × 그 동작점 LUT gm/ID, writer
`dc_tolerances` 하나). parent(S2p)에 의존하지 않으므로 같은 θ 는 parent 와 무관하게 같은 봉인 결과를 낸다(사용자 결정 G-3').
옛 S2p 경로(`previous_gm_id`·`inherited_gm_id`·`canonical_gm_id`·`gm_grid_max`·`dc_gm_bound`)와 그것을 단언하던 test 는 설계
§11 U17 ① '같은 변경에서 지우는 것' 에 따라 지웠다.

oracle:
- (a) 손계산 -- r4 toy LUT(conftest: ln IDu = ln I0 + B·VGS − C·VGS²/2 + LAM·VDS + VS 항, gm/ID = B − C·VGS)의 닫힌 식.
  예: 'W 고정 쓰기 소자의 좌표 = ln(ID·L/W)' 는 정의(CONTRACT 14.3·계획 N3.17 LY3)를 r4 식에 넣어 VGS 를 닫힌 식으로 푼다.
- (a) dc_gm 손계산 -- conftest `hand_dc_gm`: 이 test 가 r4 LUT 파일(npz)을 직접 열어 그 동작점 gm/ID 를 보간한 값 × ID.
- (a) 구성으로 정한 parent -- 손으로 쓴 `ss_dev`(conftest `with_hand_ss`, 정합·어긋남). 새 설계에서는 결과에 영향이 없어야 하는 입력이다.
- 피검 함수(`size_and_seal`·`dc_tolerances`·`normalize_w_request`)로 기대값을 만들지 않는다. 스냅샷에서 읽는 값은 피검 결과(대조
  대상)이거나 피검 블록의 입력(예: dc_op 의 동작점 좌표·전류, dc_tol_v)뿐이다.
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
from gmid_engine.sizing.kernel_run import normalize_w_request

from .conftest import (B, C, HERE, MIRROR_W_DELTA, SKILL_DIR, build_ctx, build_ctx_u4, circuit_cs_res, circuit_mirror, detail,
                       hand_dc_gm, mirror_delta_max, mirror_w_request, node_voltages, r4_ln_idu, r4_npz, r4_vgs_of, rel_close,
                       seal_item, theta_mirror, theta_r4c, two, with_hand_ss)
from .conftest import block_row  # [XRUN-F1 card B C1] 실행 계수 행

EVAL12 = (S.dc_currents, S.dc_lengths, S.dc_columns, S.dc_widths, S.dc_tolerances, S.dc_seal_node_conflict,
          S.dc_seal_vgs_match, S.dc_seal_kcl, S.dc_seal_bulk_reverse, S.dc_seal_region, S.dc_seal_kvl_branch,
          S.dc_seal_report)         # [EO-1 범위 4] 봉인 7·9 블록 둘 -> dc_seal_region 하나(자리는 옛 봉인 7 자리, 해석)


def computes(ctx):
    """[XRUN-F1 card B C1] ctx 실행 계수에서 평가 블록 12개의 computes(옛 블록 객체 stats 대체 -- 블록은 상태가 없다, C4)."""
    return {b.name: block_row(ctx.counters, b.name)[4] for b in EVAL12}


def computes_since(ctx, before):
    now = computes(ctx)
    return {k: now[k] - before[k] for k in now}


def ops(ev):
    return dict(ev.snapshot.column("device", "dc_op"))


def dc_gm(ev):
    return dict(ev.snapshot.column("device", "dc_gm"))


def same_dc(a, b):
    """두 평가의 DC 결과(노드전압·소자 op·허용오차·봉인 보고)가 같다. parent 에 손 ss 를 쓴 스냅샷은 지문이 다르므로 지문 대신 쓴다."""
    for kind, field in (("node", "dc_v"), ("device", "dc_op"), ("device", "dc_tol_v"), ("device", "dc_gm")):
        if a.snapshot.column(kind, field) != b.snapshot.column(kind, field):
            return False
    return a.report == b.report


def r4_grid_max_gm(kind, L, W, vds, vsb):
    """옛 '첫 평가 gm 상한'(곡선 VGS 격자 위 최대 gm × W/w_m, 폐기된 정의) -- r4 toy 닫힌 식. 새 dc_gm 이 이것과 다름(자기 동작점
    값)을 보이는 대조용으로만 쓴다(vsb = 0 격자점, VDS 방향 1차라 보간 정확)."""
    from .conftest import R4_VGS
    return max(math.exp(math.log(W / L) + r4_ln_idu(kind, v, vds, vsb)) * (B - C * v) for v in R4_VGS)


# [XRUN-F1 card B 규칙 M M-d] KernelContext 는 실행 두 객체를 칸으로 쥔다 -- function 범위(test 하나 = 실행 하나)
@pytest.fixture
def mir(tmp_path_factory, r4_access):
    """circuit_mirror(r4 toy, I1 = 10 µA 선언) KernelContext. M1 diode·M3 writer, M2 dependent(parallel_vgs, 짝 M1)."""
    return build_ctx_u4(tmp_path_factory.mktemp("u4_mir"), circuit_mirror(), r4_access, element_values=(("I1", 1e-5),))[1]


@pytest.fixture
def sealed_c(ctx_r4c):
    """회로 C(r4) 의 봉인 점(1~9 pass)과 그 S2p parent(손 ss_dev)."""
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    assert e0.sealed is not None                                          # 전제(test_seal.py 와 같은 θ)
    return e0, with_hand_ss(e0)


# ===========================================================================
# tol_I = tol_V × 자기 동작점 dc_gm, parent 무관 (설계 40 v1.6 §3.7-3, §2.4.11, 사용자 결정 G-3', U17 ①)
# ===========================================================================

def _npz(r4_lut_root):
    return lambda kind: r4_npz(r4_lut_root[1], kind)


def _parents(ctx, e0):
    """같은 θ 를 평가할 서로 다른 parent 이력: 없음(첫 평가), 봉인 parent + 정합 손 ss(옛 S2p 경로), 봉인 parent + 어긋난 손 ss
    (M1 gm 1.5 배), 다른 θ 의 평가 + 손 ss."""
    other = size_and_seal(ctx, theta_r4c(v1=0.65))
    return {"none": None, "s2p": with_hand_ss(e0), "stale": with_hand_ss(e0, gm_scale={"M1": 1.5}),
            "other": with_hand_ss(other)}


def test_first_evaluation_dc_gm_is_own_operating_point(sealed_c, r4_lut_root):
    """parent 없는 첫 평가: dc_gm = 자기 동작점 ID × LUT 파일 gm/ID(§3.7-3). 옛 '첫 평가 = 곡선 격자 최대 gm' 과 다른 값이다."""
    e0, _ = sealed_c
    gm = dc_gm(e0)
    assert set(gm) == set(ops(e0))
    for m, o in ops(e0).items():
        want = hand_dc_gm(_npz(r4_lut_root), o)
        assert rel_close(gm[m], want, 1e-9), (m, gm[m], want)
        assert r4_grid_max_gm(o.kind, o.L, o.W, o.vds, o.vsb) > 10 * want, m          # 전제: 폐기된 상계와 구별 가능


def test_tol_i_parent_independent(ctx_r4c, sealed_c, r4_lut_root):
    """§3.7-3·§2.4.11: 같은 θ 를 서로 다른 parent 이력(없음·S2p 정합·S2p 어긋남·다른 θ)에서 평가하면 dc_gm·dc_tol_v 열, 봉인 3 결과
    (SealItem 전체: status·magnitude·tol·margin·detail), 봉인 보고가 비트 동일하다. tol_I 손계산: 봉인 3 의 out 행 tol =
    max over out 에 채널이 닿는 M1·M2 of tol_V × dc_gm(손, LUT 파일)."""
    e0, _ = sealed_c
    th = theta_r4c(v1=0.62)
    evs = {k: size_and_seal(ctx_r4c, th, parent=p) for k, p in _parents(ctx_r4c, e0).items()}
    base = evs["none"]
    item0 = seal_item(base.snapshot, 3)
    for k, ev in evs.items():
        assert ev.snapshot.column("device", "dc_gm") == base.snapshot.column("device", "dc_gm"), k
        assert ev.snapshot.column("device", "dc_tol_v") == base.snapshot.column("device", "dc_tol_v"), k
        assert seal_item(ev.snapshot, 3) == item0, k
        assert ev.report == base.report, k
    tolv = dict(base.snapshot.column("device", "dc_tol_v"))
    o = ops(base)
    want = max(tolv[m] * hand_dc_gm(_npz(r4_lut_root), o[m]) for m in ("M1", "M2"))
    assert dict(item0.detail)["worst"] == "out"
    assert rel_close(item0.tol, want, 1e-9), (item0.tol, want)


@pytest.mark.parametrize("which", ["none", "s2p", "stale"])
def test_seal_3_violation_margin_parent_independent(mir, r4_lut_root, which):
    """종속 소자 M2 의 요청 W 가 그 전류에 맞는 W 의 2배 -> 순방향 전류 2·ID, 노드 out 의 KCL 잔차 = ID = 1e-5 A(닫힌 식). tol_I =
    max over out 에 채널이 닿는 M2·M3 of tol_V × dc_gm(자기 동작점: ID × LUT 파일 gm/ID -- W 만 바뀌어 VGS·VDS·VSB·ID 는 요청
    없는 평가 e0 와 같다). margin = 잔차 / tol_I 이고 parent(없음·S2p 정합·S2p 어긋남)와 무관하게 같다(§3.7-3·§2.4.11)."""
    th = theta_mirror()
    e0 = size_and_seal(mir, th)
    assert e0.sealed is not None
    parent = {"none": None, "s2p": with_hand_ss(e0), "stale": with_hand_ss(e0, gm_scale={"M2": 1.5, "M3": 0.5})}[which]
    V0 = node_voltages(e0.snapshot)
    w_nat = 1e-5 * 1e-6 / math.exp(r4_ln_idu("nmos", V0["nb"], 0.9, 0.0))
    assert rel_close(ops(e0)["M2"].W, w_nat, 1e-9)                       # 전제: 요청 없을 때 W
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(mir, th, parent=parent, w_request={"M2": 2 * w_nat})
    d = detail(ei.value)
    assert d["item"] == 3 and d["nodes"] == ("out",)
    tol_v = dict(e0.snapshot.column("device", "dc_tol_v"))
    o0 = ops(e0)
    tol_i = max(tol_v[m] * hand_dc_gm(_npz(r4_lut_root), o0[m]) for m in ("M2", "M3"))
    assert rel_close(ei.value.record.margin, 1e-5 / tol_i, 1e-5), (ei.value.record.margin, 1e-5 / tol_i)


@pytest.fixture
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
    before = computes(ctx_passive_r4)
    e1 = size_and_seal(ctx_passive_r4, theta_passive_r4(cz=2e-12), parent=p0)
    delta = computes_since(ctx_passive_r4, before)
    assert sum(delta.values()) == 0, delta
    assert same_dc(e1, e0)


def test_passive_only_child_of_s2p_evaluation_reuses(ctx_passive_r4):
    """DEC-92 재사용 계약(CONTRACT 7절 r5 '수동소자 θ 만 다른 θ 를 parent 에서 부르면 dc 블록 전부 computes 0, 결과는 parent 와
    같은 봉인 상태')은 parent 가 **첫 평가가 아닐 때**도 성립해야 한다(FD 기준점은 보통 탐색 중간 점이다). 사슬: e0(봉인) -> e1 =
    좌표 하나 바꾼 후보(parent = e0 + ss) -> e2 = e1 에서 수동소자 θ 만 바꾼 후보(parent = e1 + ss).
    e2 의 DC 입력은 e1 과 모두 같으므로 DC 블록 computes 0, DC 결과(노드전압·op·허용오차)·보고가 e1 과 같아야 한다(CONTRACT 14.2 가 '새 dc_op 전체가
    parent 의 것과 같으면 ... DEC-92 재사용을 지킨다' 고 주장하는 경우)."""
    ctx = ctx_passive_r4
    e0 = size_and_seal(ctx, theta_passive_r4())
    e1 = size_and_seal(ctx, theta_passive_r4(vgs=0.62), parent=with_hand_ss(e0))
    assert e1.sealed is not None
    p1 = with_hand_ss(e1)
    before = computes(ctx)
    e2 = size_and_seal(ctx, theta_passive_r4(vgs=0.62, cz=2e-12), parent=p1)
    delta = computes_since(ctx, before)
    assert sum(delta.values()) == 0, {k: v for k, v in delta.items() if v}
    assert same_dc(e2, e1)


def test_passive_only_chain_bit_identical_dc_gm(ctx_passive_r4, r4_lut_root):
    """DEC-92 재사용 + §3.7-3 '수동소자 θ 만 바뀐 자식의 DC 재사용은 parent 입력을 이어받는 특수 경로 없이 입력 버전 일치로 성립한다
    (`dc_gm` 이 수동소자 θ 를 읽지 않는다)': 수동소자 θ 만 바꾼 자식을 두 번 잇는다(e1 -> e2 -> e3, 각 parent 는 직전 평가 + 정합 ss).
    매 단계 DC 블록 computes 0, dc_gm 열이 e1 과 비트 동일(==)하고 그 값은 손계산(ID × LUT 파일 gm/ID)과 같다."""
    ctx = ctx_passive_r4
    e0 = size_and_seal(ctx, theta_passive_r4())
    e1 = size_and_seal(ctx, theta_passive_r4(vgs=0.62), parent=with_hand_ss(e0))
    assert e1.sealed is not None
    for m, o in ops(e1).items():
        assert rel_close(dc_gm(e1)[m], hand_dc_gm(_npz(r4_lut_root), o), 1e-9), m
    prev = e1
    for cz in (2e-12, 3e-12):
        before = computes(ctx)
        nxt = size_and_seal(ctx, theta_passive_r4(vgs=0.62, cz=cz), parent=with_hand_ss(prev))
        delta = computes_since(ctx, before)
        assert sum(delta.values()) == 0, {k: v for k, v in delta.items() if v}
        assert nxt.snapshot.column("device", "dc_gm") == e1.snapshot.column("device", "dc_gm")
        assert same_dc(nxt, e1)
        prev = nxt


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
    """종속 소자 M2(parallel_vgs) 에 W = (1 + δ)·W_nat(conftest `mirror_w_request`, δ = 0.05): 좌표·노드전압은 요청 없을 때의 닫힌 식
    그대로(V(out) = 0.9, V(nb) = M1 좌표의 diode 근 0.6 -- θ 구성), DeviceOp.W = 요청값, idu_forward = exp(ln IDu(V(nb), 0.9, 0)).
    [U17 ①] 옛 요청 3e-5(δ ≈ 0.27)는 자기 동작점 gm 의 tol_I(설계 40 §3.7-3)에서 봉인 3 위반이라 봉인되는 δ 로 바꿨다 -- 전제로
    δ < δ_max = tol_V × max gm/ID (dc_tol_v 입력 + r4 닫힌 식, conftest `mirror_delta_max`)를 함께 확인한다."""
    w_req = mirror_w_request()
    ev = size_and_seal(mir, theta_mirror(), w_request={"M2": w_req})
    V, o = node_voltages(ev.snapshot), ops(ev)
    assert MIRROR_W_DELTA < mirror_delta_max(ev.snapshot)                  # 전제: 요청 어긋남이 봉인 3 허용오차 안
    log = {e.nodes: e for e in ev.snapshot.value("graph", S.DC_KEY, "dc_scc_log")}[("nb",)]
    assert abs(V["nb"] - 0.6) <= log.tol and abs(V["out"] - 0.9) <= 1e-12
    assert o["M2"].W == w_req
    assert rel_close(o["M2"].idu_forward, math.exp(r4_ln_idu("nmos", V["nb"], 0.9, 0.0)), 1e-9)


def test_w_request_forms_equivalent(mir):
    """{MOS: W} 와 ((MOS, W), ...)(순서 무관) 은 같은 입력(CONTRACT 14.3). 종속 소자 M2 의 요청은 봉인 3 허용오차 안(U17 ①)."""
    w_req = mirror_w_request()
    a = size_and_seal(mir, theta_mirror(), w_request={"M3": 1e-5, "M2": w_req})
    b = size_and_seal(mir, theta_mirror(), w_request=(("M2", w_req), ("M3", 1e-5)))
    c = size_and_seal(mir, theta_mirror(), w_request=(("M3", 1e-5), ("M2", w_req)))
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


@pytest.mark.parametrize("dup", [(("M1", 2e-5), ("M1", 2e-5)), (("M1", 2e-5), ("M1", 3e-5)),
                                 (("M3", 1e-5), ("M1", 2e-5), ("M3", 1e-5))])
def test_w_request_duplicate_name_rejected(mir, dup):
    """CONTRACT 14.3(U4 후속): (MOS, W) 쌍 목록에 같은 소자 이름이 두 번 -> ValueError(호출 계약 위반, 값이 같아도 거부), 후보 실패
    클래스가 아니다. oracle (d) 계약 문언."""
    with pytest.raises(ValueError) as ei:
        size_and_seal(mir, theta_mirror(), w_request=dup)
    assert not isinstance(ei.value, CANDIDATE_FAILURE_CLASSES)
    with pytest.raises(ValueError):
        normalize_w_request(mir, dup)


# ===========================================================================
# IC10 -- 캐시 키가 바뀐 입력을 덮는다 (설계 40 §10.3 IC10, 계획 N3.5 SC-b·SC-d)
# ===========================================================================

def test_ic10_w_request_change_not_served_from_parent(mir):
    """같은 θ, parent = 요청 없는 평가, 바뀐 것은 W_request 하나 -> dc_widths 다시 계산, W = 새 요청값(옛 값 미반환)."""
    th = theta_mirror()
    e0 = size_and_seal(mir, th)
    w1, w2 = mirror_w_request(0.05), mirror_w_request(0.10)              # [U17 ①] 둘 다 δ < δ_max(봉인 3 허용오차 안, conftest 주석)
    assert 0.10 < mirror_delta_max(e0.snapshot)
    before = computes(mir)
    e1 = size_and_seal(mir, th, parent=e0, w_request={"M2": w1})
    assert computes_since(mir, before)["dc_widths"] == 1
    assert ops(e1)["M2"].W == w1 != ops(e0)["M2"].W
    before = computes(mir)
    e2 = size_and_seal(mir, th, parent=e1, w_request={"M2": w2})
    assert computes_since(mir, before)["dc_widths"] == 1 and ops(e2)["M2"].W == w2


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


# =====================================================================================================================
# [IT-2a 20261021-it2a-snapshot-derive, T-L11a] parent 분기 = `parent.snapshot.derive_child(keep)` (design 41 4.7-3c).
# keep = base writer(ctx.base.block_versions 키) ∪ 그 평가 커널 호출 블록. 시그니처 불변 진입점 `size_and_seal(ctx, theta, parent=)` 로 잰다.
# oracle:
# - (a) 구성으로 정한 parent -- `with_hand_ss`(커널 밖 writer `ss_dev` 의 필드를 손으로 실은 parent).
# - (a) 독립 기준 -- 같은 θ 를 parent 없이 평가한 스냅샷(= 커널 호출 블록 + base writer 필드만 가진다)과 ctx.base(S1·계획 등 base writer 필드).
# - 피검 함수(derive_child·run_kernel 내부)로 기대값을 만들지 않는다.
# =====================================================================================================================

def _it2a_nonempty_fields(snap):
    """권한표의 (kind, field) 가운데 열이 비어 있지 않은 것(스냅샷 읽기만)."""
    return {kf for kf, _w in snap.writers.entries if snap.column(*kf) != ()}


def _it2a_theta():
    return theta_r4c(v1=0.62)


def _it2a_ss_writer():
    from gmid_engine.sizing import S2_WRITERS
    return S2_WRITERS.writer_of("device", "ss_dev")


def test_it2a_child_drops_fields_of_writer_outside_kernel(ctx_r4c):
    """parent 에 커널 밖 writer(ss_dev) 필드를 실은 픽스처 -> child 스냅샷에 그 필드·block_version 없음. 기준 = 같은 θ 의 parent 없는 평가.
    base(parent.snapshot 통째 출발): ss_dev 열이 child 에 남아 red."""
    ss_writer = _it2a_ss_writer()
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    assert e0.sealed is not None                                           # 전제
    parent = with_hand_ss(e0)
    assert parent.snapshot.column("device", "ss_dev") != ()                # 전제: parent 에 낡은 커널 밖 필드가 실려 있다
    assert parent.snapshot.block_version(ss_writer) == "hand_ss"
    child = size_and_seal(ctx_r4c, _it2a_theta(), parent=parent)
    free = size_and_seal(ctx_r4c, _it2a_theta())                           # 기준: parent 없는 평가
    assert child.snapshot.column("device", "ss_dev") == ()
    assert child.snapshot.block_version(ss_writer) is None
    assert set(child.snapshot.block_versions) == set(free.snapshot.block_versions)
    assert _it2a_nonempty_fields(child.snapshot) == _it2a_nonempty_fields(free.snapshot)


def test_it2a_child_keeps_every_base_writer_field(ctx_r4c):
    """base writer(ctx.base.block_versions 키) 필드는 child 에 남는다(지우면 red) -- 기대값 = ctx.base 의 같은 열·같은 block_version."""
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    assert e0.sealed is not None
    child = size_and_seal(ctx_r4c, _it2a_theta(), parent=with_hand_ss(e0))
    base = ctx_r4c.base
    base_fields = [(kf, w) for kf, w in base.writers.entries if w in base.block_versions and base.column(*kf) != ()]
    assert len(base_fields) > 0                                            # 전제: 비교 대상이 있다
    for (kind, field), w in base_fields:
        assert child.snapshot.column(kind, field) == base.column(kind, field), (kind, field, w)
        assert child.snapshot.block_version(w) == base.block_version(w), w


def test_it2a_parentless_evaluation_passes_seal_4(ctx_r4c):
    """parent 없는 평가(스냅샷 = ctx.base)는 봉인 4 를 통과한다(keep 을 옛 _CONTEXT_WRITERS 로 구현하면 base writer 필드가 빠져 red).
    parent 가 있는 평가도 같다."""
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    assert e0.sealed is not None
    assert e0.report.items[3].item == 4 and e0.report.items[3].status == "pass"
    e1 = size_and_seal(ctx_r4c, _it2a_theta(), parent=with_hand_ss(e0))
    assert e1.sealed is not None
    assert e1.report.items[3].item == 4 and e1.report.items[3].status == "pass"


def test_it2a_parent_with_other_base_writer_version_rejected(ctx_r4c):
    """base writer 버전이 ctx.base 와 다른 parent -> ValueError. base writer 마다(옛 검사는 PLAN_WRITERS 만 봤다) 그 writer 필드를 다른
    input_version 으로 다시 쓴 parent 를 만들어 하나씩 거부를 확인한다. 거부 전 전제: 어긋나지 않은 parent 는 받아들여진다."""
    from gmid_engine.sizing import DcEvaluation
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    assert e0.sealed is not None
    size_and_seal(ctx_r4c, _it2a_theta(), parent=with_hand_ss(e0))        # 전제: 일치하는 parent 는 거부되지 않는다
    base = ctx_r4c.base
    tried = []
    for (kind, field), w in base.writers.entries:
        if w not in base.block_versions or w in tried or base.column(kind, field) == ():
            continue
        bad = e0.snapshot.write(w, "tampered_it2a", {(kind, field): dict(e0.snapshot.column(kind, field))})
        assert bad.block_version(w) != base.block_version(w)               # 전제: 어긋남이 실제로 만들어졌다
        tried.append(w)
        with pytest.raises(ValueError):
            size_and_seal(ctx_r4c, _it2a_theta(), parent=DcEvaluation(bad, e0.report, None))
    assert len(tried) >= 2                                                 # 전제: base writer 여럿을 시험했다


# =====================================================================================================================
# [IT-2e 20261104-it2e-partial-snapshot, T-E1·T-E8] parent 있는 평가에서 커널 블록 k 의 후보 실패 -> 부분 스냅샷(EvalResult.partial = exc.partial)
# 규칙(interface '규칙'): block_versions 키 = base writer ∪ k 앞 블록, 필드 writer ⊆ 같은 집합, k 와 그 뒤 블록 필드 없음(parent 값이 남으면 red).
# oracle (변성): 같은 θ 를 parent 가 있을 때/없을 때 부르는 변환에도 부분 스냅샷 규칙이 같다. 기대 집합은 이 test 가 독립 관찰로 만든다 --
#   base writer = 실행 컨텍스트 ctx.base.block_versions 의 키(입력), k 앞 블록 = `ComputeBlock.__call__` 감쌈이 센 호출 순서.
#   피검 함수(writers_in_scope·derive_child·run_kernel)로 기대값을 만들지 않는다. 고정 블록 목록은 쓰지 않는다(k 는 EVAL12 상수, 앞 블록은 관찰).
# 실패 주입: test_partial_snapshot_seal_stage_block_failure 와 같은 공개 경로 -- 대상 블록 호출에서 실제 봉인 위반 기록(구성)으로 만든
#   SealViolationError.from_record 를 올린다. 사례 유효 조건 (가): 주입 직전 같은 입력으로 그 블록 함수를 실제로 한 번 돌려 계수 증분이
#   (calls 1, reuses 0, grafts 0, replays 0, computes 1, 재계산 0)임을 확인한다 -- 아니면 사례 무효(단언 실패). (나): 대조 평가는 다른 컨텍스트·다른 객체.
# =====================================================================================================================

from types import SimpleNamespace  # noqa: E402

from gmid_engine.core import ComputeBlock  # noqa: E402

from .conftest import COUNT_FIELDS, Oracle, circuit_cs_pmos_load, row_delta, theta_c  # noqa: E402

IT2E_KERNEL = tuple(b.name for b in EVAL12[:5])          # 평가 커널 4 + dc_tolerances (EVAL12 상수에서 읽음)
IT2E_SEAL = tuple(b.name for b in EVAL12[5:])            # 봉인 항목 블록 6 + dc_seal_report


def it2e_theta_parent():
    return theta_c()


def it2e_theta_child():
    """parent 와 전류·L·좌표·y 가 모두 다른 θ -- 어느 블록이든 입력 버전이 parent 와 달라 실제로 계산된다(가)."""
    return theta_c(y=0.45, i2=3e-5, l1=2e-6, l2=1e-6)


def it2e_record(tmp_path_factory, toy_access):
    """주입할 FailureRecord = 실제 봉인 위반 평가가 낸 기록(구성: test_failure_seal_violation 과 같은 θ)."""
    doc = circuit_cs_res(bulk_m1="out")
    doc["topology_name"] = "it2e_record"
    ctx = build_ctx(tmp_path_factory.mktemp("it2e_rec"), doc, toy_access)[2]
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.3, -0.3),
          ("current", "R1"): 1e-5, ("resistance", "R1"): 1.5e5}
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    return ei.value.record


def it2e_rows(ctx):
    return {r.block: tuple(getattr(r, f) for f in COUNT_FIELDS) for r in ctx.counters.snapshot().blocks if r.part == "*"}


def it2e_run(tmp_path_factory, toy_access, monkeypatch, k, with_parent, rec):
    """새 실행 하나(회로 C, toy)에서 θ_child 를 평가하며 블록 k 에서 후보 실패를 주입한다. with_parent 면 같은 컨텍스트에서 먼저 평가한
    θ_parent 의 평가를 parent 로 준다. 반환 SimpleNamespace(exc, seen, entered, probe, parent, ctx, delta)."""
    ctx = build_ctx(tmp_path_factory.mktemp("it2e_run"), circuit_cs_pmos_load(), toy_access)[2]
    parent = size_and_seal(ctx, it2e_theta_parent()) if with_parent else None
    seen, entered, probe = [], [], []
    orig = ComputeBlock.__call__

    def wrapped(self, snapshot, *extras, **kw):
        seen.append(self.name)
        if self.name == k:
            entered.append(snapshot)
            row0 = block_row(ctx.counters, k)
            orig(self, snapshot, *extras, **kw)                    # (가) 실제로 계산되는지 계수로 확인
            probe.append(row_delta(block_row(ctx.counters, k), row0))
            raise SealViolationError.from_record(rec)
        return orig(self, snapshot, *extras, **kw)

    rows0 = it2e_rows(ctx)
    with monkeypatch.context() as mp:
        mp.setattr(ComputeBlock, "__call__", wrapped)
        with pytest.raises(SealViolationError) as ei:
            size_and_seal(ctx, it2e_theta_child(), parent=parent)
    rows1 = it2e_rows(ctx)
    zero = (0,) * len(COUNT_FIELDS)
    delta = {n: row_delta(rows1[n], rows0.get(n, zero)) for n in rows1}
    # 전제 (가): 대상 블록에 정확히 한 번 들어갔고, 마지막 호출이 k 이며, 재사용·이식 없이 계산됐다. 부분 스냅샷이 붙어 있다.
    assert len(entered) == 1 and seen[-1] == k, (k, seen)
    assert probe[0] == (1, 0, 0, 0, 1, 0), (k, dict(zip(COUNT_FIELDS, probe[0])))
    assert ei.value.partial is not None
    return SimpleNamespace(exc=ei.value, seen=seen, entered=entered, probe=probe, parent=parent, ctx=ctx, delta=delta)


def it2e_expected_keys(r):
    """base writer ∪ k 앞 블록 -- base writer = ctx.base.block_versions 키(입력), k 앞 = 관찰한 호출 순서."""
    return set(r.ctx.base.block_versions) | set(r.seen[:-1])


def it2e_assert_rule(r, k):
    partial = r.exc.partial
    exp = it2e_expected_keys(r)
    assert set(partial.block_versions) == exp, sorted(set(partial.block_versions) ^ exp)
    assert k not in partial.block_versions
    for kf, w in partial.writers.entries:                         # 필드 writer ⊆ 같은 집합 (parent 값이 남으면 red)
        if partial.column(*kf) != ():
            assert w in exp, (kf, w)
    later = [b.name for b in EVAL12 if b.name not in exp]         # k 와 그 뒤 블록
    assert k in later
    for kf, w in partial.writers.entries:
        if w in later:
            assert partial.column(*kf) == (), (kf, w)


def it2e_assert_parent_had_k_fields(r, k):
    """전제: parent 스냅샷은 k 의 필드를 실제로 갖고 있다 -- 안 지우면 남는 값이 있는 사례만 유효."""
    assert r.parent is not None
    ps = r.parent.snapshot
    assert any(ps.column(*kf) != () for kf, w in ps.writers.entries if w == k), k


@pytest.mark.parametrize("k", IT2E_KERNEL)
def test_it2e_kernel_block_failure_with_parent_partial_rule(tmp_path_factory, toy_access, monkeypatch, k):
    """T-E1: parent 있는 평가의 커널 블록 k 후보 실패 -> 부분 스냅샷 규칙 충족, k 이후 필드 없음."""
    rec = it2e_record(tmp_path_factory, toy_access)
    r = it2e_run(tmp_path_factory, toy_access, monkeypatch, k, True, rec)
    it2e_assert_parent_had_k_fields(r, k)
    it2e_assert_rule(r, k)


@pytest.mark.parametrize("k", IT2E_KERNEL + IT2E_SEAL)
def test_it2e_failure_attach_adds_no_block_calls(tmp_path_factory, toy_access, monkeypatch, k):
    """T-E8 (G-10): 부분 스냅샷 부착이 블록을 더 부르지 않는다 -- 실행 계수 호출 증분 = 감쌈이 센 호출 수, 같은 입력 재계산 0,
    블록당 계산 ≤ 1. oracle (독립): 감쌈이 센 호출(피검 출력이 아닌 관찰)."""
    rec = it2e_record(tmp_path_factory, toy_access)
    r = it2e_run(tmp_path_factory, toy_access, monkeypatch, k, True, rec)
    for name, row in r.delta.items():
        d = dict(zip(COUNT_FIELDS, row))
        assert d["calls"] == r.seen.count(name), (name, d, r.seen)
        assert d["recomputes_same_input"] == 0, (name, d)
        assert d["computes"] <= 1, (name, d)
