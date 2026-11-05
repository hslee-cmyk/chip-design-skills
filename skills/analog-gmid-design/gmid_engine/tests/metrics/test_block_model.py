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

import dataclasses

import pytest

from gmid_engine.metrics import (BlockGain, Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit,
                                 block_local_gain)

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
    """[UB-1 T-3 뜻 교체] 막다른 가지(출력 아님, 저항 단자 하나뿐, 스탬프 MOS 단자 아님)는 넷과 저항을 함께 뺀다:
    있는·없는 회로의 gain·zout 이 같고(-gm·R', R'), Rz 는 members 에, mz 는 node_v 에 없다. (옛 뜻: mz 를 끌어들여 members 에 넣음.)
    oracle (a) 닫힌 식."""
    nets, m, rr = _cs(extra_res=(H.res("Rz", "out", "mz", 5e3),), extra_nets=("mz", "v1"))
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    blk = H.block(("out",), ("in",), ("out",), ("in", "out"), members=("M1", "RL"))
    got = block_local_gain(ss, blk, others=("v1",))
    nets0, m0, rr0 = _cs()
    bare = block_local_gain(H.circuit(nets0, m0, rr0, ("gnd", "vdd"), ("in",)), blk)
    rp = H.par(1 / R, GDS)
    assert got.gain == pytest.approx(-GM * rp, rel=1e-12) and bare.gain == pytest.approx(-GM * rp, rel=1e-12)
    assert got.gain == pytest.approx(bare.gain, rel=1e-12)
    assert got.zout_ohm == pytest.approx(rp, rel=1e-12) and got.zout_ohm == pytest.approx(bare.zout_ohm, rel=1e-12)
    assert "Rz" not in got.members and "mz" not in dict(got.node_v)


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


# =====================================================================================================================
# [UB-1 + NL-1, card 20261104-ub1-nl1] 봉인 모드 U_b 규칙 -- interface card 'toy' T-1 ~ T-11. 기대값은 전부 oracle (a): 손 닫힌 식
# (KCL 을 손으로 세워 푼 식 -- 피검 함수 호출·식 복사 없음). 허용오차 = 부동소수 풀이 잔차(rel 1e-12 관행; 용량 혼합 T-4 는 1e-10).
# =====================================================================================================================

def test_ub1_cs_to_cg_adjacent_blocks():
    """T-1 (a): CS(M1, R1) -> CG(M2, R2). 아래 단의 입력 컨덕턴스 g_in = gm2 + gmb2 + gds2.
    A: gain = −gm1/(gds1 + G1 + g_in), zout = 1/(gds1 + G1 + g_in), members = (M1, M2, R1), node_v 키 = {in, x}(out 안 풂).
    B: gain = g_in/(gds2 + G2), zout = 1/(gds2 + G2)."""
    gm1, gds1, r1 = 1.1e-3, 2.0e-5, 4e4
    gm2, gds2, gmb2, r2 = 0.9e-3, 1.5e-5, 2.2e-4, 3e4
    nets = ("gnd", "vdd", "vb", "in", "x", "out")
    m = (H.mos("M1", "x", "in", "gnd", "gnd", gm1, gds1), H.mos("M2", "out", "vb", "x", "gnd", gm2, gds2, gmb2))
    rr = (H.res("R1", "vdd", "x", r1), H.res("R2", "vdd", "out", r2))
    ss = H.circuit(nets, m, rr, ("gnd", "vdd", "vb"), ("in",))
    g_in = gm2 + gmb2 + gds2
    a = block_local_gain(ss, H.block(("x",), ("in",), ("x",), ("in", "x"), members=("M1", "R1")), others=("out",))
    den = gds1 + 1 / r1 + g_in
    assert a.undefined == ()
    assert a.gain == pytest.approx(-gm1 / den, rel=1e-12)
    assert a.zout_ohm == pytest.approx(1 / den, rel=1e-12)
    assert a.members == ("M1", "M2", "R1")
    assert set(dict(a.node_v)) == {"in", "x"}
    b = block_local_gain(ss, H.block(("out",), ("x",), ("out",), ("x", "out"), members=("M2", "R2")))
    assert b.undefined == ()
    assert b.gain == pytest.approx(g_in / (gds2 + 1 / r2), rel=1e-12)
    assert b.zout_ohm == pytest.approx(1 / (gds2 + 1 / r2), rel=1e-12)


