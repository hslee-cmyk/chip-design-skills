"""helper `_helpers_seal`(`judge`·`node_values`) -- CONTRACT 6절 judge 규칙. helper 는 비공개라 공개 봉인 블록으로 확인한다.

judge(item, rows): tol 정의 행 중 크기 > tol 있으면 fail(대상 = 그 행들), 없고 tol None 행 있으면 undefined, 그 밖 pass.
magnitude·tol·margin = margin(크기/tol, tol 0 이면 무한) 최대 행(fail 이면 fail 행 중), 행 없으면 None.
detail = n_checked·n_undefined·worst 키 정렬. node_values: 레일 = dc_rail_v, 그 밖 = dc_v.
"""
import dataclasses
import math

from gmid_engine.sizing import dc_seal_bulk_reverse, dc_seal_node_conflict, dc_seal_vgs_match

from .conftest import node_voltages, seal_item, tamper, theta_c, with_tol


def test_tol_zero_gives_infinite_margin_fail(ctx_c):
    """계약 6절 judge: 'margin(크기/tol, tol 0 이면 무한)'. (실행 2026-10-07: margin None 을 낸다 -- 계약과 불일치, 보고)"""
    snap, _ = with_tol(ctx_c[2], theta_c())
    ops = dict(snap.column("device", "dc_op"))
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": 0.0})
    s2 = tamper(s2, "dc_widths", "device", "dc_op",
                {"M1": dataclasses.replace(ops["M1"], idu_forward=ops["M1"].idu_forward * 1.001)})
    item = seal_item(dc_seal_vgs_match(s2), 2)
    assert item.status == "fail" and item.tol == 0.0
    assert item.margin is not None and math.isinf(item.margin), "tol 0 행의 margin 은 무한이어야 한다(계약 6절)"
    assert item.devices == ("M1",)


def test_zero_magnitude_zero_tol_is_pass(ctx_c):
    """크기 0, tol 0: 0 > 0 이 아니므로 fail 아님(bulk 역바이어스 0 인 소자)."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": 0.0, "M2": 0.0})
    item = seal_item(dc_seal_bulk_reverse(s2), 6)
    assert item.status == "pass"


def test_fail_targets_only_failing_rows(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    ops = dict(snap.column("device", "dc_op"))
    s2 = tamper(snap, "dc_widths", "device", "dc_op",
                {"M2": dataclasses.replace(ops["M2"], idu_forward=ops["M2"].idu_forward * 3.0)})
    s2 = tamper(s2, "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    item = seal_item(dc_seal_vgs_match(s2), 2)
    d = dict(item.detail)
    assert item.status == "fail" and item.devices == ("M2",)            # undefined 행(M1)은 fail 대상 아님
    assert d["n_checked"] == 2 and d["n_undefined"] == 1 and d["worst"] == "M2"
    assert [k for k, _ in item.detail] == sorted(d)


def test_undefined_targets_and_pass_reports_worst(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    item = seal_item(dc_seal_vgs_match(s2), 2)
    assert item.status == "undefined" and item.devices == ("M1",)
    ok = seal_item(dc_seal_vgs_match(snap), 2)
    assert ok.status == "pass" and ok.devices == () and ok.nodes == ()
    assert ok.margin is not None and ok.margin <= 1


def test_node_values_use_rail_value_on_rails(ctx_c):
    """레일 노드 값 = dc_rail_v: 레일 path 값을 바꾸면 그 레일 행의 spread 가 정확히 그 차."""
    from gmid_engine.sizing import PathValue
    snap, _ = with_tol(ctx_c[2], theta_c())
    pv = dict(snap.column("node", "dc_path_values"))["gnd"]
    new = tuple(PathValue(p.relation, 0.2) if p.relation == ("vgs", "M1") else p for p in pv)
    s2 = tamper(snap, "dc_columns", "node", "dc_path_values", {"gnd": new})
    item = seal_item(dc_seal_node_conflict(s2), 1)
    assert item.status == "fail" and item.nodes == ("gnd",)
    assert abs(item.magnitude - 0.2) <= 1e-15
    assert node_voltages(snap)["gnd"] == 0.0
