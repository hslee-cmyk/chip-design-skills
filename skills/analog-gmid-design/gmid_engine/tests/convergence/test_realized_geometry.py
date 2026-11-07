"""`realized_geometry(snapshot, placements) -> sizing.RealizedGeometry(layout_ref, w_request)` (CONTRACT 4절, 계획 LY7·LY8, WB-1 §3·§8).

oracle (a): 손으로 만든 배치·확산 기하 -- w_request = 요청 대기(pending) 소자의 요청 손가락 행 참조(A-139, 배치 소자는 두지 않음), layout_ref = `ly_diffusion` 필드 중 pending 아닌 소자의
(finger_w, ad, as, pd, ps, m = float(nf)) 참조. [WB-1] 폭 키(kind당 슬라이스) 인자·칸은 없다: 인자는 (snapshot, placements) 둘, 값 칸은 (layout_ref, w_request) 둘.

[FS-1] 옛 R-13a·R-13b·L-2 (레이아웃 뒤 재평가) test 4개는 '탐색 스냅샷 dc_finger (m, w_f_m) 를 레이아웃 입력으로 놓고 finger_slice 호출 0 을 센다' 는 구성이라 삭제했다
(tests/RETIRED_TESTS_fs1.md). 레이아웃 뒤 평가의 새 입력(요청 행 (nf, finger_w) -> `slice_of_finger`, 없는 소자 = 기준(실현) 스냅샷 dc_finger.m·w_key)은
tests/sizing/test_block_dc.py D-7 이 함수 수준으로 본다.
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


def test_geometry_device_class_helper_is_not_defined_anywhere():
    """부류 helper `geometry_device_class` 정의·호출 0 (소스 grep -- 엔진 소스, tests 제외)."""
    root = Path(__file__).resolve().parents[2]
    files = [p for p in root.rglob("*.py") if "tests" not in p.relative_to(root).parts]
    assert len(files) > 50                                                          # 양성 대조: 엔진 소스를 실제로 훑었다
    assert [str(p) for p in files if "geometry_device_class" in p.read_text(encoding="utf-8")] == []


# =====================================================================================================================
# [FS-1 A-191 M-5] 레이아웃 뒤 재평가 (interface §4.4) 의 물리·fail-closed 성질을 새 입력 꼴로 다시 쓴다.
# 입력 꼴 = D-7: 기준(실현) 스냅샷 `RealizeInput(base)` + 레이아웃 요청 행/배치. 기준 = 사이징 점을 `realize_front` 로 실현한 점(손가락 m 정수).
# 이 꼴에서는 레이아웃이 소자 하나만 W' 를 바꿀 수 있어(요청 행 (nf, finger_w)) 옛 R-13a 의 비대칭 입력 차 이동이 다시 만들어진다.
# 기대값: 옛 test 와 같은 `wb1_hand` 독립 해 (r = W'/W_기준 − 1 은 스냅샷에서 읽는다).
# =====================================================================================================================
def _geometry(fingers, requested=None):
    """공개 `realized_geometry(snapshot, placements)` 로 만든 레이아웃 뒤 기하. fingers = 배치 {소자: (finger_w, nf)}, requested = 요청 대기 {소자: (finger_w, nf)}.
    W' = nf·finger_w, 접합 ad/as/pd/ps 는 DC 와 무관한 손 값."""
    requested = requested or {}
    pl = [placement(m, round(fw / GRID), nf, nf * fw) for m, (fw, nf) in sorted(fingers.items())]
    pl += [placement(m, round(fw / GRID), nf, nf * fw, pending=True) for m, (fw, nf) in sorted(requested.items())]
    diff = tuple(ddiff(m, fw, nf, 3e-13, 3e-13, 4e-6, 4e-6) for m, (fw, nf) in sorted(fingers.items()))
    return realized_geometry(layout(diffusion=diff).snapshot, tuple(pl))


def _realized_base(case, ev):
    """사이징 점 ev 를 실현한 점 (공개 realize_front) -> 그 EvalResult. 실현이 점을 잃으면 멈추고 보고."""
    from gmid_engine.search import FrontPoint, realize_front
    out = realize_front(case.sctx, (FrontPoint("base", ev, ()),))
    assert len(out.points) == 1 and out.lost == (), ("기준 실현 점 불성립 -- 멈추고 보고", out.lost)
    return out.points[0].result


def _reeval(case, ev, base, geometry):
    from gmid_engine.sizing import RealizeInput
    from search.conftest import evaluate
    return evaluate(case.sctx, ev.theta, ev.key.cells, parent=base, geometry=geometry, realized=RealizeInput(base.evaluation.snapshot))


