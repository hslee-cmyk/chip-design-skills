"""`block_residual` -- 설계 41 §2.2(잔차 = gain_ss_db − 20·log10|A_decomp|, `ss.block_gain`, `ss.rout_residual_ohm`, 되먹임 수동소자가
블록을 가로지르면 '분해값'), §1.12.2-4(FF: A_decomp = Π_main A_i + Σ_ff A_in→tap·G_ff·Z_merge, `ss.ff_contrib{gain_db, sign}`),
체크리스트 D-BM·D-J2, 설계 40 §11 U7 '단일 블록 잔차 0', 41 §9 '단일 블록 잔차 ≤ 수치 분해능', 'A_decomp 잔차 ≤ 수치 분해능'.

oracle (a) 손 폐형식 -- 3단 CS 사슬(u7_hand.chain3, R_k' = 1/(1/r_k + gds_k), R3'' = 1/(1/r3 + gds3 + gdsf)):
  v1 = −gm1·R1'·v_in, v2 = −gm2·R2'·v1, 전회로 out = −R3''·(gm3·v2 + gmf·v1).
  FF 경로 기여(41 §1.12.2-4 식): A_in→tap·G_ff·Z_merge, Z_merge = merge 노드 임피던스(그 노드의 모든 부하) = R3''.
(b) 독립 numpy 풀이(`u7_hand.ref_solve`)로 전회로 이득과 rout.
"""
from __future__ import annotations

import pytest

from gmid_engine.authoring import ViewDecl
from gmid_engine.metrics import BlockResidual, block_residual

from . import u7_hand as H
from . import u7_ngcc as N
from .conftest import codes

C = H.CH


def _rp(k, *extra):
    return H.par(1 / C["r%d" % k], C["gds%d" % k], *extra)


def _chain(with_ff=True, p=None):
    nets, m, r, ground, inputs = H.chain3(p, with_ff)
    return H.circuit(nets, m, r, ground, inputs), m, r


def test_no_ff_chain_block_gains_multiply_to_full():
    """주경로만: 블록 gain_k = −gm_k·R_k', Σ dB = 전회로 dB, 잔차 0, rout 잔차 0(마지막 블록 Z_out = R3' = 전회로 rout)."""
    ss, m, r = _chain(False)
    got = block_residual(ss, H.transfer({"in": 1.0}, "out"), H.chain3_struct(False))
    assert isinstance(got, BlockResidual) and got.undefined == ()
    want = [-C["gm%d" % k] * _rp(k) for k in (1, 2, 3)]
    assert [b.gain for b in got.blocks] == [pytest.approx(w, rel=1e-12) for w in want]
    full = H.sense_of(H.ref_solve(m, r, {"gnd": 0.0, "vdd": 0.0, "in": 1.0}), "out")
    assert full == pytest.approx(want[0] * want[1] * want[2], rel=1e-12)
    assert got.full_gain_db == pytest.approx(H.db(full), rel=1e-12)
    assert sum(b.gain_db for b in got.blocks) == pytest.approx(got.full_gain_db, rel=1e-12)
    assert got.gain_residual_db == pytest.approx(0.0, abs=1e-9)
    assert got.rout_residual_ohm == pytest.approx(0.0, abs=1e-9 * _rp(3))
    assert got.ff_contrib == ()
    assert got.read_devices == ("M1", "M2", "M3", "R1", "R2", "R3")


def test_single_block_residual_zero():
    nets = ("gnd", "vdd", "in", "out")
    ss = H.circuit(nets, (H.mos("M1", "out", "in", "gnd", "gnd", 1e-3, 2e-5),), (H.res("RL", "vdd", "out", 3e4),), ("gnd", "vdd"), ("in",))
    vs = H.vstruct("v", {"in": 1.0}, ("out",), (H.block(("out",), ("in",), ("out",), ("in", "out")),))
    got = block_residual(ss, H.transfer({"in": 1.0}, "out"), vs)
    assert got.gain_residual_db == pytest.approx(0.0, abs=1e-12)
    assert got.decomposed_gain_db == pytest.approx(got.full_gain_db, rel=1e-14)


