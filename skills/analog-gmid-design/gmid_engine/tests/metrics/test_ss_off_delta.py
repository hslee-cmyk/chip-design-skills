"""`ss_off_delta`(graph.ss_off_delta = OffDelta(node_dv, sources)) · `ss_off_op`(device.off_op) 값 -- interface card
20261104-eo1r4-sf1l §4 '식' (T-O1·T-O2).

oracle (손): card §4 의 식 -- vgs = p(Vg - Vs), vds = p(Vd - Vs), vsb = p(Vs - Vb); ΔI_off = IDu(vgs, vds, vsb)·w_m/l_m;
주입(노드로 들어가는 전류) nmos = drain -ΔI, source +ΔI / pmos = drain +ΔI, source -ΔI; G·ΔV = 주입, G = 소신호 노드 컨덕턴스(off 소자 스탬프 포함).
합성 LUT(sizing conftest r4 해석식): VGS = 0·VSB = 0 에서 IDu = I0·exp(LAM·VDS) (닫힌 식), off 소자 gds = LAM·ΔI (GDS 열 = LAM·ID, ln 선형이라 정확).
다른 MOS 의 gds 는 r4 npz 의 GDS 열을 독립 numpy 보간(metrics conftest `multilinear`)으로 계산. 연립은 numpy.linalg.solve (피검 함수 아님).
회로: A = 노드 out 하나(M1 nmos + R1 vdd->out + off 소자), TWO = 노드 out·mid 둘(왼쪽 가지 A, 오른쪽 가지 pmos M2 + R2 mid->gnd, off 소자는 out-mid 사이).
off 소자 단자: gate·bulk 를 source 노드에 묶어 vgs = 0, vsb = 0 (게이트·벌크가 source 와 함께 움직여 gm·gmb 항이 0, 닫힌 식만 남는다).
단언 금지: 블록 내부 호출 인자.
"""
import numpy as np
import pytest

from .conftest import rel_close
from .off_cases import (build_case, circuit_a, circuit_two, evaluate, gds_lut, gds_off, graph_field, i_off_at_vgs0_vsb0,
                        off_entry, theta_from_schema)

I1, R1 = 1e-5, 9e4          # V(out) = 1.8 - 0.9 = 0.9
I2, R2 = 1e-5, 3e4          # V(mid) = 0.3


def theta_a(ctx):
    return theta_from_schema(ctx, {"M1": ("nmos", 0.6, 1.8 - I1 * R1, 0.0)}, {"R1": I1, "M1": I1}, {"R1": R1})


def theta_two(ctx):
    return theta_from_schema(ctx, {"M1": ("nmos", 0.6, 1.8 - I1 * R1, 0.0), "M2": ("pmos", 0.7, 1.8 - I2 * R2, 0.0)},
                             {"R1": I1, "M1": I1, "R2": I2, "M2": I2}, {"R1": R1, "R2": R2})


TWO_ELEMENTS = (("R1", "resistor", None), ("R2", "resistor", None), ("CL", "capacitor", 1e-12))


def case_a(tmp, w_m=1e-6, l_m=1e-6, with_off=True, name="od_a"):
    off = [("Moff", "nmos", "out", "gnd", "gnd", "gnd")] if with_off else []
    return build_case(tmp, circuit_a(off, name=name), {"Moff": off_entry(w_m, l_m)} if with_off else {}, theta_a)


# ---- T-O1 -------------------------------------------------------------------------------------------------------------

def test_off_delta_single_node_equals_hand_solution(tmp_path):
    case = case_a(tmp_path / "w")
    snap = evaluate(case).snapshot
    vout = snap.value("node", "out", "dc_v")
    assert rel_close(vout, 1.8 - I1 * R1, 1e-9)                              # (d) V(out) = vdd - I·R
    ref = case_a(tmp_path / "n", with_off=False, name="od_a_noff")           # off 소자를 지운 회로의 봉인점
    assert rel_close(vout, ref.ev.snapshot.value("node", "out", "dc_v"), 1e-12)
    assert "Moff" not in dict(case.ev.snapshot.column("device", "dc_op"))

    dI = i_off_at_vgs0_vsb0("nmos", vout, 1e-6, 1e-6)
    op = snap.value("device", "M1", "dc_op")
    g_xx = 1.0 / R1 + gds_lut("nmos", op.L, op.vgs, op.vds, op.vsb, op.W) + gds_off(dI)
    od = graph_field(snap, "ss_off_delta")
    dv = dict(od.node_dv)["out"]
    assert dv < 0.0                                                          # nmos: drain 로 -ΔI 주입 -> ΔV < 0
    assert rel_close(dv, -dI / g_xx, 1e-9)
    assert rel_close(dict(od.sources)["Moff"], dI, 1e-9)


