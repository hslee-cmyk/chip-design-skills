"""`realized_geometry(snapshot, placements) -> sizing.RealizedGeometry(layout_ref, w_request)` (CONTRACT 4절, 계획 LY7·LY8, WB-1 §3·§8).

oracle (a): 손으로 만든 배치·확산 기하 -- w_request = 요청 대기(pending) 소자의 요청 손가락 행 참조(A-139, 배치 소자는 두지 않음), layout_ref = `ly_diffusion` 필드 중 pending 아닌 소자의
(finger_w, ad, as, pd, ps, m = float(nf)) 참조. [WB-1] 폭 키(kind당 슬라이스) 인자·칸은 없다: 인자는 (snapshot, placements) 둘, 값 칸은 (layout_ref, w_request) 둘.
"""
from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from gmid_engine.convergence import realized_geometry
from gmid_engine.metrics import DiffusionGeometry
from gmid_engine.sizing import RealizedGeometry

from .conftest import GRID, ddiff, layout, placement


def test_all_placed_devices_fixed_and_pending_diffusion_dropped():
    pl = (placement("A", 100, 3, 3e-6), placement("B", 50, 2, 1e-6, pending=True), placement("C", 70, 1, 7e-7))
    diff = (ddiff("C", 7e-7, 1, 1e-13, 2e-13, 1.5e-6, 2.5e-6), ddiff("A", 1e-6, 3, 3e-13, 4e-13, 2.0e-6, 3.0e-6),
            ddiff("B", 9e-7, 4, 5e-13, 6e-13, 1.1e-6, 1.2e-6))
    g = realized_geometry(layout(diffusion=diff).snapshot, pl)
    assert isinstance(g, RealizedGeometry)
    # [개정 여섯째 A-139, interface §3] w_request = 요청 대기 소자(배치 아님 + 요청 행 있음)마다 요청 손가락 행 참조 -- 배치 소자는 w_request 에 두지 않는다 (옛 '배치 소자 전부의 W').
    # 요청 행의 값 모양((nf, finger_w) 참조)은 interface 가 칸 형태를 정하지 않아 이름만 단언한다.
    assert tuple(n for n, _ in g.w_request) == ("B",)
    # [dispute 8.4, 위임 A-141] 요청 행 값 = (nf, finger_w): 요청 대기 배치 B(폭 키 50, nf 2)의 손가락 -- 레이아웃 요청 레코드(Placement)에서 온다 (W 1e-6 에서 다시 고르지 않음)
    assert g.w_request == (("B", (2, 50 * GRID)),)
    assert g.layout_ref == (("A", DiffusionGeometry(1e-6, 3e-13, 4e-13, 2.0e-6, 3.0e-6, 3.0)),
                            ("C", DiffusionGeometry(7e-7, 1e-13, 2e-13, 1.5e-6, 2.5e-6, 1.0)))     # B(대기) 는 탐색 규칙·LUT 규칙 기하로 둔다
    assert all(isinstance(d.m, float) for _n, d in g.layout_ref)


def test_realized_geometry_has_no_width_key_argument_or_field():
    """[WB-1] kind 당 폭 키 운반 삭제: 서명은 (snapshot, placements) 둘, 값 칸은 (layout_ref, w_request) 둘 -- 옛 finger·diffusion·w_keys 칸 없음."""
    assert list(inspect.signature(realized_geometry).parameters) == ["snapshot", "placements"]
    assert [f.name for f in dataclasses.fields(RealizedGeometry)] == ["layout_ref", "w_request"]


def test_geometry_equality_is_value_based():
    pl = (placement("A", 100, 3, 3e-6),)
    diff = (ddiff("A", 1e-6, 3, 3e-13, 4e-13, 2.0e-6, 3.0e-6),)
    a = realized_geometry(layout(diffusion=diff).snapshot, pl)
    b = realized_geometry(layout(diffusion=diff).snapshot, pl)
    c = realized_geometry(layout(diffusion=(ddiff("A", 1e-6, 3, 3e-13, 4.5e-13, 2.0e-6, 3.0e-6),)).snapshot, pl)
    assert a == b and a != c                # 고정점 판정(CONTRACT 7절)은 값 비교 -- 확산 기하만 달라도 다른 기하


