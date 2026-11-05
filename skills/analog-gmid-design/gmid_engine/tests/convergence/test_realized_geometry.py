"""`realized_geometry(snapshot, placements) -> sizing.RealizedGeometry(layout_ref, w_request)` (CONTRACT 4절, 계획 LY7·LY8, WB-1 §3·§8).

oracle (a): 손으로 만든 배치·확산 기하 -- w_request = 배치 소자 전부(이름순, Placement.W_m), layout_ref = `ly_diffusion` 필드 중 pending 아닌 소자의
(finger_w, ad, as, pd, ps, m = float(nf)) 참조. [WB-1] 폭 키(kind당 슬라이스) 인자·칸은 없다: 인자는 (snapshot, placements) 둘, 값 칸은 (layout_ref, w_request) 둘.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest

from gmid_engine.convergence import realized_geometry
from gmid_engine.metrics import DiffusionGeometry
from gmid_engine.sizing import RealizedGeometry

from .conftest import ddiff, layout, placement


def test_all_placed_devices_fixed_and_pending_diffusion_dropped():
    pl = (placement("A", 100, 3, 3e-6), placement("B", 50, 2, 1e-6, pending=True), placement("C", 70, 1, 7e-7))
    diff = (ddiff("C", 7e-7, 1, 1e-13, 2e-13, 1.5e-6, 2.5e-6), ddiff("A", 1e-6, 3, 3e-13, 4e-13, 2.0e-6, 3.0e-6),
            ddiff("B", 9e-7, 4, 5e-13, 6e-13, 1.1e-6, 1.2e-6))
    g = realized_geometry(layout(diffusion=diff).snapshot, pl)
    assert isinstance(g, RealizedGeometry)
    assert g.w_request == (("A", 3e-6), ("B", 1e-6), ("C", 7e-7))       # LY7: pending 포함 모든 배치 소자
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
def _geometry(snap, **placed):
    """레이아웃 뒤 기하: 사이징 점 스냅샷의 손가락(m·w_s)을 모든 MOS 에 그대로 놓고, 키워드 {소자: (finger_w, nf)} 만 바꾼다.
    W' = nf·finger_w, 접합 ad/as/pd/ps 는 DC 와 무관한 손 값. (layout_ref, w_request) = realized_geometry 와 같은 꼴(전 배치 소자)."""
    from gmid_engine.metrics import DiffusionGeometry
    from gmid_engine.sizing import RealizedGeometry
    fingers = {m: (f.w_f_m, f.m) for m, f in dict(snap.column("device", "dc_finger")).items()}
    fingers.update(placed)
    return RealizedGeometry(tuple((m, DiffusionGeometry(fw, 3e-13, 3e-13, 4e-6, 4e-6, float(nf))) for m, (fw, nf) in sorted(fingers.items())),
                            tuple((m, nf * fw) for m, (fw, nf) in sorted(fingers.items())))


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
    out = evaluate(case.sctx, ev.theta, ev.key.cells, parent=ev, geometry=_geometry(snap, M1=(1e-6, 3)))
    assert out.failure is None and out.evaluation is not None, out.failure        # 옛 기대(봉인만)이면 봉인 3 실패 (red)
    rsnap = out.evaluation.snapshot
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(3e-6, rel=1e-12)
    assert dict(rsnap.column("device", "dc_finger")) == {}                         # 'geometry 있음': dc_finger 빈 열
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
    out = evaluate(case.sctx, ev.theta, ev.key.cells, parent=ev, geometry=_geometry(snap, M1=(2e-6, 18)))
    assert out.failure is None and out.evaluation is not None, out.failure        # 옛 기대(봉인만)이면 봉인 3 실패 (red)
    rsnap = out.evaluation.snapshot
    v0, v1 = dict(snap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert v1["in"] == pytest.approx(v0["in"], rel=1e-12)
    dv = v1["out"] - v0["out"]
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs(dv) >= abs(hand) / 2.0, (dv, hand)                                  # 공허 방지
    assert abs(dv - hand) <= tol, ("measured_dV_V", dv, "hand_dV_V", hand, "tol_V", tol)
    assert dict(rsnap.column("device", "dc_finger")) == {}
    assert all(seal_item(rsnap, n).status == "pass" for n in (3, 7))