def test_ub1_dead_end_branch_output_exception_and_gate_reader():
    """T-3a (a): 막다른 가지 끝 mz 가 출력이면 뺄 수 없다 -- V(mz) = V(out)(Rz 에 전류 없음), gain = −gm·R', Rz ∈ members.
    T-3b (a): mz 가 MOS gate 로 읽히면 막다른 넷이 아니다 -- 다음 단 M2(d o2, g mz, s gnd), R2(vdd–o2), 출력 o2:
    gain = (−gm1·R1')(−gm2·R2'), mz ∈ node_v, Rz ∈ members."""
    gm2, gds2, r2, rz = 0.8e-3, 1.5e-5, 2.5e4, 5e3
    nets, m, rr = _cs(extra_res=(H.res("Rz", "out", "mz", rz),), extra_nets=("mz",))
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    rp = H.par(1 / R, GDS)
    a = block_local_gain(ss, H.block(("out",), ("in",), ("mz",), ("in", "out", "mz"), members=("M1", "RL", "Rz")))
    assert a.gain == pytest.approx(-GM * rp, rel=1e-12)
    assert "Rz" in a.members
    nv = dict(a.node_v)
    assert nv["mz"] == pytest.approx(nv["out"], rel=1e-12)
    nets2 = nets + ("o2",)
    m2 = m + (H.mos("M2", "o2", "mz", "gnd", "gnd", gm2, gds2),)
    rr2 = rr + (H.res("R2", "vdd", "o2", r2),)
    ss2 = H.circuit(nets2, m2, rr2, ("gnd", "vdd"), ("in",))
    b = block_local_gain(ss2, H.block(("o2",), ("in",), ("o2",), ("in", "out", "mz", "o2"),
                                      members=("M1", "M2", "R2", "RL", "Rz")))
    assert b.gain == pytest.approx(GM * rp * gm2 * H.par(1 / r2, gds2), rel=1e-12)
    assert "mz" in dict(b.node_v) and "Rz" in b.members


def _ub1_t4(c1=2e-12, c2=3e-12, cgs=5e-13, cgd=2e-13, cgb=1e-13, gm=1e-3, gds=2e-5, rl=3e4, caps=True, missing=()):
    """T-4 회로: C1(in–n), C2(n–gnd), M1(d out, g n, s gnd, cgs·cgd·cgb), RL(vdd–out) -- `SmallSignalCircuit` 을 직접 만든 `SsCircuit`.
    caps=False: 용량 전부 없음(0). missing: 값 없는 수동소자 이름(그 용량은 회로에 없다)."""
    nets = ("gnd", "vdd", "in", "n", "out")
    i = {n: k for k, n in enumerate(nets)}
    if not caps:
        cgs = cgd = cgb = 0.0
    mos = (MosSmallSignal(i["out"], i["n"], i["gnd"], i["gnd"], gm, 0.0, gds, cgs=cgs, cgd=cgd, cgb=cgb, label="M1"),)
    cap_rows = []
    if caps:
        cap_rows = [Capacitor(i["in"], i["n"], c1, label="C1"), Capacitor(i["n"], i["gnd"], c2, label="C2")]
        cap_rows = [c for c in cap_rows if c.label not in missing]
    res = (Resistor(i["vdd"], i["out"], rl, label="RL"),)
    return SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=tuple(cap_rows)), ("RL",),
                     tuple(c.label for c in cap_rows), ("gnd", "vdd"), ("in",), tuple(missing))


_UB1_T4_BLOCK = dict(key=("out",), inputs=("in",), outputs=("out",), nodes=("in", "out"))