# ---------------------------------------------------------------- R-13 (새 2026-11-06, A-124): 레이아웃 뒤 재평가 = W'·바이어스 고정 KCL 재풀이 + 재봉인
# oracle (a) 합성 입력의 손 고정점 (`wb1_hand`, 피검 함수 아님). 레이아웃 기하는 손으로 만든 RealizedGeometry(layout_ref = 배치 소자 접합 기하,
# w_request = 배치 소자 W'), 기준 스냅샷 = parent(사이징 점). 옛 '노드 재풀이 없이 봉인만' 이면 봉인 3 실패 -> evaluate 가 던진다 (red).
def _fingers(snap, **placed):
    """레이아웃 입력 손가락 {소자: (finger_w, nf)}: 사이징 점 스냅샷의 손가락(m·w_s)을 모든 MOS 에 그대로 놓고, 키워드 {소자: (finger_w, nf)} 만 바꾼다."""
    fingers = {m: (f.w_f_m, f.m) for m, f in dict(snap.column("device", "dc_finger")).items()}
    fingers.update(placed)
    return fingers


def _geometry(fingers, requested=None):
    """레이아웃 뒤 기하 -- 공개 `realized_geometry(snapshot, placements)` 로 만든다(값 칸 모양에 기대지 않는다). fingers = {소자: (finger_w, nf)} 는 배치,
    requested = {소자: (finger_w, nf)} 는 요청 대기(배치 아님 + 요청 행). W' = nf·finger_w, 접합 ad/as/pd/ps 는 DC 와 무관한 손 값."""
    requested = requested or {}
    pl = [placement(m, round(fw / GRID), nf, nf * fw) for m, (fw, nf) in sorted(fingers.items())]
    pl += [placement(m, round(fw / GRID), nf, nf * fw, pending=True) for m, (fw, nf) in sorted(requested.items())]
    diff = tuple(ddiff(m, fw, nf, 3e-13, 3e-13, 4e-6, 4e-6) for m, (fw, nf) in sorted(fingers.items()))
    return realized_geometry(layout(diffusion=diff).snapshot, tuple(pl))


def _assert_input_rows(snap, rows):
    """[개정 여섯째 A-139, 완료 (8) (a)] 그 평가 dc_finger = 소자 전부의 입력 손가락 행 (nf, finger_w, 0.0). rows = {소자: (finger_w, nf)}."""
    got = dict(snap.column("device", "dc_finger"))
    assert set(got) == set(rows), (sorted(got), sorted(rows))                       # 모든 MOS 행 (옛 '행 없음·빈 열' 효력 없음)
    for m, (fw, nf) in rows.items():
        assert got[m].m == nf and got[m].w_f_m == pytest.approx(fw, rel=1e-12) and got[m].residual == 0.0, (m, got[m])