def test_ff_chain_decomposed_equals_full():
    """FF 묶음(Mf, 탭 v1, merge out): 분해 합성 = 전회로 -> 잔차 ≤ 수치 분해능. 주경로 앞 두 블록 gain 은 FF 와 무관."""
    ss, m, r = _chain(True)
    got = block_residual(ss, H.transfer({"in": 1.0}, "out"), H.chain3_struct(True))
    v1 = -C["gm1"] * _rp(1)
    v2 = -C["gm2"] * _rp(2) * v1
    full = -_rp(3, C["gdsf"]) * (C["gm3"] * v2 + C["gmf"] * v1)
    assert full == pytest.approx(H.sense_of(H.ref_solve(m, r, {"gnd": 0.0, "vdd": 0.0, "in": 1.0}), "out"), rel=1e-12)
    assert got.full_gain_db == pytest.approx(H.db(full), rel=1e-12)
    assert got.gain_residual_db == pytest.approx(0.0, abs=1e-9)
    assert [b.gain for b in got.blocks[:2]] == [pytest.approx(-C["gm1"] * _rp(1), rel=1e-12), pytest.approx(-C["gm2"] * _rp(2), rel=1e-12)]
    assert "Mf" in got.read_devices
    assert [c.id for c in got.ff_contrib] == ["v1->out"]


def test_ff_contribution_is_path_term_a_tap_gff_zmerge():
    """[RED 예상 -- 이의] 41 §1.12.2-4: FF 기여 = A_in→tap·G_ff·Z_merge = v1·(−gmf)·R3'' -- 경로 항이다. (merge 노드 부하 변화(gdsf 가 주경로 출력을 누르는 양)는
    경로 기여가 아니다: Π_main A_i 와 FF 항이 같은 Z_merge 를 쓸 때 둘의 합이 전회로와 같다.)"""
    ss, _m, _r = _chain(True)
    got = block_residual(ss, H.transfer({"in": 1.0}, "out"), H.chain3_struct(True))
    v1 = -C["gm1"] * _rp(1)
    term = v1 * (-C["gmf"]) * _rp(3, C["gdsf"])
    (fc,) = got.ff_contrib
    assert fc.gain_db == pytest.approx(H.db(term), rel=1e-9)
    main = -C["gm3"] * _rp(3, C["gdsf"]) * (-C["gm2"] * _rp(2) * v1)
    assert fc.sign == (1 if term * main > 0 else -1) == -1


def test_ff_reinforcing_path_sign_is_plus_even_when_ff_loads_merge():
    """[RED 예상 -- 이의] 보강 FF: 입력 in 에서 out 으로 바로 가는 CS(Mf gate in) -- 경로 부호 −(입력 1 V -> −gmf·Z) 이고 주경로(CS 3단)도 −: 같은 방향 -> sign +1
    (41 §1.12.2-4 '보강 +1'). Mf 의 gds 가 out 을 눌러도(부하) 그것은 경로 기여의 부호를 바꾸지 않는다."""
    nets = ("gnd", "vdd", "in", "v1", "v2", "out")
    _n, m, r, ground, inputs = H.chain3(with_ff=False)
    m = tuple(m) + (H.mos("Mf", "out", "in", "gnd", "gnd", C["gmf"], C["gdsf"]),)
    ss = H.circuit(nets, m, r, ground, inputs)
    s0 = H.chain3_struct(False)
    vs = H.vstruct("transfer:0", {"in": 1.0}, ("out",), s0.blocks,
                   (H.ff("in->out", "in", "out", ("Mf",), ("out",), ("v1",), ("M1",)),), ("M1",))
    got = block_residual(ss, H.transfer({"in": 1.0}, "out"), vs)
    term = 1.0 * (-C["gmf"]) * _rp(3, C["gdsf"])
    (fc,) = got.ff_contrib
    assert got.gain_residual_db == pytest.approx(0.0, abs=1e-9)
    assert fc.sign == 1
    assert fc.gain_db == pytest.approx(H.db(term), rel=1e-9)


