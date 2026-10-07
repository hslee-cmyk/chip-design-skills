"""봉인 5 `seal_writers(snapshot)` -- CONTRACT 6절: 모든 필드 writer == 권한표 writer; 노드마다 dc_writer 있음,
(tier == W0) == is_rail, dc_rail_v·dc_v 중 정확히 하나, dc_rail_v 있음 == is_rail. 위반 노드 = nodes, 위반 필드 = detail fields.
위반은 권한표 writer 로 열을 바꿔 써서 만든다(권한표 밖 writer 쓰기는 core 가 막으므로 첫 조건은 정상 경로에서 늘 참).
"""
import dataclasses

from gmid_engine.sizing import SealItem, seal_writers

from .conftest import column_dict, eval_calls, tamper, theta_c


def test_pass(ev_c):
    item = seal_writers(ev_c.snapshot)
    assert isinstance(item, SealItem) and item.item == 5
    assert item.status == "pass" and item.nodes == ()
    assert dict(item.detail)["fields"] == ()
    assert item.magnitude == 0


def test_rail_with_dc_v(ctx_c):
    snap, _ = eval_calls(ctx_c[2], theta_c())
    bad = tamper(snap, "dc_columns", "node", "dc_v", {"vdd": 1.8})
    item = seal_writers(bad)
    assert item.status == "fail"
    assert "vdd" in item.nodes and set(item.nodes) == {"vdd"}


def test_non_rail_with_rail_value(ctx_c):
    snap, _ = eval_calls(ctx_c[2], theta_c())
    bad = tamper(snap, "dc_rails", "node", "dc_rail_v", {"out": 0.9})
    item = seal_writers(bad)
    assert item.status == "fail" and set(item.nodes) == {"out"}


def test_node_without_value(ctx_c):
    snap, _ = eval_calls(ctx_c[2], theta_c())
    col = column_dict(snap, "node", "dc_v")
    del col["pb"]
    bad = snap.write("dc_columns", "tampered", {("node", "dc_v"): col})
    item = seal_writers(bad)
    assert item.status == "fail" and set(item.nodes) == {"pb"}


def test_node_without_writer_plan(ctx_c):
    snap, _ = eval_calls(ctx_c[2], theta_c())
    col = column_dict(snap, "node", "dc_writer")
    del col["in"]
    bad = snap.write("dc_writer_plan", "tampered", {("node", "dc_writer"): col})
    item = seal_writers(bad)
    assert item.status == "fail" and "in" in item.nodes


def test_tier_rail_mismatch(ctx_c):
    snap, _ = eval_calls(ctx_c[2], theta_c())
    w = dict(snap.column("node", "dc_writer"))["out"]
    bad = tamper(snap, "dc_writer_plan", "node", "dc_writer", {"out": dataclasses.replace(w, tier="W0")})
    item = seal_writers(bad)
    assert item.status == "fail" and set(item.nodes) == {"out"}
    w2 = dict(snap.column("node", "dc_writer"))["gnd"]
    bad2 = tamper(snap, "dc_writer_plan", "node", "dc_writer", {"gnd": dataclasses.replace(w2, tier="W2")})
    assert set(seal_writers(bad2).nodes) == {"gnd"}
