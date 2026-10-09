"""`block_local_gain` -- 설계 41 §2.1·§2.3(블록 국소 모델: 미지수 = 블록 노드, 입력 단위 구동(차동 ±½), 블록 밖 교류접지, 스탬프 = 봉인 ss,
산출 gain·Z_out·복합 블록 경로별 기여), 체크리스트 D-BM, metrics CONTRACT 10.6('스탬프 소자 = netlist 인접', 폐포, exclude/extra).

oracle (a) 손 폐형식(R' = 1/(1/R + gds)):
* CS: gain = −gm·R', Z_out = R'.
* 대칭 저항 부하 차동쌍(입력 im·ip 이름순 +½/−½, 출력 om − op): 꼬리 노드는 차동 구동에서 대칭으로 0 -> gain = +gm·R', Z_out(+1/−1) = 2R'.
* 되먹임 저항 Rf(입력-출력): KCL 출력 gm·v_in + (gds + 1/RL)·v_o + (v_o − v_in)/Rf = 0 -> gain = (1/Rf − gm)/(gds + 1/Rf + 1/RL), 분해값 표시.
* 복합 블록(입력 둘): 경로 a 기여 = 다른 경로 입력 소자 gm 0(gds 유지) 국소 해 = −gm_a/(1/R + gds_a + gds_b).
* 폐포: 출력에 직렬 Rz 만 닿은 중간 넷(용량으로만 다른 블록에 닿음)은 DC 에서 전류가 없어 gain 불변.
"""
from __future__ import annotations

import pytest

from gmid_engine.metrics import BlockGain, block_local_gain

from . import u7_hand as H
from .conftest import codes

GM, GDS, R = 1e-3, 2e-5, 3e4


def _cs(extra_res=(), extra_nets=()):
    nets = ("gnd", "vdd", "in", "out") + tuple(extra_nets)
    m = (H.mos("M1", "out", "in", "gnd", "gnd", GM, GDS),)
    rr = (H.res("RL", "vdd", "out", R),) + tuple(extra_res)
    return nets, m, rr


def test_cs_gain_zout_members():
    nets, m, rr = _cs()
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out")))
    rp = H.par(1 / R, GDS)
    assert isinstance(got, BlockGain) and got.undefined == ()
    assert got.gain == pytest.approx(-GM * rp, rel=1e-12)
    assert got.gain_db == pytest.approx(H.db(GM * rp), rel=1e-12)
    assert got.zout_ohm == pytest.approx(rp, rel=1e-12)
    assert got.members == ("M1", "RL")
    assert dict(got.node_v) == {"in": 1.0, "out": pytest.approx(-GM * rp, rel=1e-12)}
    assert got.decomposed_only is False
    assert 0.0 <= got.solve_residual <= 1e-14


def test_explicit_drive_scales_and_divides():
    nets, m, rr = _cs()
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out")), {"in": 0.37})
    assert got.gain == pytest.approx(-GM * H.par(1 / R, GDS), rel=1e-12)
    assert dict(got.node_v)["out"] == pytest.approx(-0.37 * GM * H.par(1 / R, GDS), rel=1e-12)


def test_differential_block_unit_drive_and_zout():
    nets, m, rr, ground, inputs = H.diff_pair()
    ss = H.circuit(nets, m, rr, ground, inputs)
    b = H.block(("om", "op"), ("im", "ip"), ("om", "op"), ("im", "ip", "om", "op", "t"), input_cells=("M1", "M2"))
    got = block_local_gain(ss, b)
    rp = H.par(1 / H.DP_R, H.DP_GDS)
    assert dict(got.node_v)["im"] == 0.5 and dict(got.node_v)["ip"] == -0.5
    assert got.gain == pytest.approx(H.DP_GM * rp, rel=1e-12)
    assert got.zout_ohm == pytest.approx(2 * rp, rel=1e-12)
    assert dict(got.node_v)["t"] == pytest.approx(0.0, abs=1e-15)
    assert got.members == ("M1", "M2", "M3", "R1", "R2")


def test_feedback_resistor_marks_decomposed_and_closed_form():
    rf = 1e5
    nets, m, rr = _cs(extra_res=(H.res("Rf", "in", "out", rf),))
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out")))
    assert got.decomposed_only is True
    assert got.gain == pytest.approx((1 / rf - GM) / (GDS + 1 / rf + 1 / R), rel=1e-12)
    assert got.zout_ohm == pytest.approx(H.par(GDS, 1 / rf, 1 / R), rel=1e-12)


def test_closure_pulls_series_rz_mid_net_without_changing_gain():
    nets, m, rr = _cs(extra_res=(H.res("Rz", "out", "mz", 5e3),), extra_nets=("mz", "v1"))
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out")), others=("v1",))
    assert got.gain == pytest.approx(-GM * H.par(1 / R, GDS), rel=1e-12)
    assert "Rz" in got.members and dict(got.node_v)["mz"] == pytest.approx(dict(got.node_v)["out"], rel=1e-12)