def test_feedback_resistor_across_blocks_leaves_residual_and_marks_decomposed():
    """블록을 가로지르는 되먹임 저항 Rf(out -> v1): 블록 2 는 '분해값'(입력 넷과 소유 노드를 잇는 저항), 잔차 ≠ 0
    (계약 10.6 '잔차가 0 이 아닌 회로는 블록을 가로지르는 되먹임의 신호').
    분해: v1 = −gm1/(1/r1 + gds1 + 1/Rf)(out 접지), out = (1/Rf − gm2)/(gds2 + 1/r2 + 1/Rf)·v1. 전회로 = 독립 풀이."""
    rf = 2e5
    nets = ("gnd", "vdd", "in", "v1", "out")
    m = (H.mos("M1", "v1", "in", "gnd", "gnd", C["gm1"], C["gds1"]), H.mos("M2", "out", "v1", "gnd", "gnd", C["gm2"], C["gds2"]))
    r = (H.res("R1", "vdd", "v1", C["r1"]), H.res("R2", "vdd", "out", C["r2"]), H.res("Rf", "out", "v1", rf))
    ss = H.circuit(nets, m, r, ("gnd", "vdd"), ("in",))
    vs = H.vstruct("v", {"in": 1.0}, ("out",), (H.block(("v1",), ("in",), ("v1",), ("in", "v1"), stage=1),
                                               H.block(("out",), ("v1",), ("out",), ("v1", "out"), stage=2)))
    got = block_residual(ss, H.transfer({"in": 1.0}, "out"), vs)
    v1 = -C["gm1"] / (1 / C["r1"] + C["gds1"] + 1 / rf)
    dec = (1 / rf - C["gm2"]) / (C["gds2"] + 1 / C["r2"] + 1 / rf) * v1
    full = H.sense_of(H.ref_solve(m, r, {"gnd": 0.0, "vdd": 0.0, "in": 1.0}), "out")
    assert got.blocks[1].decomposed_only is True          # 입력 넷(v1)과 소유 노드(out)를 잇는 저항(계약 10.6). 블록 1 표시는 설계 문구가 모호 -- 단정 안 함
    assert got.decomposed_gain_db == pytest.approx(H.db(dec), rel=1e-12)
    assert got.gain_residual_db == pytest.approx(H.db(full) - H.db(dec), rel=1e-9)
    assert abs(got.gain_residual_db) > 1e-3


def test_undefined_codes():
    ss, _m, _r = _chain(False)
    s = H.chain3_struct(False)
    assert codes(block_residual(ss, ViewDecl("ratio"), s).undefined) == {"unsupported_view"}
    empty = H.vstruct("v", {"in": 1.0}, ("out",), ())
    assert codes(block_residual(ss, H.transfer({"in": 1.0}, "out"), empty).undefined) == {"no_blocks"}
    got = block_residual(ss, H.transfer({"in": 1.0}, "out"), s)
    assert got.view == "transfer:0"


def test_name_bijection_invariance():
    ss, m, r = _chain(True)
    a = block_residual(ss, H.transfer({"in": 1.0}, "out"), H.chain3_struct(True))
    nmap = {"in": "z_in", "v1": "k3", "v2": "a7", "out": "b0", "vdd": "pp", "gnd": "nn"}
    dmap = {"M1": "Y", "M2": "X", "M3": "W", "Mf": "A", "R1": "Rc", "R2": "Rb", "R3": "Ra"}
    nets, _m, _r, ground, inputs = H.chain3()
    nets2, m2, r2 = H.rename(nets, m, r, nmap, dmap, order_seed=5)
    ss2 = H.circuit(nets2, m2, r2, [nmap[g] for g in ground], [nmap[i] for i in inputs])
    s2 = H.vstruct("transfer:0", {"z_in": 1.0}, ("b0",),
                   (H.block(("k3",), ("z_in",), ("k3",), ("z_in", "k3"), stage=1, input_cells=("Y",)),
                    H.block(("a7",), ("k3",), ("a7",), ("k3", "a7"), stage=2, input_cells=("X",)),
                    H.block(("b0",), ("a7",), ("b0",), ("a7", "b0"), stage=3, input_cells=("W",))),
                   (H.ff("k3->b0", "k3", "b0", ("A",), ("b0",), ("a7",), ("X",)),), ("Y",))
    b = block_residual(ss2, H.transfer({"z_in": 1.0}, "b0"), s2)
    assert b.full_gain_db == pytest.approx(a.full_gain_db, rel=1e-12)
    assert b.decomposed_gain_db == pytest.approx(a.decomposed_gain_db, rel=1e-12)
    assert [x.gain_db for x in b.blocks] == pytest.approx([x.gain_db for x in a.blocks], rel=1e-12)
    assert [(c.gain_db, c.sign) for c in b.ff_contrib] == [(pytest.approx(c.gain_db, rel=1e-12), c.sign) for c in a.ff_contrib]
    assert set(b.read_devices) == {dmap[d] for d in a.read_devices}


def test_deterministic():
    ss, _m, _r = _chain(True)
    args = (ss, H.transfer({"in": 1.0}, "out"), H.chain3_struct(True))
    assert block_residual(*args) == block_residual(*args)


# ---------------------------------------------------------------- ngcc 실제 구조 + 합성 소신호 값

def _ngcc():
    nets, m, r, ground, inputs = N.hand_circuit()
    (vs,) = N.structure_of(N.s1v()).views
    return H.circuit(nets, m, r, ground, inputs), m, r, ground, vs


