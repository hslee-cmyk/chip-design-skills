"""WB-1 R-1~R-10, R-12 (interface card 20261104-wb1 §6): 실현 평가 `realize_front(sctx, points) -> RealizeOutcome`.

oracle 종류와 출처
- R-1 (a/d): 탐색 W = I·L/exp(ln IDu), 실현 W = m·w_s, 실현 전류밀도 = I'·L/W' -- dc_op 의 current·L·ln_idu·W 사이 항등식(값은 스냅샷 입력 열).
- R-2 (식, [개정 2026-11-06 판정 MJ-1] VGS2 고정점으로 정밀화): r4 닫힌 식 ln IDu = const + B·V - C·V²/2 + LAM·VDS (B = 20, C = 8, LAM = 0.1, sizing conftest r4 toy 상수).
  입력 차 이동 Δ = [-g2 + √(g2² + 2C·ln(1 + r))]/C, g2 = B - C·VGS2, r = W'/W - 1 (VGS2 = 실현 점 M2 VGS). M2 전류 불변에서
  f(VGS2) - f(VGS0) + LAM·(VGS2 - VGS0 - Δ/2) = 0 (ΔV(inn) = Δ/2, 공통모드 고정 반대칭 가중). 두 식의 고정점은 `wb1_hand.diff_pair_input_shift`(이분법, 피검 함수 아님).
  ln(1 + r)/g 근사는 쓰지 않는다. 단언 = ||V_id(실현) - V_id(탐색)| - Δ| <= tol_V(봉인 tol 최솟값, 바꾸지 않음) 와 |V_id 이동| >= Δ/2 (공허 방지).
  VGS0 는 선언 상수(wb1_flow.VGS0 = θ 입력)이고 탐색 스냅샷 dc_op 값과 같음을 전제 단언한다. 판정 mi-10: 측정과 손 값의 차(약 4.5 mV, 원인 미상)는 tol 을 바꾸지 않고
  단언 메시지·보고에 두 값을 남긴다.
- R-6 ([기대 변경 2026-11-06 O-237]): 입력 고정 갈래 = KCL 재풀이 + 재봉인. ΔV(out) = a·[(1 + r)·e^{-LAM·ΔV} - 1] 의 근(`wb1_hand.source_load_out_shift`, 이분법; 회로 = M1 pmos 소스 vdd + 저항 out -> gnd [dispute 7.1],
  nmos·vdd 저항 꼴의 거울)과 같음. a = V(out)_탐색 = R·I, r = W'/W - 1. 옛 '재풀이 0, 봉인만' 단언은 폐기. R-6c: 레일 안 근 없음(F(V_gnd) < 0) -> lost, fail-closed. R-15 (동작 대체, mi-7):
  입력 고정 경로에서 실현 뒤 출력 넷 KCL 이 성립(저항 전류 = M1 채널 전류 I')하고 출력이 움직임 -- 재풀이 없는 경로는 KCL 이 깨져 봉인 3 이 실패한다.
- R-16 ([새 2026-11-06 A-123 (4)]): KCL 항등식 V_dd·V(s)_실현/R (MOS 채널 전류 = I' = 저항 전류), 비교 허용 = V_dd·tol_V/R (카드의 tol_V 계열). 공허 방지 = θ 전류 셈과의
  차 > `power_resolution_w`. 이상 전류원 항: P = V_dd·(V(s)/R + I_b), I_b = 선언 입력 값.
  [개정 2026-11-06, dispute 7.2] 비교 허용 = 그 평가의 `objectives.power_resolution_w`(graph 필드, Σ_레일 |V_k|·봉인 3 tol_I -- 엔진 KCL 허용 정의). 채널 전류 = 저항 전류
  단언의 허용 = power_resolution_w / V_dd (vdd 레일만 셈). 옛 허용 V_dd·tol_V/R 은 엔진 정의에 없는 발명 상수라 폐기.
- R-3~R-8, R-12 (d): interface 표의 사유 어휘·r = 0 이면 입력 값 유지·`finger_slice` 호출 0(관찰 지점 §9) -- 같은 test 에서 탐색 평가의 호출 >= 1 을 먼저 단언.
- R-5 (구성): 탐색에서 비지배인 두 점(전력 낮음·면적 큼 / 전력 높음·면적 작음), 한 점 M1 을 큰 W' 로 tamper -> 실현 면적이 커져 다른 점이 지배.
- R-9: `find_front` 모듈 전역 `sweep_front`·`realize_front` (관찰 지점 §9).
**미측정**: R-2 회로의 실제 통과·실현 평가 c < 0 발생 수는 card 가 미측정으로 적었다. 전제 단언이 깨지면 회로·기대값을 고치지 말고 멈추고 보고한다.
기존 fixture 이행은 이번 범위가 아니라 `wb1_flow.bins_case`(합성 bin LUT, 새 LutAccess)를 쓴다.
"""
import dataclasses
import json
import math
import sys
from pathlib import Path