def test_exclude_and_extra_ff_devices():
    nets, m, rr, ground, inputs = H.chain3()
    ss = H.circuit(nets, m, rr, ground, inputs)
    b3 = H.block(("out",), ("v2",), ("out",), ("v2", "out"), stage=3)
    others = ("in", "v1")
    c = H.CH
    loaded = block_local_gain(ss, b3, others=others)                                   # 인접 규칙: Mf(d out) 도 붙는다(gate v1 = 0)
    assert loaded.gain == pytest.approx(-c["gm3"] * H.par(1 / c["r3"], c["gds3"], c["gdsf"]), rel=1e-12)
    assert "Mf" in loaded.members
    bare = block_local_gain(ss, b3, others=others, exclude=("Mf",))
    assert bare.gain == pytest.approx(-c["gm3"] * H.par(1 / c["r3"], c["gds3"]), rel=1e-12)
    assert "Mf" not in bare.members
    merged = block_local_gain(ss, b3, {"v2": 0.0, "v1": 1.0}, others=("in",), exclude=("Mf",), extra=("Mf",))
    assert dict(merged.node_v)["out"] == pytest.approx(-c["gmf"] * H.par(1 / c["r3"], c["gds3"], c["gdsf"]), rel=1e-12)


def test_other_block_nodes_held_at_zero():
    """블록 1(v1) 국소 해에서 블록 2 노드 v2 는 교류접지: M2(채널 v2-gnd)는 v1 에 채널 단자가 없어 스탬프되지 않는다."""
    nets, m, rr, ground, inputs = H.chain3(with_ff=False)
    ss = H.circuit(nets, m, rr, ground, inputs)
    got = block_local_gain(ss, H.block(("v1",), ("in",), ("v1",), ("in", "v1")), others=("v2", "out"))
    assert got.members == ("M1", "R1")
    assert got.gain == pytest.approx(-H.CH["gm1"] * H.par(1 / H.CH["r1"], H.CH["gds1"]), rel=1e-12)


def test_composite_block_path_contributions():
    nets = ("gnd", "vdd", "ia", "ib", "out")
    ga, gb, da, dbs, rl = 1e-3, 4e-4, 2e-5, 1e-5, 2e4
    m = (H.mos("Ma", "out", "ia", "gnd", "gnd", ga, da), H.mos("Mb", "out", "ib", "gnd", "gnd", gb, dbs))
    ss = H.circuit(nets, m, (H.res("RL", "vdd", "out", rl),), ("gnd", "vdd"), ("ia", "ib"))
    got = block_local_gain(ss, H.block(("out",), ("ia", "ib"), ("out",), ("ia", "ib", "out"), kind="composite"))
    assert got.gain is None and codes(got.undefined) == {"composite_paths"}
    load = H.par(1 / rl, da, dbs)
    assert dict(got.contributions) == {"ia": pytest.approx(-ga * load, rel=1e-12), "ib": pytest.approx(-gb * load, rel=1e-12)}


def test_undefined_codes():
    nets, m, rr, ground, inputs = H.diff_pair()
    ss = H.circuit(nets, m, rr, ground, inputs)
    nodes = ("im", "ip", "om", "op", "t")
    three_out = block_local_gain(ss, H.block(("om", "op", "t"), ("im", "ip"), ("om", "op", "t"), nodes))
    assert codes(three_out.undefined) == {"unsupported_outputs"} and three_out.gain is None
    three_in = block_local_gain(ss, H.block(("om",), ("im", "ip", "vb"), ("om",), nodes + ("vb",)))
    assert codes(three_in.undefined) == {"unsupported_inputs"}
    same = block_local_gain(ss, H.block(("om", "op"), ("im", "ip"), ("om", "op"), nodes), {"im": 0.3, "ip": 0.3})
    assert codes(same.undefined) == {"input_zero"} and same.zout_ohm is not None
    nets2 = ("gnd", "in", "y", "z")
    float_ss = H.circuit(nets2, (H.mos("M1", "y", "in", "gnd", "gnd", 1e-3, 0.0),), (H.res("Rq", "y", "z", 1e3),), ("gnd",), ("in",))
    sing = block_local_gain(float_ss, H.block(("y",), ("in",), ("y",), ("in", "y")))
    assert codes(sing.undefined) == {"singular_dc"} and sing.gain is None


def test_name_bijection_invariance():
    nets, m, rr, ground, inputs = H.diff_pair()
    a = block_local_gain(H.circuit(nets, m, rr, ground, inputs),
                         H.block(("om", "op"), ("im", "ip"), ("om", "op"), ("im", "ip", "om", "op", "t")))
    nmap = {"im": "u2", "ip": "u1", "om": "w2", "op": "w1", "t": "k", "vb": "e", "vdd": "p", "gnd": "q"}
    nets2, m2, r2 = H.rename(nets, m, rr, nmap, {"M1": "Q7", "M2": "Q3", "M3": "A", "R1": "Z1", "R2": "Z0"}, order_seed=11)
    b = block_local_gain(H.circuit(nets2, m2, r2, [nmap[g] for g in ground], [nmap[i] for i in inputs]),
                         H.block(("w1", "w2"), ("u1", "u2"), ("w1", "w2"), ("u1", "u2", "w1", "w2", "k")))
    # 이름순이 뒤집혀(u1 < u2, w1 < w2) 입력·출력 차의 방향이 함께 뒤집힌다 -- gain(차 / 차)은 같다.
    assert b.gain == pytest.approx(a.gain, rel=1e-12) and b.zout_ohm == pytest.approx(a.zout_ohm, rel=1e-12)