def _ngcc_terms(m, r, ground):
    """(b) 전회로 독립 풀이에서 41 §1.12.2-4 의 항: 주경로 = v2·(−gm13)·Z, FF2 = v1·(−gm14)·Z, FF1 = v_NX·(−gm7)·Z,
    Z = Vout 노드 임피던스(모든 부하 gds7 + gds12 + gds13 + gds14). V1·V2·NX 는 Vout 에 gate 로만 닿아 전회로 값 = 사슬 값."""
    fixed = {n: 0.0 for n in ground}
    fixed.update({"Vinp": 0.5, "Vinn": -0.5})
    v = H.ref_solve(m, r, fixed)
    val = N.VALUES
    z = H.par(val["M7"][1], val["M12"][1], val["M13"][1], val["M14"][1])
    main = v["V2"] * (-val["M13"][0]) * z
    ff2 = v["V1"] * (-val["M14"][0]) * z
    ff1 = v["NX"] * (-val["M7"][0]) * z
    return v, main, {"V1->Vout": ff2, "ND->Vout": ff1}


def test_ngcc_residual_zero_and_full_gain():
    ss, m, r, ground, vs = _ngcc()
    got = block_residual(ss, N.view(), vs)
    v, main, ff = _ngcc_terms(m, r, ground)
    assert main + sum(ff.values()) == pytest.approx(v["Vout"], rel=1e-9)          # 항 분해의 자기 일관성(손 유도 확인)
    assert got.full_gain_db == pytest.approx(H.db(v["Vout"]), rel=1e-12)
    assert got.gain_residual_db == pytest.approx(0.0, abs=1e-9)
    assert [b.key for b in got.blocks] == [("V1",), ("V2",), ("Vout",)]
    assert {c.id for c in got.ff_contrib} == {"V1->Vout", "ND->Vout"}


def test_ngcc_ff_contrib_is_reinforcing_path_term():
    """[RED 예상 -- 이의, 작성자 10.8 'FF 둘 −1 부호'] 41 §1.12.2-4 'ss.ff_contrib{gain_db, sign}' = 경로 항 A_in→tap·G_ff·Z_merge 의 크기와 주경로 대비 부호.
    ngcc 의 FF 두 묶음은 주경로와 같은 방향(push-pull 출력단을 이루는 보강 경로 -- V1->V2 는 M8·M10 두 번 반전으로 비반전, 출력단 M13·M14·M7 은
    모두 반전)이라 sign = +1 이어야 한다. FF 소자의 gds 가 merge 노드를 누르는 부하 효과는 경로 기여가 아니다."""
    ss, m, r, ground, vs = _ngcc()
    got = block_residual(ss, N.view(), vs)
    _v, main, ff = _ngcc_terms(m, r, ground)
    by_id = {c.id: c for c in got.ff_contrib}
    for fid, term in ff.items():
        assert term * main > 0, fid                                                  # 손 유도 확인: 보강
        assert by_id[fid].sign == 1, (fid, by_id[fid])
        assert by_id[fid].gain_db == pytest.approx(H.db(term), rel=1e-9), fid


# ---------------------------------------------------------------- library 일반화 측정(이름 없는 합성 값 -- u7_ngcc.library_case)
# 계약 10.6 '정상 회로의 잔차는 부동소수 바닥(0.0 dB) -- 잔차가 0 이 아닌 회로는 블록을 가로지르는 되먹임이나 구조 모형 누락의 신호'.
# 작성자 10.8 표가 0 이라고 적은 7회로(봉인 점이 있던 회로)를 합성 값으로 다시 잰다(봉인 점과 무관한 구조 성질이어야 한다).
# current_reuse_telescopic_ota·sf_pushpull_output_opamp 는 작성자 측 봉인 점이 없어 주장이 없다 -- 단정하지 않고 값만 보고(test 밖 측정).
CLAIMED_ZERO = ("common_gate_amplifier", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier", "pushpull_follower_buffer",
                "two_stage_ota", "two_stage_ota_sf")


@pytest.mark.parametrize("name", CLAIMED_ZERO)
def test_library_residual_floor(name):
    ss, views, decls = N.library_case(name)
    assert views
    for vs, decl in zip(views, decls):
        got = block_residual(ss, decl, vs)
        assert got.undefined == (), (name, got.undefined)
        assert abs(got.gain_residual_db) <= 1e-9, (name, got.gain_residual_db)
        assert got.full_gain_db == pytest.approx(got.decomposed_gain_db, abs=1e-9)
