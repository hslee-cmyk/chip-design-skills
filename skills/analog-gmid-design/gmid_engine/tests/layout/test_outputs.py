"""CONTRACT 4.12 5~8·4.13 11·4.14 `layout_outputs(snapshot) -> LayoutOutputs` -- 레이아웃 필드 -> 출력 계약 파생 항목 (규칙 H 1:1, `outputs.py`).

[U17 1-e] design 40 v1.6 §2.4.7: `LayoutResult` 는 (스냅샷, 계산 블록 목록)뿐이고, 옛 결과 칸(review_needed·devices·coverage·w_requests·
w_invariant_ok·revalidation)은 필드에서 읽을 때 만드는 반환값이다. 이 파일은 그 파생 규칙 자체를 본다.

oracle (a): 레이아웃 필드 값(`ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`·`ly_slices`·`ly_finger`·`ly_groups`·`ly_rows`·`ly_diffusion`)을 손으로 만들어 `_ly_fields` 권한표의
빈 스냅샷에 쓰고, 기대 출력은 CONTRACT 4.12 5~8·4.14 의 규칙을 손으로 적용해 적는다(옛 test_run 의 손계산 oracle 과 같은 수:
C 의 finger_quantization 요청 0.75e-6 -> 1e-6, 없는 슬라이스 소자 Z 의 no_usable_slice 요청·coverage 누락). 계산 블록·run_layout 을 부르지 않는다.
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.core import GraphSnapshot
from gmid_engine.layout import LayoutOutputs, layout_outputs
from gmid_engine.layout import _ly_fields as lf
from gmid_engine.layout.contract_output import (
    REVALIDATION_CONSUMER,
    REVALIDATION_PENDING,
    REVALIDATION_PENDING_REASON,
    REVALIDATION_SEALS,
    BoxVerdict,
    DeviceDiffusion,
    DeviceFinger,
    DeviceLayout,
    GroupLayout,
    GroupRebuild,
    RealizedDevice,
    Revalidation,
    ReviewItem,
    RowLayout,
    RowsLayout,
    SliceDensity,
    WRequest,
)

from .conftest import W_INPUT, dev, input_device_columns

GRID = 1e-8
NO_ROOT = "lut_no_strong_inversion_root"


# ---------------------------------------------------------------- 손으로 만든 필드 값

def slice_ok(key, W_need):
    return SliceDensity(key, key * GRID, 0.5, 1.0, W_need, 0.0, "")


def slice_bad(key, reason=NO_ROOT):
    return SliceDensity(key, key * GRID, None, None, None, None, reason)


def finger(name, key, nf, W_need, origin="row", group=None, w_request=None, err=None, lower=None):
    fw = key * GRID
    W_real = nf * fw
    err_rel = abs(W_real - W_need) / W_need if err is None else err
    low = GRID / (2 * fw) if lower is None else lower
    eff = max(0.0, low)
    return DeviceFinger(name, key, fw, nf, W_need, W_real, err_rel, low, 0.0, eff, low > 0.0, err_rel <= eff, origin, group, w_request)


def group(gid, role, members, pattern=None, pending=False, reason="", dx=None, dy=None, w_requests=()):
    return GroupLayout(gid, role, tuple(members), pattern, None, None, None, (), (), None, None, None, dx, dy,
                       pattern is not None and dx == 0.0 and dy == 0.0, pending, pending, reason, (), tuple(w_requests))


def row(rid, devices, fw_key=100, group_=None):
    names = tuple(n for n, _ in devices)
    return RowLayout(rid, "rg", "nmos", fw_key, fw_key * GRID, 1e-6, tuple(devices), names, ("n",) * (len(names) + 1), (), "euler",
                     0, 1, True, group_, group_ is not None)


def rows_layout(rows, rebuilt=()):
    box = BoxVerdict(1.0, 1.0, 1e-6, 1e-6, rows[0].row_id if rows else "", rows[0].row_id if rows else "", ())
    return RowsLayout(tuple(rows), box, (), (), tuple(rebuilt))


def diffusion(name, fw, nf):
    return DeviceDiffusion(name, fw, nf, 1e-13, 2e-13, 1.5e-6, 2.5e-6)


def snapshot(devices, slices, fingers, groups, rows_, diffusions):
    """`_ly_fields` 권한표의 빈 스냅샷에 필드를 writer 별로 쓴다(값은 손계산). 입력 버전 문자열은 임의."""
    s = GraphSnapshot.empty(lf.LY_WRITERS)
    # [v1.11.2 O-39 (1)] 입력 소자 칸 = 네 필드(`ly_point`·`ly_pins`·`ly_w_adjustable`·`ly_attrs`, design 40 §2.4.8 옛 소자 통째 필드 삭제 행)
    s = s.write(W_INPUT, "in", input_device_columns(devices))
    s = s.write(lf.WRITER_SLICES, "sl", {(lf.DEVICE, lf.F_SLICES): dict(slices)})
    s = s.write(lf.WRITER_GROUPS, "gr", {(lf.GRAPH, lf.F_GROUPS): {lf.GRAPH_KEY: tuple(groups)}})
    s = s.write(lf.WRITER_FINGER, "fg", {(lf.DEVICE, lf.F_FINGER): {f.name: f for f in fingers}})
    return s.write(lf.WRITER_ROWS, "rw", {(lf.GRAPH, lf.F_ROWS): {lf.GRAPH_KEY: rows_},
                                          (lf.GRAPH, lf.F_DIFFUSION): {lf.GRAPH_KEY: tuple(diffusions)}})


# 손 시나리오: 차동쌍 g1(A·B, 배치됨, B 는 diode), branch_symmetric g2(E·F, pattern None, 조정 불가 -> review, 재구성 기록이 dx·dy 를 덮는다),
# diff_pair g3(P·Q, W_request 응답 대기 -> review 아님, 그룹 요청 둘), mirror g4(I·J, pattern None -- CC 요구 role 아님 -> review 아님),
# C(finger_quantization 요청: W_need 0.75e-6, 실현 1e-6, err 1/3 > 실효 0.005), Z(사용 가능 슬라이스 없음 -> ly_finger 없음).
# WRequest(device, W_old_m, W_new_m, nf, finger_w_m, reason, group) -- W_new = nf x finger_w_m (계획 LY3·MOD7 스키마 v6.38.24, dispute 8.4)
C_REQ = WRequest("C", 0.75e-6, 1e-6, 1, 1e-6, "finger_quantization", None)
P_REQ = WRequest("P", 1e-6, 2e-6, 2, 1e-6, "cc_nf", "g3")
Q_REQ = WRequest("Q", 1e-6, 2e-6, 2, 1e-6, "cc_nf", "g3")


def scenario(with_z=True, c_request=True, rows_ok=True):
    devices = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6, diode=True), dev("C", "x", "y", 0.75e-6),
               dev("E", "p", "q", 1e-6, gate="gc"), dev("F", "r", "t", 1e-6, gate="gc"),
               dev("I", "i1", "i2", 1e-6), dev("J", "j1", "j2", 1e-6),
               dev("P", "pp", "pd", 1e-6), dev("Q", "qq", "qd", 1e-6)]
    slices = {n: (slice_ok(100, 2e-6), slice_ok(200, 2e-6)) for n in ("A", "B")}
    slices.update({n: (slice_ok(100, 1e-6), slice_bad(200)) for n in ("C", "E", "F", "I", "J", "P", "Q")})
    slices["C"] = (slice_ok(100, 0.75e-6), slice_ok(200, 0.75e-6))
    fingers = [finger("A", 100, 2, 2e-6, "group", "g1"), finger("B", 100, 2, 2e-6, "group", "g1"),
               finger("C", 100, 1, 0.75e-6, w_request=C_REQ if c_request else None),
               finger("E", 100, 1, 1e-6), finger("F", 100, 1, 1e-6), finger("I", 100, 1, 1e-6), finger("J", 100, 1, 1e-6),
               finger("P", 100, 1, 1e-6, "group", "g3"), finger("Q", 100, 1, 1e-6, "group", "g3")]
    groups = [group("g1", "diff_pair", ("A", "B"), pattern="common_centroid", dx=0.0, dy=0.0, reason="cc_same_W"),
              group("g2", "branch_symmetric", ("E", "F"), reason="w_not_adjustable", dx=1.0, dy=0.0),
              group("g3", "diff_pair", ("P", "Q"), pending=True, reason="w_request", w_requests=(P_REQ, Q_REQ)),
              group("g4", "mirror", ("I", "J"), reason="no_hub_net")]
    rows_ = [row("r1/g1", (("A", 2), ("B", 2)), group_="g1"),
             row("r2", (("E", 1), ("F", 1))), row("r3", (("C", 1), ("I", 1), ("J", 1))),
             row("r4", (("P", 1), ("Q", 1)) if rows_ok else (("P", 1), ("Q", 2)))]
    diffusions = [diffusion(n, 1e-6, nf) for n, nf in (("A", 2), ("B", 2), ("C", 1), ("E", 1), ("F", 1), ("I", 1), ("J", 1), ("P", 1))]
    if with_z:
        devices.append(dev("Z", "a", "b", 2e-6, gm_id=25.0, W=3e-6))
        slices["Z"] = (slice_bad(100), slice_bad(200))
    return devices, snapshot(devices, slices, fingers, groups, rows_layout(rows_, rebuilt=(GroupRebuild("g2", 2, "row_swap", 0.5, 0.0),)),
                             diffusions)


# ---------------------------------------------------------------- 4.12 5~8

def test_returns_layout_outputs_without_writing():
    _devs, snap = scenario()
    fp0, versions0 = snap.fp, dict(snap.block_versions)
    o = layout_outputs(snap)
    assert isinstance(o, LayoutOutputs)
    assert [f.name for f in dataclasses.fields(o)][0] == "review_needed"                   # Q8 (iv)
    assert snap.fp == fp0 and dict(snap.block_versions) == versions0                      # 반환값만, 필드에 저장하지 않는다
    assert layout_outputs(snap) == o                                                     # 같은 필드 -> 같은 출력


def test_review_needed_cc_roles_without_pattern_not_pending_dx_from_rebuild():
    # 4.12 6: groups 순, role ∈ CC_REQUIRED_ROLES ∧ pattern None ∧ not pending. g2 는 재구성 기록(GroupRebuild)의 dx·dy 를 쓴다(그룹 값 1.0 아님).
    # g1(배치됨)·g3(pending)·g4(mirror -- CC 요구 아님)는 대상 아님.
    _devs, snap = scenario()
    assert layout_outputs(snap).review_needed == (ReviewItem("g2", "branch_symmetric", "w_not_adjustable", 0.5, 0.0),)


def test_review_needed_uses_group_dx_dy_when_not_rebuilt():
    devices = [dev("E", "p", "q", 1e-6, gate="gc"), dev("F", "r", "t", 1e-6, gate="gc")]
    snap = snapshot(devices, {"E": (slice_ok(100, 1e-6),), "F": (slice_ok(100, 1e-6),)},
                    [finger("E", 100, 1, 1e-6), finger("F", 100, 1, 1e-6)],
                    [group("g2", "branch_symmetric", ("E", "F"), reason="branch_gate_differs", dx=None, dy=None)],
                    rows_layout([row("r2", (("E", 1), ("F", 1)))]), [])
    assert layout_outputs(snap).review_needed == (ReviewItem("g2", "branch_symmetric", "branch_gate_differs", None, None),)


def test_devices_name_order_fields_and_excluded_slices():
    # 4.12 5: 소자 이름순 DeviceLayout(이름, finger_w, nf, ((행 id, nf), ...) 행 id 순, W_m, W_need, 실현 W, err, lower, upper, effective,
    # grid_dominated, origin, excluded_slices). ly_finger 없는 Z 는 숫자 필드 None, rows ().
    devs, snap = scenario()
    o = layout_outputs(snap)
    assert [d.name for d in o.devices] == ["A", "B", "C", "E", "F", "I", "J", "P", "Q", "Z"]
    by = {d.name: d for d in o.devices}
    assert by["A"] == DeviceLayout("A", 1e-6, 2, (("r1/g1", 2),), 4e-6, 2e-6, 2e-6, 0.0, 0.005, 0.0, 0.005, True, "group", ())
    assert by["C"] == DeviceLayout("C", 1e-6, 1, (("r3", 1),), 4e-6, 0.75e-6, 1e-6, pytest.approx(1 / 3), 0.005, 0.0, 0.005, True, "row",
                                   ())
    assert by["E"].excluded_slices == ((200, NO_ROOT),)                                # reason 있는 슬라이스만 (키, 사유)
    assert by["Z"] == DeviceLayout("Z", None, None, (), 3e-6, None, None, None, None, None, None, None, None,
                                   ((100, NO_ROOT), (200, NO_ROOT)))
    assert by["B"].rows == (("r1/g1", 2),)


def test_w_requests_group_finger_and_no_usable_slice_sorted():
    # 4.12 5: 그룹 요청(ly_groups) + finger_quantization(ly_finger.w_request) + ly_finger 없는 소자마다 (이름, W_m, W_m, no_usable_slice, None),
    # (device, reason) 순.
    _devs, snap = scenario()
    assert layout_outputs(snap).w_requests == (C_REQ, P_REQ, Q_REQ, WRequest("Z", 3e-6, 3e-6, None, None, "no_usable_slice", None))   # no_usable_slice = 요청 손가락 없음


def test_coverage_missing_device_not_in_any_row():
    # 4.13 11: 모든 소자가 물리 행에 있으면 coverage_ok, 아니면 빠진 이름(정렬)
    _d, with_z = scenario()
    _d, without_z = scenario(with_z=False)
    assert (layout_outputs(with_z).coverage_ok, layout_outputs(with_z).coverage_missing) == (False, ("Z",))
    assert (layout_outputs(without_z).coverage_ok, layout_outputs(without_z).coverage_missing) == (True, ())


@pytest.mark.parametrize("case, expected", [
    ("all_placed_requested", True),        # 모든 소자 ly_finger 있음, 행 nf 합 == nf, C 는 허용오차 밖이지만 W_request 있음
    ("unplaced", False),                   # Z 에 ly_finger 없음
    ("row_sum_mismatch", False),           # Q 의 행 finger 합 2 != nf 1
    ("over_tolerance_no_request", False),  # C err 1/3 > 0.005 인데 요청 없음
])
def test_w_invariant_ok(case, expected):
    # 4.12 5·4.13 4: w_invariant_ok = 모든 소자가 ly_finger 를 갖고 (행별 nf 합 == nf) 이고 (err <= effective 또는 그 소자의 W_request 있음)
    kw = {"all_placed_requested": dict(with_z=False), "unplaced": dict(with_z=True),
          "row_sum_mismatch": dict(with_z=False, rows_ok=False), "over_tolerance_no_request": dict(with_z=False, c_request=False)}[case]
    _d, snap = scenario(**kw)
    assert layout_outputs(snap).w_invariant_ok is expected


def test_revalidation_realized_devices_name_order_diode_and_diffusion():
    # 4.14: Revalidation(required=True, status pending_wiring, seals, devices = 이름순 배치 소자 RealizedDevice, consumer, reason);
    # recalibrate_id = not diode, recompute_node_voltages = True, diffusion = 그 소자의 DeviceDiffusion(없으면 None).
    devs, snap = scenario()
    rv = layout_outputs(snap).revalidation
    assert isinstance(rv, Revalidation)
    assert (rv.required, rv.status, rv.seals, rv.consumer, rv.reason) == (
        True, REVALIDATION_PENDING, REVALIDATION_SEALS, REVALIDATION_CONSUMER, REVALIDATION_PENDING_REASON)
    assert [r.name for r in rv.devices] == ["A", "B", "C", "E", "F", "I", "J", "P", "Q"]       # Z 없음(배치 안 됨)
    by_in = {d.name: d for d in devs}
    by = {r.name: r for r in rv.devices}
    a = by_in["A"]
    assert by["A"] == RealizedDevice("A", "nmos", 100, 1e-6, 2, 2e-6, 2e-6, a.ID_A, a.gm_id, a.L_m, a.vds_V, a.vsb_V, True, True,
                                     diffusion("A", 1e-6, 2))
    assert by["B"].recalibrate_id is False and by["B"].recompute_node_voltages is True        # diode
    assert by["Q"].diffusion is None                                                           # ly_diffusion 에 없는 소자
    assert by["C"].W_need_m == 0.75e-6 and by["C"].W_realized_m == 1e-6