def test_layout_resolve_r13a_servo_branch_follows_the_vgs2_fixed_point(tmp_path):
    from sizing.conftest import B, C, LAM, seal_item
    from search.wb1_flow import R2_CELLS, R2_ELEMENTS, VGS0, bins_case, circuit_r2, r2_theta, sorted_theta
    from search.conftest import evaluate
    from wb1_hand import diff_pair_input_shift
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS)
    ev = evaluate(case.sctx, sorted_theta(r2_theta(case.dc)), R2_CELLS)
    base = _realized_base(case, ev)
    bsnap = base.evaluation.snapshot
    bops = dict(bsnap.column("device", "dc_op"))
    assert bops["M1"].vgs == pytest.approx(VGS0, abs=1e-6)
    cfg = next(iter(dict(ev.evaluation.snapshot.column("graph", "icm_config")).values()))
    assert cfg.config == "servo"                                                    # 전제 (미측정): R-2 회로 servo 갈래
    r = 3e-6 / bops["M1"].W - 1.0                                                   # 레이아웃 M1 = (nf 3, finger_w 1e-6): W' = 3e-6, 기준 W' = bops["M1"].W
    assert r == pytest.approx(0.5, abs=2e-3)
    out = _reeval(case, ev, base, _geometry({"M1": (1e-6, 3)}))
    assert out.failure is None and out.evaluation is not None, out.failure
    rsnap = out.evaluation.snapshot
    rops = dict(rsnap.column("device", "dc_op"))
    assert rops["M1"].W == pytest.approx(3e-6, rel=1e-12) and rops["M1"].w_key == 100
    for m in ("M2", "M3", "M4"):                                                    # 요청 없는 소자 = 기준 스냅샷 그대로 (m·w_key·grid)
        assert rops[m].W == bops[m].W and rops[m].w_key == bops[m].w_key
    v0, v1 = dict(bsnap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert (v1["inp"] + v1["inn"]) == pytest.approx(v0["inp"] + v0["inn"], abs=1e-9)         # 공통모드 고정 (반대칭 가중 전제)
    delta, _x = diff_pair_input_shift(r, VGS0, B, C, LAM)
    shift = abs((v1["inp"] - v1["inn"]) - (v0["inp"] - v0["inn"]))
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert shift >= delta / 2.0, (shift, delta)                                     # 공허 방지
    assert abs(shift - delta) <= tol, ("measured_shift_V", shift, "hand_delta_V", delta, "tol_V", tol)    # R-2 와 같은 tol (바꾸지 않음)
    assert all(seal_item(rsnap, n).status == "pass" for n in (3, 7))


def test_layout_resolve_r13b_input_fixed_branch_follows_the_output_fixed_point(tmp_path):
    from sizing.conftest import LAM, seal_item
    from search.wb1_flow import R6_ELEMENTS, R6_I, R6_R, R6_RBOUNDS, VDD, bins_case, circuit_r6, single_mos_resistor_theta, sorted_theta
    from search.conftest import evaluate
    from wb1_hand import source_load_out_shift
    i, rr = R6_I, R6_R                                                              # V(out)_사이징 = I·R = 0.75 V = a
    case = bins_case(tmp_path, circuit_r6(), elements=R6_ELEMENTS, rbounds=R6_RBOUNDS)
    ev = evaluate(case.sctx, sorted_theta(single_mos_resistor_theta(case.dc, i, rr, VDD - i * rr, kind="pmos")), (0,))
    base = _realized_base(case, ev)
    bsnap = base.evaluation.snapshot
    cfg = next(iter(dict(ev.evaluation.snapshot.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")                               # 전제: 입력 고정 갈래
    w = dict(bsnap.column("device", "dc_op"))["M1"].W
    r = 18 * 2e-6 / w - 1.0                                                         # 레이아웃 M1 = (nf 18, finger_w 2e-6): r ≈ 0.5 (손, 기준 W' 기준)
    assert 0.4 <= r <= 0.7
    a = dict(bsnap.column("node", "dc_v"))["out"]
    hand = source_load_out_shift(a, r, LAM)
    assert VDD - (a + hand) > 0.455                                                 # 전제 (손): 재풀이 점에서도 M1 포화
    out = _reeval(case, ev, base, _geometry({"M1": (2e-6, 18)}))
    assert out.failure is None and out.evaluation is not None, out.failure
    rsnap = out.evaluation.snapshot
    v0, v1 = dict(bsnap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert v1["in"] == pytest.approx(v0["in"], rel=1e-12)
    dv = v1["out"] - v0["out"]
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs(dv) >= abs(hand) / 2.0, (dv, hand)
    assert abs(dv - hand) <= tol, ("measured_dV_V", dv, "hand_dV_V", hand, "tol_V", tol)
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(36e-6, rel=1e-12)
    assert all(seal_item(rsnap, n).status == "pass" for n in (3, 7))


def _l2_start(tmp_path):
    from search.wb1_flow import R2_CELLS, R2_ELEMENTS, bins_case, circuit_r2, r2_theta, sorted_theta
    from search.conftest import evaluate
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS)
    ev = evaluate(case.sctx, sorted_theta(r2_theta(case.dc)), R2_CELLS)
    return case, ev, _realized_base(case, ev)


def test_layout_resolve_l2_waiting_device_row_is_the_request_and_junction_follows_two_places(tmp_path):
    """L-2: M1 = 배치 (nf 3, 1e-6), M2 = 요청 대기 (nf 4, 1e-6) -- 기준 실현 m(2) 과 다른 요청 (W' 4e-6 != 기준 2e-6), M3·M4 = 기준 스냅샷 그대로.
    M2 접합 = 그 평가가 쓴 W 의 레이아웃 전 규칙 기하, M1 접합 = 배치 확산 값. oracle (손): 합성 r4 LUT 접합 입력 열 상수(JC1_*)."""
    from metrics.conftest import JUNCTION_RTOL, toy_rule_values
    from sizing.wb1_toy import JC1_CDD, JC1_CGD, JC1_CGS, JC1_CSS
    case, ev, base = _l2_start(tmp_path)
    bops = dict(base.evaluation.snapshot.column("device", "dc_op"))
    assert bops["M2"].W != 4e-6                                                     # 전제: 요청 (nf 4: W' 4e-6) 이 기준 (2e-6) 과 다르다 (공허 방지)
    out = _reeval(case, ev, base, _geometry({"M1": (1e-6, 3)}, {"M2": (1e-6, 4)}))   # nf 4: csb2 = 4·s_cap != csb1 = 3·s_cap (nf 3 이면 csb 가 두 자리를 못 가른다 -- 판정 MR-2a)
    assert out.failure is None and out.evaluation is not None, out.failure
    rsnap = out.evaluation.snapshot
    ops, ss = dict(rsnap.column("device", "dc_op")), dict(rsnap.column("device", "ss_dev"))
    assert ops["M2"].W == pytest.approx(4e-6, rel=1e-12) and ops["M2"].w_key == 100       # W' = nf·finger_w, 슬라이스 = slice_of_finger(1e-6)
    assert ops["M1"].W == pytest.approx(3e-6, rel=1e-12)
    for m in ("M3", "M4"):
        assert ops[m].W == bops[m].W
    tol = JUNCTION_RTOL
    rule, w_ref = toy_rule_values(), 1e-6
    d_cap, s_cap = JC1_CDD - JC1_CGD, JC1_CSS - JC1_CGS
    cdb1 = d_cap * ((3e-13 * 3.0) / ((rule["ad_per_w"] * w_ref) * 1.0))
    csb1 = s_cap * ((3e-13 * 3.0) / ((rule["as_per_w"] * w_ref) * 1.0))
    assert ss["M1"].junction_model == "lut_vgs_min_layout_area"
    assert ss["M1"].cdb == pytest.approx(cdb1, rel=tol) and ss["M1"].csb == pytest.approx(csb1, rel=tol)
    cdb2 = d_cap * ((rule["ad_per_w"] * ops["M2"].W * 1.0) / ((rule["ad_per_w"] * w_ref) * 1.0))
    csb2 = s_cap * ((rule["as_per_w"] * ops["M2"].W * 1.0) / ((rule["as_per_w"] * w_ref) * 1.0))
    assert ss["M2"].junction_model == "lut_vgs_min_rule_area"
    assert ss["M2"].cdb == pytest.approx(cdb2, rel=tol) and ss["M2"].csb == pytest.approx(csb2, rel=tol)
    assert cdb1 != cdb2 and csb1 != csb2                                            # 공허 방지: 두 자리의 기대값이 다르다 (옛 단언 그대로, AND)


def test_layout_resolve_l2_device_without_input_finger_row_is_realized_finger_missing(tmp_path):
    """기준(실현) 스냅샷에 dc_finger 행이 없는 소자(M3: 요청도 배치도 아님) -> `realized_finger_missing` (분류된 후보 실패, KeyError 아님). 기준 행을 지운 스냅샷이 입력."""
    from gmid_engine.sizing import DC_SOLVE_WRITER, RealizeInput
    from sizing.conftest import column_dict
    from search.conftest import evaluate
    case, ev, base = _l2_start(tmp_path)
    bsnap = base.evaluation.snapshot
    col = column_dict(bsnap, "device", "dc_finger")
    assert "M3" in col                                                              # 전제: 지울 행이 있다
    col.pop("M3")
    broken = bsnap.write(DC_SOLVE_WRITER, "tampered", {("device", "dc_finger"): col})
    out = evaluate(case.sctx, ev.theta, ev.key.cells, parent=base, geometry=_geometry({"M1": (1e-6, 3)}, {"M2": (1e-6, 3)}), realized=RealizeInput(broken))
    assert out.failure is not None and out.evaluation is None, out
    assert "realized_finger_missing" in {out.failure.failure_class, dict(out.failure.detail).get("reason")}