def test_ub1_capacitive_divider_gate_net_is_charge_conserved():
    """T-4 (a): n 은 용량으로만 구동되는 게이트 넷 -- DC 에서 0 V 가 아니라 전하 보존 행으로 푼다.
    KCL(n): C1(v_n − v_in) + C2·v_n + cgs·v_n + cgb·v_n + cgd(v_n − v_out) = 0, KCL(out): gm·v_n + (gds + G)·v_out = 0
    -> D = C1 + C2 + cgs + cgb + cgd(1 + gm·R'), V(n) = C1/D, gain = −gm·R'·C1/D (R' = 1/(gds + G))."""
    c1, c2, cgs, cgd, cgb, gm, gds, rl = 2e-12, 3e-12, 5e-13, 2e-13, 1e-13, 1e-3, 2e-5, 3e4
    got = block_local_gain(_ub1_t4(), H.block(**_UB1_T4_BLOCK, members=("C1", "C2", "M1", "RL")))
    rp = 1.0 / (gds + 1.0 / rl)
    d = c1 + c2 + cgs + cgb + cgd * (1.0 + gm * rp)
    assert got.undefined == ()
    assert got.gain == pytest.approx(-gm * rp * c1 / d, rel=1e-10)
    assert dict(got.node_v)["n"] == pytest.approx(c1 / d, rel=1e-10)
    assert dict(got.node_v)["out"] == pytest.approx(-gm * rp * c1 / d, rel=1e-10)


def test_ub1_charge_net_without_capacitors_or_with_missing_one_is_singular():
    """T-4b (a): 용량 전부 0 이면 n 의 전하 행이 0 -> 풀 수 없다(0 V 로 두지 않음): undefined {singular_dc}, gain None.
    T-4f (a): 용량 하나가 값 없음(ss.missing)이면 남은 용량만으로 풀지 않는다(C 일부) -> 같은 코드. 전하 넷 없는 CS 는 결측이 있어도 값 그대로."""
    blk = H.block(**_UB1_T4_BLOCK, members=("C1", "C2", "M1", "RL"))
    none = block_local_gain(_ub1_t4(caps=False), blk)
    assert codes(none.undefined) == {"singular_dc"} and none.gain is None
    part = block_local_gain(_ub1_t4(missing=("C1",)), blk)
    assert codes(part.undefined) == {"singular_dc"} and part.gain is None
    nets, m, rr = _cs()
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    ss = dataclasses.replace(ss, missing=("Cx",))
    cs = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out"), members=("M1", "RL")))
    assert cs.gain == pytest.approx(-GM * H.par(1 / R, GDS), rel=1e-12)