import pytest

from sizing.conftest import B, C, LAM, column_dict, seal_item
from wb1_hand import diff_pair_input_shift, source_load_kcl_at_vdd, source_load_out_shift

from .conftest import CELLS_C, circuit_c, theta_r4c
from .wb1_flow import (R2_CELLS, R2_ELEMENTS, R6_ELEMENTS, R6_FINGER_W, R6_I, R6_R, R6_RBOUNDS, VDD, VGS0, bins_case, circuit_r16, circuit_r2, circuit_r6, r2_theta,
                       single_mos_resistor_theta, sorted_theta)

GRID = 1e-8


def mod(name):
    return sys.modules["gmid_engine.search." + name]


def replace_snap(ev, snap):
    return dataclasses.replace(ev, evaluation=dataclasses.replace(ev.evaluation, snapshot=snap))


def with_fingers(ev, updates=None, remove=()):
    from gmid_engine.sizing import DC_SOLVE_WRITER
    snap = ev.evaluation.snapshot
    col = column_dict(snap, "device", "dc_finger")
    col.update(updates or {})
    for k in remove:
        col.pop(k)
    return replace_snap(ev, snap.write(DC_SOLVE_WRITER, "tampered", {("device", "dc_finger"): col}))


class Count:
    def __init__(self, orig):
        self.orig, self.n = orig, 0

    def __call__(self, *a, **k):
        self.n += 1
        return self.orig(*a, **k)


@pytest.fixture(scope="module")
def r2(tmp_path_factory):
    from gmid_engine.search import evaluate
    case = bins_case(tmp_path_factory.mktemp("wb1_r2"), circuit_r2(), elements=R2_ELEMENTS)
    th = r2_theta(case.dc)
    ev = evaluate(case.sctx, sorted_theta(th), R2_CELLS)
    ops = dict(ev.evaluation.snapshot.column("device", "dc_op"))
    # 전제 (손): 탐색 W_M1 = W_M2 = 2e-6 (V(out) = V(x) 로 고정), 자연 선택 (1, 2e-6)
    assert abs(ops["M1"].W - 2e-6) <= 1e-3 * 2e-6 and abs(ops["M2"].W - 2e-6) <= 1e-2 * 2e-6, (ops["M1"].W, ops["M2"].W)
    fing = dict(ev.evaluation.snapshot.column("device", "dc_finger"))
    assert (fing["M1"].m, round(fing["M1"].w_f_m / GRID)) == (1, 200)
    return case, th, ev


@pytest.fixture
def r2_own(tmp_path):
    """R-3 전용: 경우마다 독립 sctx(평가 캐시 `sctx.cache` 공유 0) -- 모듈 fixture 를 쓰면 첫 경우가 채운 캐시 때문에 둘째 경우의 양성 대조(`finger_slice` 호출 >= 1)가 항상 0 이다."""
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS)
    return case, r2_theta(case.dc)


def realize(case, *evs, ids=None):
    from gmid_engine.search import FrontPoint, realize_front
    ids = ids or ["p%d" % i for i in range(len(evs))]
    pts = tuple(FrontPoint(i, e, ()) for i, e in zip(ids, evs))
    return pts, realize_front(case.sctx, pts)


def lost_of(out):
    return {pid: (reason, detail) for pid, reason, detail in out.lost}


def vid(snap):
    v = dict(snap.column("node", "dc_v"))
    return v["inp"] - v["inn"]


# ---------------------------------------------------------------- R-1
def test_realize_r1_search_and_realized_widths_and_current_density(r2):
    case, th, ev = r2
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == ()
    s_ops = dict(ev.evaluation.snapshot.column("device", "dc_op"))
    for m, o in s_ops.items():                                     # 탐색: W = I·L/IDu
        assert o.W == pytest.approx(o.current * o.L / math.exp(o.ln_idu), rel=1e-9), m
    rsnap = out.points[0].result.evaluation.snapshot
    r_ops, r_fing = dict(rsnap.column("device", "dc_op")), dict(rsnap.column("device", "dc_finger"))
    assert len(r_fing) == len(r_ops) >= 4
    for m, o in r_ops.items():                                     # 실현: W' = m·w_s, 전류밀도 = I'·L/W'
        f = r_fing[m]
        assert o.W == pytest.approx(f.m * f.w_f_m, rel=1e-12), m
        assert o.current * o.L / o.W == pytest.approx(math.exp(o.ln_idu), rel=1e-9), m
        assert f.residual == 0.0
        assert o.w_key == round(f.w_f_m / GRID)