def test_layout_resolve_r13a_servo_branch_follows_the_vgs2_fixed_point(tmp_path):
    from gmid_engine.search import evaluate
    from sizing.conftest import B, C, LAM, seal_item
    from search.wb1_flow import R2_CELLS, R2_ELEMENTS, VGS0, bins_case, circuit_r2, r2_theta, sorted_theta
    from wb1_hand import diff_pair_input_shift
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS)
    ev = evaluate(case.sctx, sorted_theta(r2_theta(case.dc)), R2_CELLS)
    snap = ev.evaluation.snapshot
    op1 = dict(snap.column("device", "dc_op"))["M1"]
    fing = dict(snap.column("device", "dc_finger"))
    assert (fing["M1"].m, round(fing["M1"].w_f_m / 1e-8)) == (1, 200)             # 전제: 사이징 점 = 자연 선택 (1, 2e-6), r = 0
    assert op1.vgs == pytest.approx(VGS0, abs=1e-6)
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config == "servo"                                                   # 전제 (미측정): R-2 회로 servo 갈래
    r = 3e-6 / op1.W - 1.0                                                         # 레이아웃 M1 = (nf 3, finger_w 1e-6): W' = 3e-6
    assert r == pytest.approx(0.5, abs=2e-3)
    layout_in = _fingers(snap, M1=(1e-6, 3))
    out = evaluate(case.sctx, ev.theta, ev.key.cells, parent=ev, geometry=_geometry(layout_in))
    assert out.failure is None and out.evaluation is not None, out.failure        # 옛 기대(봉인만)이면 봉인 3 실패 (red)
    rsnap = out.evaluation.snapshot
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(3e-6, rel=1e-12)
    _assert_input_rows(rsnap, layout_in)                                           # [A-139] 모든 MOS 행 = 레이아웃 입력 손가락 (옛 '빈 열' 폐기)
    v0, v1 = dict(snap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert (v1["inp"] + v1["inn"]) == pytest.approx(v0["inp"] + v0["inn"], abs=1e-9)        # 공통모드 고정 (반대칭 가중 전제)
    delta, _x = diff_pair_input_shift(r, VGS0, B, C, LAM)
    shift = abs((v1["inp"] - v1["inn"]) - (v0["inp"] - v0["inn"]))
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert shift >= delta / 2.0, (shift, delta)                                    # 공허 방지
    assert abs(shift - delta) <= tol, ("measured_shift_V", shift, "hand_delta_V", delta, "tol_V", tol)    # R-2 와 같은 tol (바꾸지 않음)
    assert all(seal_item(rsnap, n).status == "pass" for n in (3, 7))


def test_layout_resolve_r13b_input_fixed_branch_follows_the_output_fixed_point(tmp_path):
    from gmid_engine.search import evaluate
    from sizing.conftest import LAM, seal_item
    from search.wb1_flow import (R6_ELEMENTS, R6_I, R6_R, R6_RBOUNDS, VDD, bins_case, circuit_r6, single_mos_resistor_theta, sorted_theta)
    from wb1_hand import source_load_out_shift
    i, rr = R6_I, R6_R                                                             # θ 입력: V(out)_사이징 = I·R = 0.75 V = a (회로 = M1 pmos 소스 vdd, dispute 7.1)
    case = bins_case(tmp_path, circuit_r6(), elements=R6_ELEMENTS, rbounds=R6_RBOUNDS)
    ev = evaluate(case.sctx, sorted_theta(single_mos_resistor_theta(case.dc, i, rr, VDD - i * rr, kind="pmos")), (0,))
    snap = ev.evaluation.snapshot
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")                              # 전제 (base 재확인): 입력 고정 갈래
    w = dict(snap.column("device", "dc_op"))["M1"].W
    r = 18 * 2e-6 / w - 1.0                                                        # 레이아웃 M1 = (nf 18, finger_w 2e-6): r ≈ 0.5 (손)
    assert 0.4 <= r <= 0.7
    a = dict(snap.column("node", "dc_v"))["out"]
    hand = source_load_out_shift(a, r, LAM)                                        # 손: ΔV(out) = a·[(1 + r)·e^{−LAM·ΔV} − 1]
    assert VDD - (a + hand) > 0.455                                                # 전제 (손): 재풀이 점에서도 M1 포화 (VSD >= VDSAT_p(0.6))
    layout_in = _fingers(snap, M1=(2e-6, 18))
    out = evaluate(case.sctx, ev.theta, ev.key.cells, parent=ev, geometry=_geometry(layout_in))
    assert out.failure is None and out.evaluation is not None, out.failure        # 옛 기대(봉인만)이면 봉인 3 실패 (red)
    rsnap = out.evaluation.snapshot
    v0, v1 = dict(snap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert v1["in"] == pytest.approx(v0["in"], rel=1e-12)
    dv = v1["out"] - v0["out"]
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs(dv) >= abs(hand) / 2.0, (dv, hand)                                  # 공허 방지
    assert abs(dv - hand) <= tol, ("measured_dV_V", dv, "hand_dV_V", hand, "tol_V", tol)
    _assert_input_rows(rsnap, layout_in)
    assert all(seal_item(rsnap, n).status == "pass" for n in (3, 7))


# ---------------------------------------------------------------- L-2 (기대 변경 -- 개정 여섯째 A-139): 요청 대기 소자가 있는 레이아웃 뒤 재평가
# oracle (손) interface §10 L-2: R-2 회로, 레이아웃 M1 = 배치 (nf 3, finger_w 1e-6), M2 = 요청 대기 (nf 2, finger_w 1e-6; 요청 W 2e-6 의 finger_slice 답 (1, 2e-6) 과 다름),
# M3·M4 = 배치(사이징 점 손가락 그대로). 접합 기대값 = metrics conftest 의 독립 BSIM4 폐형식(`ref_caps`·`oracle_junction`)과 toy 선언 값(`TOY_JUNCTION`).
class CountFingerSlice:
    """`block_dc.finger_slice` 호출 수 (관찰 지점 §9)."""

    def __init__(self, monkeypatch):
        import sys
        self.mod = sys.modules["gmid_engine.sizing.block_dc"]
        self.orig, self.n = self.mod.finger_slice, 0
        monkeypatch.setattr(self.mod, "finger_slice", self)

    def __call__(self, *a, **k):
        self.n += 1
        return self.orig(*a, **k)


def _reason(failure):
    return {failure.failure_class, dict(failure.detail).get("reason")}


def _l2_start(tmp_path, monkeypatch):
    from gmid_engine.search import evaluate
    from search.wb1_flow import R2_CELLS, R2_ELEMENTS, bins_case, circuit_r2, r2_theta, sorted_theta
    counter = CountFingerSlice(monkeypatch)
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS)
    ev = evaluate(case.sctx, sorted_theta(r2_theta(case.dc)), R2_CELLS)
    assert counter.n >= 1                                                           # 양성 대조: 탐색 평가는 선택 함수를 부른다
    counter.n = 0
    snap = ev.evaluation.snapshot
    nat = dict(snap.column("device", "dc_finger"))
    assert (nat["M2"].m, round(nat["M2"].w_f_m / GRID)) == (1, 200)                 # 전제 (손): 요청 W 2e-6 의 자연 선택 = (1, 2e-6) != 요청 (2, 1e-6)
    return case, ev, counter


def test_layout_resolve_l2_waiting_device_row_is_the_request_and_junction_follows_two_places(tmp_path, monkeypatch):
    from gmid_engine.search import evaluate
    from metrics.conftest import JUNCTION_RTOL, toy_rule_values
    from sizing.wb1_toy import JC1_CDD, JC1_CGD, JC1_CGS, JC1_CSS
    case, ev, counter = _l2_start(tmp_path, monkeypatch)
    snap = ev.evaluation.snapshot
    placed = _fingers(snap, M1=(1e-6, 3))
    placed.pop("M2")
    out = evaluate(case.sctx, ev.theta, ev.key.cells, parent=ev, geometry=_geometry(placed, {"M2": (1e-6, 2)}))
    assert out.failure is None and out.evaluation is not None, out.failure         # base = KeyError (분류되지 않은 예외) -- red
    assert counter.n == 0                                                           # 그 평가 finger_slice 호출 0 (요청 W 로 다시 고르지 않음)
    rsnap = out.evaluation.snapshot
    _assert_input_rows(rsnap, {**placed, "M2": (1e-6, 2)})                          # 배치 = layout_ref (nf, finger_w, 0.0), 요청 대기 M2 = 요청 행 (2, 1e-6, 0.0)
    ops, ss = dict(rsnap.column("device", "dc_op")), dict(rsnap.column("device", "ss_dev"))
    assert ops["M2"].W == pytest.approx(2e-6, rel=1e-12) and ops["M2"].w_key == 100  # W' = nf·finger_w, 슬라이스 = slice_of_finger(1e-6)
    tol = JUNCTION_RTOL
    # [JC-1] 접합 기대값 = 정의 문장: (CDD − CGD)·r_d, (CSS − CGS)·r_s -- 합성 r4 LUT 의 접합 입력 열은 모든 점 같은 상수(JC1_*), r = (면적·m)/(규칙 비율·w_ref·1)
    rule, w_ref = toy_rule_values(), 1e-6
    d_cap, s_cap = JC1_CDD - JC1_CGD, JC1_CSS - JC1_CGS
    # 배치 소자 M1 접합 = layout_ref 확산 값 (ad = as = 3e-13, m = nf = 3)
    cdb1 = d_cap * ((3e-13 * 3.0) / ((rule["ad_per_w"] * w_ref) * 1.0))
    csb1 = s_cap * ((3e-13 * 3.0) / ((rule["as_per_w"] * w_ref) * 1.0))
    assert ss["M1"].junction_model == "lut_vgs_min_layout_area"
    assert ss["M1"].cdb == pytest.approx(cdb1, rel=tol) and ss["M1"].csb == pytest.approx(csb1, rel=tol)
    # 요청 대기 소자 M2 접합 = 그 평가가 쓴 W (2e-6) 의 레이아웃 전 규칙 기하 -- dc_finger (2, 1e-6) 아님(둘째 폭 m·w_s 0)
    cdb2 = d_cap * ((rule["ad_per_w"] * ops["M2"].W * 1.0) / ((rule["ad_per_w"] * w_ref) * 1.0))
    csb2 = s_cap * ((rule["as_per_w"] * ops["M2"].W * 1.0) / ((rule["as_per_w"] * w_ref) * 1.0))
    assert ss["M2"].junction_model == "lut_vgs_min_rule_area"
    assert ss["M2"].cdb == pytest.approx(cdb2, rel=tol) and ss["M2"].csb == pytest.approx(csb2, rel=tol)
    assert cdb1 != cdb2 and csb1 != csb2                                            # 공허 방지: 두 자리의 기대값이 다르다


def test_layout_resolve_l2_device_without_input_finger_row_is_realized_finger_missing(tmp_path, monkeypatch):
    """입력 손가락 행 없는 소자(M3: 배치도 요청도 아님) -> `realized_finger_missing` (분류된 후보 실패). 사이징 점 스냅샷에는 M3 행이 있다 -- 그 행을 읽으면 통과해 red."""
    from gmid_engine.search import evaluate
    case, ev, counter = _l2_start(tmp_path, monkeypatch)
    snap = ev.evaluation.snapshot
    assert "M3" in dict(snap.column("device", "dc_finger"))                         # 전제: 읽을 수 있는 사이징 점 행이 있다
    placed = _fingers(snap, M1=(1e-6, 3))
    placed.pop("M2")
    placed.pop("M3")
    out = evaluate(case.sctx, ev.theta, ev.key.cells, parent=ev, geometry=_geometry(placed, {"M2": (1e-6, 2)}))
    assert out.failure is not None and out.evaluation is None, out
    assert "realized_finger_missing" in _reason(out.failure)
    assert counter.n == 0


# [JC-1] 접합 입력에서 대기 소자 dc_finger 행을 지운 꼴의 `realized_finger_missing` test 는 폐기됐다 -- card 범위: `ss_dev` 가 `dc_finger` 를 읽지 않는다
# (tests/RETIRED_TESTS_jc1.md). 짝 test(입력 손가락 행 없는 소자)는 정지 자리가 `block_dc` 실현 입력 손가락 관문이라 유지.


def test_geometry_device_class_helper_is_not_defined_anywhere():
    """부류 helper `geometry_device_class` 정의·호출 0 (소스 grep -- 엔진 소스, tests 제외)."""
    root = Path(__file__).resolve().parents[2]
    files = [p for p in root.rglob("*.py") if "tests" not in p.relative_to(root).parts]
    assert len(files) > 50                                                          # 양성 대조: 엔진 소스를 실제로 훑었다
    assert [str(p) for p in files if "geometry_device_class" in p.read_text(encoding="utf-8")] == []
