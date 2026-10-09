"""`ff_gm_ratio` -- 설계 41 §1.12.2-5(r_ff = G_ff / gm_in(B_b), G_ff = B_b 입력 넷 전압 -> merge 단락 전류 FF 경로 트랜스컨덕턴스(FF 안
미러 비 포함), gm_in = B_b input 셀 gm), 40 §3.8-8 표 행, 체크리스트 D-J2, metrics CONTRACT 10.6·10.9 (5)(크기 비, 묶음 최댓값).

oracle:
* (a) 탭이 B_b 입력 넷인 FF(2단 우회 단일 CS): 탭 = 1 V 구동, merge 단락 -> 전류 = gm_f 정확히 -> r = gm_f / gm_in(B_b).
  ngcc FF2(M14, 탭 V1, B_b = (V2,) 입력 셀 M8): r = gm14 / gm8 (작성자 앵커 '0.911 = gm14/gm8' 의 관계를 합성 값으로 재유도).
* (b) 탭이 B_b 내부 노드인 FF(ngcc FF1, 탭 ND): 전회로(모든 소자)에서 merge Vout 을 0 V 로 묶고 입력 차동 1 V(이름순 ±½)를 준 독립 numpy 풀이
  (`u7_hand.ref_solve`)의 M7 채널 전류 크기 / 입력쌍 gm 평균. 전회로 풀이는 블록 선택 규칙을 쓰지 않는다(ND·NX·TAIL 은 gate 로만 다른
  블록에 닿아 같은 값이어야 한다).
* (a) 분해능(계약 10.6): 탭 = 입력 넷인 FF 에서 r 은 gm_f·gm_in 에만 달린다 -> Σ|Δr| = r·ε + r·ε/(1 + ε)(gds·gmb 섭동은 변화 0).
"""
from __future__ import annotations

import pytest

from gmid_engine.metrics import FfRatio, ff_gm_ratio

from . import u7_hand as H
from . import u7_ngcc as N
from .conftest import codes

C = H.CH


def _toy():
    nets, m, r, ground, inputs = H.chain3()
    return H.circuit(nets, m, r, ground, inputs)


def test_tap_is_bypassed_input_ratio_exact():
    got = ff_gm_ratio(_toy(), H.chain3_struct(True))
    assert isinstance(got, FfRatio) and got.undefined == ()
    assert got.ratio == pytest.approx(C["gmf"] / C["gm2"], rel=1e-12)
    ((fid, r, g, gm_in),) = got.per_ff
    assert fid == "v1->out" and g == pytest.approx(C["gmf"], rel=1e-12) and gm_in == pytest.approx(C["gm2"], rel=1e-12)


def test_one_stage_bypass_from_view_input():
    """탭 in(B_b = (v1,) 입력 넷): Mf2(d v2, g in) -- r = gmf2 / gm1."""
    nets, m, r, ground, inputs = H.chain3(with_ff=False)
    m = tuple(m) + (H.mos("Mf2", "v2", "in", "gnd", "gnd", 3.3e-4, 1e-5),)
    ss = H.circuit(nets, m, r, ground, inputs)
    s0 = H.chain3_struct(False)
    vs = H.vstruct("t", {"in": 1.0}, ("out",), s0.blocks, (H.ff("in->v2", "in", "v2", ("Mf2",), ("v2",), ("v1",), ("M1",)),), ("M1",))
    assert ff_gm_ratio(ss, vs).ratio == pytest.approx(3.3e-4 / C["gm1"], rel=1e-12)


def test_ngcc_ff2_ratio_is_gm14_over_gm8():
    nets, m, r, ground, inputs = N.hand_circuit()
    vs = _ngcc_struct()
    got = ff_gm_ratio(H.circuit(nets, m, r, ground, inputs), vs)
    per = {row[0]: row for row in got.per_ff}
    assert per["V1->Vout"][1] == pytest.approx(N.VALUES["M14"][0] / N.VALUES["M8"][0], rel=1e-12)
    assert per["V1->Vout"][3] == pytest.approx(N.VALUES["M8"][0], rel=1e-12)