# ---------------------------------------------------------------- R-2
def test_realize_r2_input_difference_shift_matches_closed_form(r2):
    case, th, ev = r2
    snap = ev.evaluation.snapshot
    op1 = dict(snap.column("device", "dc_op"))["M1"]
    r = 3e-6 / op1.W - 1.0                                          # W' = 3e-6 (3, 1e-6)
    assert r == pytest.approx(0.5, abs=2e-3)                        # 전제
    from gmid_engine.sizing import FingerGeom
    tam = with_fingers(ev, {"M1": FingerGeom(3, 1e-6, 0.0)})
    _, out = realize(case, tam)
    assert len(out.points) == 1 and out.lost == ()
    rsnap = out.points[0].result.evaluation.snapshot
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(3e-6, rel=1e-12)
    assert op1.vgs == pytest.approx(VGS0, abs=1e-6)                 # 전제: 탐색 VGS0 = 선언 θ 입력 0.6 V
    # [정밀화 2026-11-06, 판정 MJ-1] 기대 = VGS2 고정점 식 (M2 전류 불변 + M1·M2 전류비 1 + r). 공통모드 고정(반대칭 입력 가중) 전제는 측정 입력 두 값의 합으로 확인
    v0, v1 = dict(snap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert (v1["inp"] + v1["inn"]) == pytest.approx(v0["inp"] + v0["inn"], abs=1e-9)
    delta, _x = diff_pair_input_shift(r, VGS0, B, C, LAM)
    shift = abs(vid(rsnap) - vid(snap))
    tol = min(v for _, v in rsnap.column("device", "dc_tol_v") if v is not None)
    assert shift >= delta / 2.0, (shift, delta)                     # 공허 방지
    assert abs(shift - delta) <= tol, ("measured_shift_V", shift, "hand_delta_V", delta, "diff_V", shift - delta, "tol_V", tol)


# ---------------------------------------------------------------- R-3
@pytest.mark.parametrize("m, w_s_key", [(2, 100), (1, 200)])
def test_realize_r3_zero_residual_keeps_input_finger_without_reselecting(r2_own, monkeypatch, m, w_s_key):
    from gmid_engine.search import evaluate
    from gmid_engine.sizing import FingerGeom
    case, th = r2_own
    bd = sys.modules["gmid_engine.sizing.block_dc"]                  # 관찰 지점 §9 (패키지가 재수출하지 않음)
    c = Count(bd.finger_slice)
    monkeypatch.setattr(bd, "finger_slice", c)
    # `r2_theta` 의 고정점 반복이 이미 이 θ 로 `size_and_seal` 을 불러 실행 색인(donors)에 DC 블록 결과가 있다 -> 입력 버전이 다른 θ(전류 1 ulp)로 평가해야
    # 탐색 경로가 `finger_slice` 를 실제로 부른다(양성 대조). 평가 캐시는 이 경우의 새 sctx 라 경우 사이 공유가 없다.
    th = dict(th)
    th[("current", "M3")] = math.nextafter(th[("current", "M3")], 1.0)
    ev = evaluate(case.sctx, sorted_theta(th), R2_CELLS)
    assert c.n >= 1
    c.n = 0
    op1 = dict(ev.evaluation.snapshot.column("device", "dc_op"))["M1"]
    assert abs(m * w_s_key * GRID - op1.W) <= 1e-3 * op1.W           # 전제: r = 0 에 가까운 입력(W' = 2e-6 = W)
    tam = with_fingers(ev, {"M1": FingerGeom(m, w_s_key * GRID, 0.0)})
    _, out = realize(case, tam)
    assert len(out.points) == 1
    got = dict(out.points[0].result.evaluation.snapshot.column("device", "dc_finger"))["M1"]
    assert (got.m, got.w_f_m, got.residual) == (m, w_s_key * GRID, 0.0)
    assert c.n == 0                                                  # finger_slice 호출 0
    assert not hasattr(mod("realize_front"), "finger_slice")


# ---------------------------------------------------------------- R-4
def test_realize_r4_failed_point_is_lost_and_survivor_stays(r2, monkeypatch):
    from gmid_engine.core import SealViolationError
    from gmid_engine.search import evaluate
    case, th, ev = r2
    th_b = dict(th)
    th_b[("current", "M3")] = math.nextafter(th_b[("current", "M3")], 1.0)
    th_b[("current", "M4")] = th_b[("current", "M3")]
    ev_b = evaluate(case.sctx, sorted_theta(th_b), R2_CELLS)
    rf = mod("realize_front")
    real = rf.evaluate
    bad_theta = tuple(ev_b.theta)
    state = {"n": 0}

    def wrapped(sctx, theta, cells, *a, **k):
        state["n"] += 1
        if tuple(theta) == bad_theta:
            raise SealViolationError(devices=("M1",), margin=0.5, detail={"item": 7, "reason": "wb1_test_forced_failure"})
        return real(sctx, theta, cells, *a, **k)
    monkeypatch.setattr(rf, "evaluate", wrapped)
    pts, out = realize(case, ev, ev_b, ids=["good", "bad"])
    assert state["n"] >= 2
    assert [p.point_id for p in out.points] == ["good"]
    lost = lost_of(out)
    assert set(lost) == {"bad"} and isinstance(lost["bad"][0], str) and lost["bad"][0]


# ---------------------------------------------------------------- R-5
def test_realize_r5_search_nondominated_point_dominated_by_realized_values(r2):
    from gmid_engine.search import evaluate
    from gmid_engine.sizing import FingerGeom
    case, th, ev_b = r2                                             # B: L = 1e-6, 전류 2·I0
    th_a = r2_theta(case.dc, l=2e-6)                                # A: L = 2e-6, W 같고 전류 절반 -> 전력 낮고 면적 큼
    ev_a = evaluate(case.sctx, sorted_theta(th_a), (1, 1, 1, 1))
    pa, aa = ev_a.objectives.power_w, ev_a.objectives.area_m2
    pb, ab = ev_b.objectives.power_w, ev_b.objectives.area_m2
    assert pa < pb and aa > ab                                      # 전제: 탐색에서 서로 지배하지 않는다
    tam_b = with_fingers(ev_b, {"M1": FingerGeom(12, 1e-6, 0.0)})   # B 의 M1 W' = 12e-6 (r = 5) -> 실현 면적 증가
    _, out = realize(case, ev_a, tam_b, ids=["pa", "pb"])
    assert [p.point_id for p in out.points] == ["pa"]               # 재필터로 B 가 빠진다
    assert out.lost == ()                                           # 지배 탈락은 lost 가 아니라 재필터


# ---------------------------------------------------------------- R-6
def test_realize_r6_unresolved_servo_pivot_keeps_input_value(tmp_path):
    from gmid_engine.search import evaluate
    from gmid_engine.sizing import FingerGeom
    case = bins_case(tmp_path, circuit_c())
    ev = evaluate(case.sctx, sorted_theta(theta_r4c()), CELLS_C)
    snap = ev.evaluation.snapshot
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")               # 전제: 피벗 판정 불능 갈래
    w1 = dict(snap.column("device", "dc_op"))["M1"].W
    m = max(1, round(w1 / 1e-6))
    tam = with_fingers(ev, {"M1": FingerGeom(m, 1e-6, 0.0)})
    assert m * 1e-6 != w1                                           # 전제: W' != W (공허 방지)
    _, out = realize(case, tam)
    assert len(out.points) == 1 and out.lost == ()
    rsnap = out.points[0].result.evaluation.snapshot
    assert dict(rsnap.column("node", "dc_v"))["in"] == dict(snap.column("node", "dc_v"))["in"]   # 입력 = 봉인점 값
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(m * 1e-6, rel=1e-12)


# ---------------------------------------------------------------- R-6 (기대 변경 2026-11-06, A-123 (3)·O-237) / R-6c / R-15
# 옛 R-6 의 '재풀이 0, 봉인만' 기대는 효력 없음 -- 위 test 는 입력 값 유지·W' 이행만 단언하므로(재풀이 여부 불문) 그대로 둔다.
# 새 기대(oracle (a), 합성 R-6 회로): 입력 고정 갈래는 KCL 재풀이 + 재봉인. 손 값 = wb1_hand.source_load_out_shift (독립 이분법).
# [개정 2026-11-06, dispute 7.1] 회로 = M1 pmos (out, in, vdd, bulk = vdd) + 저항 out -> gnd (vdd 레일에 채널이 닿아 전력 분해능 정의).
# θ 입력 (M1 전류, 저항, 손가락 폭) = wb1_flow.R6_I, R6_R, R6_FINGER_W. V(out)_탐색 = I·R = 0.75 V (a), VSD(M1) = 1.05 V, M1 포화(손: VDSAT_p(0.6) = 0.455 V).


@pytest.fixture(scope="module")
def r6(tmp_path_factory):
    from gmid_engine.search import evaluate
    case = bins_case(tmp_path_factory.mktemp("wb1_r6"), circuit_r6(), elements=R6_ELEMENTS, rbounds=R6_RBOUNDS)
    th = single_mos_resistor_theta(case.dc, R6_I, R6_R, VDD - R6_I * R6_R, kind="pmos")
    ev = evaluate(case.sctx, sorted_theta(th), (0,))
    snap = ev.evaluation.snapshot
    v = dict(snap.column("node", "dc_v"))
    assert v["out"] == pytest.approx(R6_I * R6_R, abs=1e-9)                              # 전제 (손): 탐색 KCL V(out) = R·I = a
    from gmid_engine.search import STATUS_SEALED
    assert ev.status == STATUS_SEALED                                                    # 전제: 전력 분해능이 정의돼 탐색 평가가 봉인 (옛 회로는 seal_undefined)
    assert ev.objectives.power_resolution_w is not None and ev.objectives.power_resolution_w > 0.0
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")                                    # 전제 (미측정, base 재확인): 입력 고정 갈래
    assert dict(snap.column("device", "dc_op"))["M1"].W > 0.0
    return case, th, ev


def r6_point(ev, m, icm_none=False):
    """search_ref M1 을 (m, R6_FINGER_W) 로 tamper (+ 선택: icm_config.config = None). -> (점, r, a)."""
    from gmid_engine.sizing import FingerGeom, ICM_CONFIG_WRITER
    from sizing.conftest import tamper
    snap = ev.evaluation.snapshot
    w = dict(snap.column("device", "dc_op"))["M1"].W
    r = m * R6_FINGER_W / w - 1.0
    a = dict(snap.column("node", "dc_v"))["out"]                     # a = V(out)_탐색 = R·I (레일 소스 꼴)
    tam = with_fingers(ev, {"M1": FingerGeom(m, R6_FINGER_W, 0.0)})
    if icm_none:
        key, cfg = next(iter(dict(snap.column("graph", "icm_config")).items()))
        tsnap = tamper(tam.evaluation.snapshot, ICM_CONFIG_WRITER, "graph", "icm_config", {key: dataclasses.replace(cfg, config=None)})
        tam = replace_snap(tam, tsnap)
    return tam, r, a


@pytest.mark.parametrize("icm_none", [False, True], ids=["natural_as_is_single_input", "icm_config_none"])
def test_realize_r6_input_fixed_branch_resolves_kcl_and_reseals(r6, icm_none):
    case, th, ev = r6
    tam, r, a = r6_point(ev, 18, icm_none)                         # m = 18 (손): W' = 36 µm, r ≈ 0.5 -> 손 근 V(out) ≈ 1.1 V (레일 안, M1 포화)
    assert 0.4 <= r <= 0.7                                          # 전제: 손으로 고른 r
    hand = source_load_out_shift(a, r, LAM)                         # ΔV(out) (양수: 전류가 늘어 출력이 vdd 쪽으로)
    assert VDD - (a + hand) > 0.455                                 # 전제 (손): 재풀이 점에서도 M1 포화(VSD >= VDSAT_p(0.6))
    _, out = realize(case, tam)
    assert len(out.points) == 1 and out.lost == (), out.lost        # 옛 기대(봉인만)이면 out 넷 봉인 3 실패 -> lost (red)
    snap, rsnap = ev.evaluation.snapshot, out.points[0].result.evaluation.snapshot
    v0, v1 = dict(snap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert v1["in"] == pytest.approx(v0["in"], rel=1e-12)           # 입력 고정
    dv = v1["out"] - v0["out"]
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs(dv) >= abs(hand) / 2.0, (dv, hand)                   # 공허 방지
    assert abs(dv - hand) <= tol, ("measured_dV_V", dv, "hand_dV_V", hand, "tol_V", tol)
    assert seal_item(rsnap, 3).status == "pass" and seal_item(rsnap, 7).status == "pass"
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(18 * R6_FINGER_W, rel=1e-12)


def test_realize_r6c_no_root_inside_rails_is_lost_fail_closed(r6):
    case, th, ev = r6
    snap = ev.evaluation.snapshot
    v_out0 = dict(snap.column("node", "dc_v"))["out"]
    ok_point, r_ok, _a = r6_point(ev, 18)
    assert source_load_kcl_at_vdd(VDD, R6_R, R6_I, v_out0, r_ok, LAM) > 0.0       # 전제 (손): 통제 점은 근이 레일 안에 있다
    bad_point, r_bad, _ = r6_point(ev, 36)                          # m = 36 (손): W' = 72 µm
    f_vdd = source_load_kcl_at_vdd(VDD, R6_R, R6_I, v_out0, r_bad, LAM)
    assert f_vdd < 0.0, f_vdd                                       # 전제 (손, 판정 MJ-1 의 거울): F(V_dd) < 0 = 레일 안에 근이 없음
    _, out = realize(case, ok_point, bad_point, ids=["ok", "bad"])
    assert [p.point_id for p in out.points] == ["ok"]               # 통제 점은 front 에 남고(base 에서는 red), 근 없는 점은 front 에 없다
    lost = lost_of(out)
    assert set(lost) == {"bad"} and isinstance(lost["bad"][0], str) and lost["bad"][0]      # 사유 이름은 base 에서 재확인 -- 비어 있지 않음만 단언


def test_realize_r15_input_fixed_realized_point_satisfies_output_kcl(r6):
    """R-15 동작 대체 (interface 가 grep 대상을 정의하지 않음, 판정 mi-7): 재풀이 없는 '입력 고정' 경로가 있으면 출력 넷 KCL 이 깨진다.
    oracle (a) KCL 항등식: 저항 전류 (V_dd − V(out)_실현)/R = M1 채널 전류 I' (= dc_op.current), 허용 = tol_V/R."""
    case, th, ev = r6
    tam, r, a = r6_point(ev, 18)
    _, out = realize(case, tam)
    assert len(out.points) == 1 and out.lost == ()
    rsnap = out.points[0].result.evaluation.snapshot
    v1 = dict(rsnap.column("node", "dc_v"))
    v0 = dict(ev.evaluation.snapshot.column("node", "dc_v"))
    assert abs(v1["out"] - v0["out"]) > 0.1                          # 공허 방지: 출력이 실제로 움직였다 (재풀이 호출)
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    i_r = v1["out"] / R6_R
    i_m1 = dict(rsnap.column("device", "dc_op"))["M1"].current
    assert abs(i_r - i_m1) <= tol / R6_R, ("R_current_A", i_r, "M1_current_A", i_m1)


# ---------------------------------------------------------------- R-16 (새 2026-11-06, A-123 (4)): 전력 축 = 실현 전류
R16_I, R16_R = 1e-5, 2.5e4                                           # θ 입력. V(s)_탐색 = I·R = 0.25 V, VGS = 0.6 -> V(in) = 0.85 V


def r16_case(tmp, with_source):
    from gmid_engine.search import evaluate
    els = R6_ELEMENTS + ((("I2", "current_source", R16_IB),) if with_source else ())
    case = bins_case(tmp, circuit_r16(with_source), constraints=(), elements=els, rbounds=R6_RBOUNDS)   # 소스 팔로어는 gain_ss_db >= 10 을 지킬 수 없다 (dispute 7.2 (i))
    th = single_mos_resistor_theta(case.dc, R16_I, R16_R, VDD - R16_I * R16_R)
    ev = evaluate(case.sctx, sorted_theta(th), (0,))
    return case, th, ev


R16_IB = 2e-6                                                        # 선언 이상 전류원 값 (입력)


@pytest.mark.parametrize("with_source", [False, True], ids=["mos_channel_only", "with_ideal_current_source"])
def test_realize_r16_power_is_rail_current_of_realized_channel_current(tmp_path, with_source):
    """oracle (a) KCL 항등식: vdd 레일 전류 = M1 채널 전류 I' = 저항 전류 V(s)_실현/R (+ 이상 전류원 선언 값 I_b). 기대 = V_dd·(V(s)_실현/R + I_b).
    비교 허용 = 그 평가의 objectives.power_resolution_w (graph 필드: Σ_레일 |V_k|·봉인 3 tol_I -- 엔진 KCL 허용 정의, 숫자 발명 없음).
    공허 방지 = θ 전류로 셈한 값과의 차 > power_resolution_w."""
    case, th, ev = r16_case(tmp_path, with_source)
    ib = R16_IB if with_source else 0.0
    snap = ev.evaluation.snapshot
    v0 = dict(snap.column("node", "dc_v"))
    assert v0["s"] == pytest.approx(R16_I * R16_R, abs=1e-9)         # 전제 (손): 탐색 V(s) = I·R
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")                # 전제 (base 재확인): 입력 고정 갈래
    assert ev.objectives.power_w == pytest.approx(VDD * (R16_I + ib), rel=1e-12)      # 같은 θ 탐색 평가: V_dd·I (불변)
    w = dict(snap.column("device", "dc_op"))["M1"].W
    m = 44                                                           # 손: W' = 44·2 µm, r = 3 근방
    r = m * 2e-6 / w - 1.0
    assert 2.5 <= r <= 5.0                                           # 전제: 손으로 고른 r (≠ 0)
    from gmid_engine.sizing import FingerGeom
    tam = with_fingers(ev, {"M1": FingerGeom(m, 2e-6, 0.0)})
    _, out = realize(case, tam)
    assert len(out.points) == 1 and out.lost == (), out.lost
    res = out.points[0].result
    rsnap = res.evaluation.snapshot
    v1 = dict(rsnap.column("node", "dc_v"))
    p_res = res.objectives.power_resolution_w                        # graph 필드 = Σ_레일 |V_k|·tol_I,k (이 회로는 vdd 레일만 센다)
    assert p_res is not None and p_res > 0.0
    hand = VDD * (v1["s"] / R16_R + ib)                              # KCL 항등식 (MOS 전류 = I' = V(s)/R)
    got = res.objectives.power_w
    assert abs(got - hand) <= p_res, ("measured_power_W", got, "hand_power_W", hand, "power_resolution_W", p_res)
    theta_current_power = VDD * (R16_I + ib)
    assert abs(got - theta_current_power) > p_res, (got, theta_current_power, p_res)      # 공허 방지 (θ 전류를 읽으면 red)
    i_m1 = dict(rsnap.column("device", "dc_op"))["M1"].current
    assert abs(i_m1 - v1["s"] / R16_R) <= p_res / VDD                # 채널 전류 = 저항 전류, 허용 = power_resolution_w / V_dd (같은 정의, vdd 만 셈)
    if with_source:
        assert dict(rsnap.column("device", "dc_current"))["I2"] == pytest.approx(R16_IB, rel=1e-12)       # 이상 전류원 항의 출처(선언 입력)


# ---------------------------------------------------------------- R-7
def test_realize_r7_servo_branch_mismatch_is_lost(r2, monkeypatch):
    from gmid_engine.sizing import ICM_CONFIG_WRITER
    from sizing.conftest import tamper
    case, th, ev = r2
    cfg0 = next(iter(dict(ev.evaluation.snapshot.column("graph", "icm_config")).values()))
    assert cfg0.config == "servo"                                   # 전제 (미측정: R-2 회로 servo 갈래)
    rf = mod("realize_front")
    real = rf.evaluate
    seen = {"n": 0}

    def wrapped(*a, **k):
        r = real(*a, **k)
        seen["n"] += 1
        snap = r.evaluation.snapshot
        key, cfg = next(iter(dict(snap.column("graph", "icm_config")).items()))
        new = dataclasses.replace(cfg, config="as_is_single_input")
        return replace_snap(r, tamper(snap, ICM_CONFIG_WRITER, "graph", "icm_config", {key: new}))
    monkeypatch.setattr(rf, "evaluate", wrapped)
    _, out = realize(case, ev)
    assert seen["n"] >= 1
    assert out.points == () and lost_of(out)["p0"][0] == "realized_servo_branch_mismatch"


# ---------------------------------------------------------------- R-8
def test_realize_r8_missing_search_finger_is_a_reason_not_keyerror(r2):
    case, th, ev = r2
    _, out = realize(case, with_fingers(ev, remove=("M1",)))
    assert out.points == () and lost_of(out)["p0"][0] == "realized_finger_missing"


# ---------------------------------------------------------------- R-12
def test_realize_r12_finger_not_a_slice_is_slice_missing(r2):
    from gmid_engine.sizing import FingerGeom
    case, th, ev = r2
    _, out = realize(case, with_fingers(ev, {"M1": FingerGeom(1, 3e-6, 0.0)}))        # 슬라이스 {1, 2} µm 에 3 µm 없음
    assert out.points == () and lost_of(out)["p0"][0] == "slice_missing"


# ---------------------------------------------------------------- R-9 / R-10
def test_realize_r9_find_front_calls_realize_once_and_front_is_realized(tmp_path, monkeypatch, short_root):
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    ff = mod("find_front")
    real_sweep, real_rf = ff.sweep_front, ff.realize_front
    rec = []

    def sweep(*a, **k):
        out = dict(real_sweep(*a, **k))
        out["front"] = tuple(out["front"])[:1]                      # front 한 점을 낸 stub
        return out

    def rf(sctx, points):
        o = real_rf(sctx, points)
        rec.append((tuple(points), o))
        return o
    monkeypatch.setattr(ff, "sweep_front", sweep)
    monkeypatch.setattr(ff, "realize_front", rf)
    fr = find_front(case.sctx, [theta_r4c()])
    assert len(rec) == 1                                            # 호출 0 이면 red
    pts_in, out = rec[0]
    assert len(pts_in) == 1
    assert [p.point_id for p in fr.front] == [p.point_id for p in out.points]
    assert all(a.result is b.result and a.result is not pts_in[0].result for a, b in zip(fr.front, out.points))


def test_realize_r10_json_finger_residual_and_selection_residual(tmp_path, short_root):
    """JSON `front[i].finger_residual` = {MOS: 탐색 residual} (reader 잠금) + 선택 경로 손 값: 슬라이스 {5 µm}, W = 12e-6 -> (2, 5e-6), r = -1/6."""
    from types import SimpleNamespace
    from gmid_engine.lut import LBin, LBinMap, finger_slice
    from gmid_engine.search import find_front
    g = 1e-8
    lut = SimpleNamespace(spec=SimpleNamespace(manufacturing_grid_m=g, min_finger_w_m=(("nmos", 1e-6),)),
                          slice_map={("nmos", 500): SimpleNamespace(l_bins=LBinMap(("m",), (1e-6, 5e-6), (LBin("b", 5e-7, 3e-6),), ()))},
                          cap_map={"nmos": SimpleNamespace(w_key=500)}, bin_rule="lower")
    fs = finger_slice(lut, "nmos", 1e-6, lambda key: 12e-6)
    assert (fs.m, fs.w_f_m, fs.w_key) == (2, 5e-6, 500)
    assert 2 * 500 * g / 12e-6 - 1.0 == pytest.approx(-1.0 / 6.0, rel=1e-12)       # 손: r = m·w_s/W - 1
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    ff = mod("find_front")
    real_sweep, searched = ff.sweep_front, []

    def sweep(*a, **k):
        out = real_sweep(*a, **k)
        searched.extend(out["front"])                                # 탐색 점(탐색 스냅샷의 dc_finger 가 기대값의 출처)
        return out
    ff.sweep_front = sweep
    try:
        fr = find_front(case.sctx, [theta_r4c()])
    finally:
        ff.sweep_front = real_sweep
    assert len(searched) >= 1 and len(fr.front) >= 1
    by_id = {p.point_id: p for p in searched}
    (run,) = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(run["front"]) == len(fr.front)
    for entry, p in zip(run["front"], fr.front):
        want = {m: f.residual for m, f in dict(by_id[p.point_id].result.evaluation.snapshot.column("device", "dc_finger")).items()}
        assert dict(entry["finger_residual"]) == want                 # 탐색 residual (실현 후 0.0 이 아님)
        assert "slice_rounds" in entry
    assert {"lost", "n_lost"} <= set(dict(run["realize"]))


def test_realize_r10_json_finger_residual_is_the_tampered_search_value(tmp_path, monkeypatch, short_root):
    """R-10 후반 (interface §6, reader 잠금 S-4): 탐색 점의 `dc_finger` 한 소자를 `FingerGeom(m, w_f, -0.5)` 로 바꾸면(같은 m·w_f 라 실현 평가는 그대로 통과) JSON
    `front[i].finger_residual[소자]` = -0.5 이다. 단언 = 바꾼 값 그대로(탐색 `FingerGeom.residual` 을 읽는다 -- 실현 평가의 0.0 이 아니다).
    oracle (d): interface 표 '탐색 FingerGeom.residual'. 선택 경로 손 값(슬라이스 {5 µm}, W = 12e-6 -> (2, 5e-6), r = -1/6)은 위 test 가 본다."""
    from gmid_engine.sizing import FingerGeom
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    ff = mod("find_front")
    real_sweep = ff.sweep_front
    seen = []

    def sweep(*a, **k):
        out = dict(real_sweep(*a, **k))
        pts = []
        for p in out["front"]:
            fing = dict(p.result.evaluation.snapshot.column("device", "dc_finger"))
            m1 = fing["M1"]
            tam = with_fingers(p.result, {"M1": FingerGeom(m1.m, m1.w_f_m, -0.5)})        # 실현 평가가 쓰는 m·w_f 는 그대로, residual 만 바꾼다
            pts.append(dataclasses.replace(p, result=tam))
            seen.append(p.point_id)
        out["front"] = tuple(pts)
        return out
    monkeypatch.setattr(ff, "sweep_front", sweep)
    fr = find_front(case.sctx, [theta_r4c()])
    assert seen and len(fr.front) >= 1                                    # 양성 대조: 탐색 점을 실제로 바꿨고 실현 뒤 front 가 남았다
    (run,) = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(run["front"]) == len(fr.front)
    for entry in run["front"]:
        assert dict(entry["finger_residual"])["M1"] == -0.5