def test_off_delta_off_op_point_and_key(tmp_path):
    case = case_a(tmp_path)
    snap = evaluate(case).snapshot
    vout = snap.value("node", "out", "dc_v")
    o = snap.value("device", "Moff", "off_op")
    assert (o.vgs, o.vsb, o.w_key) == (0.0, 0.0, 100)                        # w_m 1e-6 / 격자 1e-8 = 100 (손계산)
    assert rel_close(o.vds, vout, 1e-12)
    assert snap.field("device", "M1", "off_op") is None                      # 선언 소자에만


@pytest.mark.parametrize("k", [2.0, 0.5])
def test_off_delta_scales_with_w_over_l(tmp_path, k):
    base = graph_field(evaluate(case_a(tmp_path / "b")).snapshot, "ss_off_delta")
    scaled = graph_field(evaluate(case_a(tmp_path / "s", w_m=k * 1e-6, name="od_a_k")).snapshot, "ss_off_delta")
    assert rel_close(dict(scaled.sources)["Moff"], k * dict(base.sources)["Moff"], 1e-12)


# ---- T-O2 두 노드 -------------------------------------------------------------------------------------------------------

def _two_node_expected(snap, dI, kind_of_off):
    """G = [[1/R1 + gds1 + gdso, -gdso], [-gdso, 1/R2 + gds2 + gdso]] (out, mid), 주입 = (-ΔI, +ΔI) (두 극성 모두 out = 낮은 쪽이 아니라
    nmos: drain out / pmos: source out -> out 에 -ΔI, mid 에 +ΔI)."""
    o1 = snap.value("device", "M1", "dc_op")
    o2 = snap.value("device", "M2", "dc_op")
    go = gds_off(dI)
    g1 = gds_lut("nmos", o1.L, o1.vgs, o1.vds, o1.vsb, o1.W)
    g2 = gds_lut("pmos", o2.L, o2.vgs, o2.vds, o2.vsb, o2.W)
    G = np.array([[1.0 / R1 + g1 + go, -go], [-go, 1.0 / R2 + g2 + go]])
    return np.linalg.solve(G, np.array([-dI, dI]))


@pytest.mark.parametrize("kind,pins", [
    ("nmos", ("Moff", "nmos", "out", "mid", "mid", "mid")),      # drain out(0.9), source/gate/bulk mid(0.3): vds = 0.6
    ("pmos", ("Moff", "pmos", "mid", "out", "out", "out")),      # drain mid(0.3), source/gate/bulk out(0.9): vds = -(0.3 - 0.9) = 0.6
], ids=["nmos", "pmos"])
def test_off_delta_two_nodes_matches_2x2_inverse(tmp_path, kind, pins):
    case = build_case(tmp_path, circuit_two([pins], name="od_two_" + kind), {"Moff": off_entry()}, theta_two,
                      elements=TWO_ELEMENTS)
    snap = evaluate(case).snapshot
    vx, vy = snap.value("node", "out", "dc_v"), snap.value("node", "mid", "dc_v")
    assert rel_close(vx, 1.8 - I1 * R1, 1e-9) and rel_close(vy, I2 * R2, 1e-9)
    dI = i_off_at_vgs0_vsb0(kind, vx - vy, 1e-6, 1e-6)
    want = _two_node_expected(snap, dI, kind)
    got = dict(graph_field(snap, "ss_off_delta").node_dv)
    assert rel_close(got["out"], want[0], 1e-9) and rel_close(got["mid"], want[1], 1e-9)
    drain_net = "out" if kind == "nmos" else "mid"
    src_net = "mid" if kind == "nmos" else "out"
    assert (got[drain_net] < 0.0) == (kind == "nmos")                        # drain 노드 ΔV: nmos < 0, pmos > 0
    assert (got[src_net] > 0.0) == (kind == "nmos")