def test_ngcc_ff1_internal_tap_matches_full_circuit_short():
    nets, m, r, ground, inputs = N.hand_circuit()
    got = ff_gm_ratio(H.circuit(nets, m, r, ground, inputs), _ngcc_struct())
    fixed = {n: 0.0 for n in ground}
    fixed.update({"Vinn": 0.5, "Vinp": -0.5, "Vout": 0.0})          # 단위 구동(이름순 +½/−½), merge 단락
    v = H.ref_solve(m, r, fixed)
    gm7 = N.VALUES["M7"][0]
    g_ff = abs(gm7 * v["NX"])                                          # M7 채널 전류(d Vout, s gnd, v_d = 0)
    gm_in = (N.VALUES["M1"][0] + N.VALUES["M2"][0]) / 2
    per = {row[0]: row for row in got.per_ff}
    assert per["ND->Vout"][2] == pytest.approx(g_ff, rel=1e-9)
    assert per["ND->Vout"][1] == pytest.approx(g_ff / gm_in, rel=1e-9)
    assert got.ratio == pytest.approx(max(row[1] for row in got.per_ff), rel=1e-15)


def test_ratio_is_max_over_bundles():
    nets, m, r, ground, inputs = N.hand_circuit({"M14": (1e-5, 1e-7)})        # FF2 를 작게 -> 최댓값은 FF1
    got = ff_gm_ratio(H.circuit(nets, m, r, ground, inputs), _ngcc_struct())
    per = {row[0]: row[1] for row in got.per_ff}
    assert per["V1->Vout"] == pytest.approx(1e-5 / N.VALUES["M8"][0], rel=1e-12)
    assert got.ratio == max(per.values()) == per["ND->Vout"]


def test_resolution_tap_input_hand():
    eps = 2e-3
    ss = _toy()
    tols = {mm.label: eps for mm in ss.circuit.mos}
    got = ff_gm_ratio(ss, H.chain3_struct(True), tols)
    r = C["gmf"] / C["gm2"]
    assert got.resolution == pytest.approx(r * eps + r * eps / (1 + eps), rel=1e-9)
    assert ff_gm_ratio(ss, H.chain3_struct(True), dict(tols, Mf=None)).resolution is None


def test_undefined_codes():
    ss = _toy()
    s0 = H.chain3_struct(False)
    assert codes(ff_gm_ratio(ss, s0).undefined) == {"no_feedforward"}
    lost = H.vstruct("t", {"in": 1.0}, ("out",), s0.blocks, (H.ff("x", "v1", "out", ("Mf",), ("out",), ("nope",), ("M2",)),))
    assert codes(ff_gm_ratio(ss, lost).undefined) == {"bypassed_block_missing"}
    nocell = H.vstruct("t", {"in": 1.0}, ("out",), s0.blocks, (H.ff("x", "v1", "out", ("Mf",), ("out",), ("v2",), ()),))
    assert codes(ff_gm_ratio(ss, nocell).undefined) == {"bypassed_input_cells_missing"}
    nets, m, r, ground, inputs = H.chain3()
    zero = H.circuit(nets, tuple(dict(x, gm=0.0) if x["label"] == "M2" else x for x in m), r, ground, inputs)
    assert codes(ff_gm_ratio(zero, H.chain3_struct(True)).undefined) == {"gm_in_zero"}


def test_name_bijection_invariance():
    a = ff_gm_ratio(_toy(), H.chain3_struct(True))
    nets, m, r, ground, inputs = H.chain3()
    nmap = {"in": "q", "v1": "zz", "v2": "aa", "out": "m", "vdd": "p", "gnd": "g0"}
    dmap = {"M1": "K", "M2": "J", "M3": "I", "Mf": "B", "R1": "x", "R2": "y", "R3": "z"}
    nets2, m2, r2 = H.rename(nets, m, r, nmap, dmap, order_seed=9)
    vs = H.vstruct("t", {"q": 1.0}, ("m",),
                   (H.block(("zz",), ("q",), ("zz",), ("q", "zz"), stage=1, input_cells=("K",)),
                    H.block(("aa",), ("zz",), ("aa",), ("zz", "aa"), stage=2, input_cells=("J",)),
                    H.block(("m",), ("aa",), ("m",), ("aa", "m"), stage=3, input_cells=("I",))),
                   (H.ff("zz->m", "zz", "m", ("B",), ("m",), ("aa",), ("J",)),), ("K",))
    b = ff_gm_ratio(H.circuit(nets2, m2, r2, [nmap[x] for x in ground], [nmap[x] for x in inputs]), vs)
    assert b.ratio == pytest.approx(a.ratio, rel=1e-14)


def _ngcc_struct():
    """ngcc 구조 입력 -- 실제 S1v 에서(metric_structure)."""
    from gmid_engine.metrics import metric_structure
    (vs,) = metric_structure(N.s1v()).views
    return vs
