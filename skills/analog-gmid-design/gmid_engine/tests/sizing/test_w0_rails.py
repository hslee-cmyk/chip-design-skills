"""`dc_rails(snapshot, supplies)` -- CONTRACT 4.1: reads node.is_rail, writes node.dc_rail_v = 레일마다 float(supplies 값).
레일 아닌 노드에는 dc_rail_v 가 없다(봉인 5: 한 노드에 dc_rail_v·dc_v 중 하나).
[XRUN-F1 card B C4] 블록 호출은 두 키워드 필수 -- test 함수 하나 = 실행 하나(open_run() 한 쌍).
"""
import pytest

from gmid_engine.graph import build_s1
from gmid_engine.search import open_run
from gmid_engine.sizing import DC_KEY, dc_rails, lift_s1

from .conftest import SUPPLIES, block_row, circuit_cs_pmos_load, load_doc, mos, topo


def _run():
    donors, counters = open_run()
    return dict(donors=donors, counters=counters)


def _lifted(tmp_path, doc, supplies, run):
    return lift_s1(build_s1(load_doc(tmp_path, doc), dict(supplies), **run))


def test_rails_get_float_values_only(tmp_path):
    run = _run()
    base = _lifted(tmp_path, circuit_cs_pmos_load(), SUPPLIES, run)
    out = dc_rails(base, (("gnd", 0), ("vdd", 1.8)), **run)
    col = dict(out.column("node", "dc_rail_v"))
    assert col == {"gnd": 0.0, "vdd": 1.8}
    assert all(type(v) is float for v in col.values())
    for net in out.keys("node"):
        is_rail = out.value("node", net, "is_rail")
        assert (out.field("node", net, "dc_rail_v") is not None) == is_rail
        if is_rail:
            assert out.field("node", net, "dc_rail_v").writer == "dc_rails"


def test_three_rails(tmp_path):
    doc = topo("hand_three_rail",
               [mos("M1", "nmos", "out", "in", "vss"), mos("M2", "pmos", "out", "pb", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")}, rails=("vdd", "vss", "agnd"),
               passives=[{"name": "CL", "kind": "capacitor", "terminals": ["out", "agnd"]}],
               bias=["pb"])                                                                  # pb: M2 gate 에만
    sup = {"vdd": 1.8, "vss": 0.0, "agnd": 0.9}
    run = _run()
    out = dc_rails(_lifted(tmp_path, doc, sup, run), tuple(sorted(sup.items())), **run)
    assert dict(out.column("node", "dc_rail_v")) == sup


def test_reuse_and_recompute(tmp_path):
    # oracle 대조: card B C4 판정 1(같은 lineage reuse)·4(compute) -- 손 순서(compute, reuse, compute)의 실행 계수(C1) 행
    run = _run()
    base = _lifted(tmp_path, circuit_cs_pmos_load(), SUPPLIES, run)
    a = dc_rails(base, (("gnd", 0.0), ("vdd", 1.8)), **run)
    b = dc_rails(a, (("gnd", 0.0), ("vdd", 1.8)), **run)
    assert b is a
    c = dc_rails(a, (("gnd", 0.0), ("vdd", 1.5)), **run)
    assert c is not a
    assert dict(c.column("node", "dc_rail_v"))["vdd"] == 1.5
    assert c.block_version("dc_rails") != a.block_version("dc_rails")
    assert block_row(run["counters"], "dc_rails") == (3, 1, 0, 0, 2, 0)


def test_context_base_has_rails(ctx_c):
    _, inputs, ctx = ctx_c
    assert dict(ctx.base.column("node", "dc_rail_v")) == dict(inputs.supplies_v)
    assert ctx.base.value("graph", DC_KEY, "dc_current_basis") is not None


def test_mutable_supplies_rejected(tmp_path):
    run = _run()
    base = _lifted(tmp_path, circuit_cs_pmos_load(), SUPPLIES, run)
    with pytest.raises(TypeError):
        dc_rails(base, {"gnd": 0.0, "vdd": 1.8}, **run)