def test_ub1_non_member_load_is_stamped_in_sealed_mode():
    """T-9 (a): 팔로워 M1(d vdd, g in, s out), 비멤버 부하 M2(d out, g vb, s gnd). 봉인은 M2 를 스탬프한다(members 에 듦):
    KCL(out): gm1(v_in − v_o) − gmb1·v_o − gds1·v_o = gds2·v_o -> gain = gm1/(gm1 + gmb1 + gds1 + gds2), zout = 1/(같은 합)."""
    gm1, gds1, gmb1, gm2, gds2 = 1e-3, 1.5e-5, 2e-4, 7e-4, 2.5e-5
    nets = ("gnd", "vdd", "vb", "in", "out")
    m = (H.mos("M1", "vdd", "in", "out", "gnd", gm1, gds1, gmb1), H.mos("M2", "out", "vb", "gnd", "gnd", gm2, gds2))
    ss = H.circuit(nets, m, (), ("gnd", "vdd", "vb"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out"), members=("M1",)))
    den = gm1 + gmb1 + gds1 + gds2
    assert got.gain == pytest.approx(gm1 / den, rel=1e-12)
    assert got.zout_ohm == pytest.approx(1 / den, rel=1e-12)
    assert got.members == ("M1", "M2")


def test_ub1_non_member_mos_does_not_widen_unknown_set():
    """T-9a (a): 비멤버 M3(d y, g vb, s out)·M4(d gnd, g vb, s y). M3 은 U_b 에 닿으므로 스탬프하지만 U_b 를 넓히지 않는다
    (y 는 0 V 로 둔다 -> y ∉ node_v, M4 ∉ members): gain = −gm1/(gds1 + G + gm3 + gmb3 + gds3)."""
    gm3, gds3, gmb3, gm4, gds4 = 6e-4, 1.2e-5, 1.5e-4, 9e-4, 3e-5
    nets = ("gnd", "vdd", "vb", "in", "out", "y")
    m = (H.mos("M1", "out", "in", "gnd", "gnd", GM, GDS), H.mos("M3", "y", "vb", "out", "gnd", gm3, gds3, gmb3),
         H.mos("M4", "gnd", "vb", "y", "gnd", gm4, gds4))
    ss = H.circuit(nets, m, (H.res("RL", "vdd", "out", R),), ("gnd", "vdd", "vb"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out"), members=("M1", "RL")))
    assert got.gain == pytest.approx(-GM / (GDS + 1 / R + gm3 + gmb3 + gds3), rel=1e-12)
    assert set(dict(got.node_v)) == {"in", "out"}
    assert "M3" in got.members and "M4" not in got.members


def test_ub1_hand_calculation_cascode_and_ota5():
    """T-7 (ii) (a): 캐스코드 M1(d x, g in, s gnd), M2(d out, g vb, s x), RL(vdd–out), members 셋. g2 = gm2 + gmb2 + gds2:
    KCL(x): gm1·v_in + (gds1 + g2)·v_x − gds2·v_o = 0, KCL(out): −g2·v_x + (G + gds2)·v_o = 0
    -> gain = −gm1/[(gds1 + g2)(G + gds2)/g2 − gds2], zout = 1/[G + gds2 − g2·gds2/(gds1 + g2)].
    T-7 (iii) (b): 차동쌍 + 미러 H.ota5 -- 입력 ±½, 기대 = H.ref_solve 독립 풀이의 |V(out)| (입력 차 1)."""
    gm1, gds1, gm2, gds2, gmb2 = 1.0e-3, 2.0e-5, 0.8e-3, 1.5e-5, 2.0e-4
    nets = ("gnd", "vdd", "vb", "in", "x", "out")
    m = (H.mos("M1", "x", "in", "gnd", "gnd", gm1, gds1), H.mos("M2", "out", "vb", "x", "gnd", gm2, gds2, gmb2))
    ss = H.circuit(nets, m, (H.res("RL", "vdd", "out", R),), ("gnd", "vdd", "vb"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out"), members=("M1", "M2", "RL")))
    g2, g = gm2 + gmb2 + gds2, 1 / R
    assert got.gain == pytest.approx(-gm1 / ((gds1 + g2) * (g + gds2) / g2 - gds2), rel=1e-12)
    assert got.zout_ohm == pytest.approx(1 / (g + gds2 - g2 * gds2 / (gds1 + g2)), rel=1e-12)
    onets, om, orr, ground, inputs = H.ota5()
    oss = H.circuit(onets, om, orr, ground, inputs)
    members = tuple(r["label"] for r in om)
    ota = block_local_gain(oss, H.block(("out",), ("im", "ip"), ("out",), ("im", "ip", "t", "x", "out"), members=members))
    ref = H.ref_solve(om, orr, {"gnd": 0.0, "vdd": 0.0, "vb": 0.0, "im": 0.5, "ip": -0.5})
    assert abs(ota.gain) == pytest.approx(abs(ref["out"]), rel=1e-9)


def test_ub1_view_ground_net_argument():
    """T-10 (a): CS + Rb(out–vb2). vb2 는 ss.ground_nets 밖이지만 뷰 교류접지(ground=("vb2",))면 F: Rb 는 출력의 1/Rb 부하
    -> gain = −gm/(gds + G + 1/Rb), 분해 표시 없음(Rb 는 입력·남의 블록 넷을 잇지 않음)."""
    rb = 8e3
    nets, m, rr = _cs(extra_res=(H.res("Rb", "out", "vb2", rb),), extra_nets=("vb2",))
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out"), members=("M1", "RL")), ground=("vb2",))
    assert got.gain == pytest.approx(-GM / (GDS + 1 / R + 1 / rb), rel=1e-12)
    assert got.decomposed_only is False
    assert "Rb" in got.members


def test_ub1_closure_stops_at_other_block_net():
    """T-11 (a): CS + Rx(out–v2), v2 = 남의 블록 넷(others) -> 폐포는 거기서 멈춘다: Rx 는 스탬프(members), v2 는 0 V 로 F 이므로
    gain = −gm/(gds + G + 1/Rx), v2 ∉ node_v, decomposed_only True."""
    rx = 6e3
    nets, m, rr = _cs(extra_res=(H.res("Rx", "out", "v2", rx),), extra_nets=("v2",))
    ss = H.circuit(nets, m, rr, ("gnd", "vdd"), ("in",))
    got = block_local_gain(ss, H.block(("out",), ("in",), ("out",), ("in", "out"), members=("M1", "RL")), others=("v2",))
    assert got.gain == pytest.approx(-GM / (GDS + 1 / R + 1 / rx), rel=1e-12)
    assert "Rx" in got.members and "v2" not in dict(got.node_v)
    assert got.decomposed_only is True


def test_ub1_dead_end_resistor_net_read_by_capacitor_to_charge_net():
    """[A-107 M-1] oracle (a) 구성 정답 + 손 KCL. out -Rz- mz -Cc- n -C2- gnd, M2(d o2, g n), M1 이 out 을 구동.
    Rz 에 흐르는 DC 전류 0(mz 는 용량으로만 이어짐) -> V(mz) = V(out). 전하 넷 n 은 용량 분배(ω→0 전하 보존):
    V(out) = −gm1/(gds1 + 1/R1) = −1e-3/(2e-5 + 1/3e4) = −18.75,
    V(n) = Cc/(Cc + C2)·V(mz) = 1/(1+3)·(−18.75) = −4.6875,
    gain = V(o2) = −gm2/(gds2 + 1/R2)·V(n) = −2e-3/(3e-5 + 1/2e4)·(−4.6875) = 117.1875.
    막다른 가지 규칙이 용량 독자를 놓치면 mz 를 뺀 뒤 gain −0.0."""
    nets = ("gnd", "vdd", "in", "out", "mz", "n", "o2")
    i = {n: k for k, n in enumerate(nets)}
    gm1, gds1, r1, gm2, gds2, r2, ccz, c2z, rz = 1e-3, 2e-5, 3e4, 2e-3, 3e-5, 2e4, 1e-12, 3e-12, 1e3
    mos = (MosSmallSignal(i["out"], i["in"], i["gnd"], i["gnd"], gm1, 0.0, gds1, label="M1"),
           MosSmallSignal(i["o2"], i["n"], i["gnd"], i["gnd"], gm2, 0.0, gds2, label="M2"))
    res = (Resistor(i["vdd"], i["out"], r1, label="R1"), Resistor(i["vdd"], i["o2"], r2, label="R2"),
           Resistor(i["out"], i["mz"], rz, label="Rz"))
    caps = (Capacitor(i["mz"], i["n"], ccz, label="Cc"), Capacitor(i["n"], i["gnd"], c2z, label="C2"))
    ss = SsCircuit(nets, SmallSignalCircuit(mos=mos, resistors=res, capacitors=caps), tuple(r.label for r in res),
                   tuple(c.label for c in caps), ("gnd", "vdd"), ("in",))
    b = H.block(("o2",), ("in",), ("o2",), ("in", "out", "mz", "n", "o2"),
                members=("M1", "M2", "R1", "R2", "Rz", "Cc", "C2"))
    got = block_local_gain(ss, b)
    assert got.undefined == ()
    assert dict(got.node_v)["mz"] == pytest.approx(-18.75, rel=1e-9)
    assert dict(got.node_v)["n"] == pytest.approx(-4.6875, rel=1e-9)
    assert got.gain == pytest.approx(117.1875, rel=1e-9)
