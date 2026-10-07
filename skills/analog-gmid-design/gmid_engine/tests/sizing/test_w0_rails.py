"""`dc_rails(snapshot, supplies)` -- CONTRACT 4.1: reads node.is_rail, writes node.dc_rail_v = 레일마다 float(supplies 값).
레일 아닌 노드에는 dc_rail_v 가 없다(봉인 5: 한 노드에 dc_rail_v·dc_v 중 하나).
"""
import pytest

from gmid_engine.graph import build_s1
from gmid_engine.sizing import DC_KEY, dc_rails, lift_s1

from .conftest import SUPPLIES, circuit_cs_pmos_load, load_doc, mos, topo


def _lifted(tmp_path, doc, supplies):
    return lift_s1(build_s1(load_doc(tmp_path, doc), dict(supplies)))


def test_rails_get_float_values_only(tmp_path):
    base = _lifted(tmp_path, circuit_cs_pmos_load(), SUPPLIES)
    out = dc_rails(base, (("gnd", 0), ("vdd", 1.8)))
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
               passives=[{"name": "CL", "kind": "capacitor", "terminals": ["out", "agnd"]}])
    sup = {"vdd": 1.8, "vss": 0.0, "agnd": 0.9}
    out = dc_rails(_lifted(tmp_path, doc, sup), tuple(sorted(sup.items())))
    assert dict(out.column("node", "dc_rail_v")) == sup


def test_reuse_and_recompute(tmp_path):
    base = _lifted(tmp_path, circuit_cs_pmos_load(), SUPPLIES)
    dc_rails.reset_stats()
    a = dc_rails(base, (("gnd", 0.0), ("vdd", 1.8)))
    b = dc_rails(a, (("gnd", 0.0), ("vdd", 1.8)))
    assert b is a
    c = dc_rails(a, (("gnd", 0.0), ("vdd", 1.5)))
    assert c is not a
    assert dict(c.column("node", "dc_rail_v"))["vdd"] == 1.5
    assert c.block_version("dc_rails") != a.block_version("dc_rails")
    st = dc_rails.stats()
    assert (st.calls, st.reuses, st.computes, st.recomputes_same_input) == (3, 1, 2, 0)


def test_context_base_has_rails(ctx_c):
    _, inputs, ctx = ctx_c
    assert dict(ctx.base.column("node", "dc_rail_v")) == dict(inputs.supplies_v)
    assert ctx.base.value("graph", DC_KEY, "dc_current_basis") is not None


def test_mutable_supplies_rejected(tmp_path):
    base = _lifted(tmp_path, circuit_cs_pmos_load(), SUPPLIES)
    with pytest.raises(TypeError):
        dc_rails(base, {"gnd": 0.0, "vdd": 1.8})
