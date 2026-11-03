"""metrics/block_gain_model.py -- `block_gain_model_of(local, spec) -> (BlockModel | None, 미상 사유 | None)`
(metrics CONTRACT 10.3 '국소 모형'·'축', 설계 41 2.1·4.2 축 표).

oracle (a) 구성으로 정답이 정해진 합성 입력: 손 `LocalInputs`·`BlockSpec` 로 축 개수·크기·격자 곱 Π 를 41 4.2 축 표와 계약 10.3 규칙으로 손으로 센다.
- 축 크기 = toy LUT 격자 크기(|VGS| 19, |L| 2, |VDS| 7, |VS| 6) -- 모듈 gb4_hand 의 격자 상수.
- 그룹 규칙: vgs = 같은 (gate, source) ∪ 같은 궤도, L = 같은 L 동치류 ∪ 같은 궤도, vds = 비 diode 같은 궤도, vsb = 소스 ≠ bulk 인 MOS 의 같은 궤도,
  current = θ 전류 대표마다(저항·값 선언 전류원 항이 없으면 0차 동차라 첫 원소를 뺀다), resistor = θ 저항마다(값 선언 저항은 고정).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from gmid_engine.metrics import BlockModel, block_gain_model_of

from .gb4_hand import GRIDS, L_GRID, VDS_GRID, VGS_GRID, VS_GRID, block_spec, local_inputs

NG, NL, ND, NS = len(VGS_GRID), len(L_GRID), len(VDS_GRID), len(VS_GRID)
CS = (("M1", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "pb", "vdd"))


def _kinds(m):
    return sorted((a.kind, a.size) for a in m.axes)


def _cs_spec(**kw):
    return block_spec(("out",), ("M1", "M2"), ("in",), ("out",), ("in", "out"), ground=("gnd", "vdd", "pb"), **kw)


def test_cs_axes_and_grid_product():
    m, why = block_gain_model_of(local_inputs(CS), _cs_spec())
    assert why is None and isinstance(m, BlockModel)
    # 손: 두 MOS 가 다른 (gate, source)·다른 궤도 -> vgs 2, L 2, vds 2; 소스 = bulk(레일) -> vsb 없음; 같은 θ 전류 하나만 읽고 저항 없음 -> 정규화
    assert _kinds(m) == sorted([("vgs", NG)] * 2 + [("L", NL)] * 2 + [("vds", ND)] * 2)
    assert m.pi == NG ** 2 * NL ** 2 * ND ** 2 == math.prod(a.size for a in m.axes)
    assert tuple(m.normalized) == ("I0",)
    assert m.nodes == ("out",) and m.driven == ("in",)
    assert [o[0] for o in m.outputs] == ["out"]
    assert {x.name: x.vsb_axis for x in m.mos} == {"M1": -1, "M2": -1}


def test_vgs_and_vds_axis_values_are_lut_grids():
    m, _ = block_gain_model_of(local_inputs(CS), _cs_spec())
    for a in m.axes:
        ref = {"vgs": VGS_GRID, "L": L_GRID, "vds": VDS_GRID}[a.kind]
        assert np.allclose(np.asarray(a.values, float), ref, rtol=0, atol=1e-15)
        assert a.continuous is False


def test_follower_has_vsb_axis():
    # M1 nmos (vdd, in, out), bulk gnd ≠ 소스 out -> vsb 축(41 4.2 K3); drain vdd 라도 비 diode 라 vds 축
    loc = local_inputs((("M1", "nmos", "vdd", "in", "out"),))
    m, why = block_gain_model_of(loc, block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out")))
    assert why is None
    assert _kinds(m) == sorted([("vgs", NG), ("L", NL), ("vds", ND), ("vsb", NS)])
    assert m.pi == NG * NL * ND * NS


def test_same_orbit_pair_shares_axes():
    # 차동쌍 M1/M2 같은 궤도(0): vgs·L·vds·vsb 가 각 한 축. 꼬리 tail 은 블록 노드(이상 전류원 -- 컨덕턴스 없음)
    devs = (("M1", "nmos", "x", "inp", "tail"), ("M2", "nmos", "y", "inn", "tail"))
    loc = local_inputs(devs, orbit={"M1": 0, "M2": 0}, basis_rows={"M1": (("I0", 0.5),), "M2": (("I0", 0.5),)})
    spec = block_spec(("x", "y"), ("M1", "M2"), ("inp", "inn"), ("x", "y"), ("inp", "inn", "tail", "x", "y"))
    m, why = block_gain_model_of(loc, spec)
    assert why is None
    assert _kinds(m) == sorted([("vgs", NG), ("L", NL), ("vds", ND), ("vsb", NS)])
    # 다른 궤도면 축이 둘씩
    loc2 = local_inputs(devs, orbit={"M1": 0, "M2": 1}, basis_rows={"M1": (("I0", 0.5),), "M2": (("I0", 0.5),)})
    m2, _ = block_gain_model_of(loc2, spec)
    assert _kinds(m2) == sorted([("vgs", NG)] * 2 + [("L", NL)] * 2 + [("vds", ND)] * 2 + [("vsb", NS)] * 2)
    assert m2.pi == m.pi ** 2


def test_two_drive_inputs_give_two_patterns_and_excite_weights_override():
    devs = (("M1", "nmos", "x", "inp", "tail"), ("M2", "nmos", "y", "inn", "tail"))
    loc = local_inputs(devs, orbit={"M1": 0, "M2": 0}, basis_rows={"M1": (("I0", 0.5),), "M2": (("I0", 0.5),)})
    # excite 가 가중을 주지 않으면(뷰 여기 없음) 두 입력 = (+½, −½)·(+½, +½) 두 패턴(계약 10.3)
    spec = block_spec(("x", "y"), ("M1", "M2"), ("inp", "inn"), ("x", "y"), ("inp", "inn", "tail", "x", "y"), excite=())
    m, _ = block_gain_model_of(loc, spec)
    pats = sorted(tuple(sorted(dict(p).items())) for p in m.patterns)
    assert pats == sorted([(("inn", -0.5), ("inp", 0.5)), (("inn", 0.5), ("inp", 0.5))]) or \
        pats == sorted([(("inn", 0.5), ("inp", -0.5)), (("inn", 0.5), ("inp", 0.5))])
    # 뷰 여기가 두 입력을 모두 주면 그 가중 하나
    spec_w = block_spec(("x", "y"), ("M1", "M2"), ("inp", "inn"), ("x", "y"), ("inp", "inn", "tail", "x", "y"),
                        excite=(("inp", 0.5), ("inn", -0.5)))
    mw, _ = block_gain_model_of(loc, spec_w)
    assert [dict(p) for p in mw.patterns] == [{"inp": 0.5, "inn": -0.5}]
    # 출력 넷 둘 = 차동(부호 반대)
    assert sorted(s for _, s in m.outputs) == [-1, 1]


def test_shared_gate_source_is_one_vgs_axis():
    # M1·M3 같은 (gate in, source gnd), 다른 궤도 -> vgs 한 축, L·vds 는 각자
    devs = (("M1", "nmos", "out", "in", "gnd"), ("M3", "nmos", "out", "in", "gnd"), ("M2", "pmos", "out", "pb", "vdd"))
    m, why = block_gain_model_of(local_inputs(devs), block_spec(("out",), ("M1", "M2", "M3"), ("in",), ("out",), ("in", "out"),
                                                        ground=("gnd", "vdd", "pb")))
    assert why is None
    assert sorted(a.kind for a in m.axes).count("vgs") == 2          # {M1, M3} 그룹 + M2
    assert sorted(a.kind for a in m.axes).count("L") == 3
    assert sorted(a.kind for a in m.axes).count("vds") == 3


def test_l_class_label_merges_l_axes():
    loc = local_inputs(CS, l_label={"M1": "c0", "M2": "c0"})
    m, _ = block_gain_model_of(loc, _cs_spec())
    assert sorted(a.kind for a in m.axes).count("L") == 1


def test_diode_has_no_vds_axis_only_when_vds_grid_holds_vgs_nodes():
    # diode(gate == drain) M2 pmos (x, x, vdd): VDS = VGS 마디. toy VDS 격자(0.3 간격)는 VGS 마디(0.1 간격)를 다 갖지 않는다 -> diode 도 자기 축
    devs = (("M1", "nmos", "x", "in", "gnd"), ("M2", "pmos", "x", "x", "vdd"))
    spec = block_spec(("x",), ("M1", "M2"), ("in",), ("x",), ("in", "x"))
    m, _ = block_gain_model_of(local_inputs(devs), spec)
    assert {x.name: x.vds_axis >= 0 for x in m.mos} == {"M1": True, "M2": True}
    # VDS 격자 = VGS 격자인 LUT 격자면 diode 는 축이 없다(vds_axis −1)
    same = (L_GRID, VGS_GRID, VGS_GRID, VS_GRID)
    m2, _ = block_gain_model_of(local_inputs(devs, grids=same), spec)
    assert {x.name: x.vds_axis for x in m2.mos}["M2"] == -1
    assert sorted(a.kind for a in m2.axes).count("vds") == 1


def test_theta_resistor_gives_continuous_resistor_and_current_axes():
    # CS + θ 저항 부하 R1(out, vdd): 저항이 있으면 gain 이 전류에 0차 동차가 아니다 -> current 축(정규화 없음) + resistor 축, 둘 다 연속
    devs = (("M1", "nmos", "out", "in", "gnd"),)
    loc = local_inputs(devs, passives=(("R1", "resistor", "out", "vdd"),), element_value={"R1": None},
                       resistor_box={"R1": (1e3, 1e5)}, basis_rows={"M1": (("I0", 1.0),), "R1": (("I0", 1.0),)})
    spec = block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), passives=("R1",))
    m, why = block_gain_model_of(loc, spec)
    assert why is None
    kinds = {a.kind: a for a in m.axes}
    assert "current" in kinds and "resistor" in kinds
    assert kinds["current"].continuous and kinds["resistor"].continuous
    assert tuple(m.normalized) == ()
    # current 격자 = θ 상자 [1e-6, 1e-4] 위 로그 균등 |VGS 격자| 점(계약 10.3)
    cur = np.asarray(kinds["current"].values, float)
    assert kinds["current"].size == NG
    assert cur[0] == pytest.approx(1e-6, rel=1e-12) and cur[-1] == pytest.approx(1e-4, rel=1e-12)
    assert np.allclose(np.diff(np.log(cur)), np.log(1e-4 / 1e-6) / (NG - 1), rtol=1e-9)
    # resistor 격자 = 컨덕턴스 [1/R_hi, 1/R_lo] 로그 균등
    g = np.sort(np.asarray(kinds["resistor"].values, float))
    assert g[0] == pytest.approx(1e-5, rel=1e-12) and g[-1] == pytest.approx(1e-3, rel=1e-12)
    assert np.allclose(np.diff(np.log(g)), np.diff(np.log(g))[0], rtol=1e-9)


def test_declared_resistor_is_fixed_conductance():
    devs = (("M1", "nmos", "out", "in", "gnd"),)
    loc = local_inputs(devs, passives=(("R1", "resistor", "out", "vdd"),), element_value={"R1": 2e4},
                       basis_rows={"M1": (("I0", 1.0),), "R1": (("I0", 1.0),)})
    m, why = block_gain_model_of(loc, block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), passives=("R1",)))
    assert why is None
    assert "resistor" not in {a.kind for a in m.axes}
    (r,) = m.res
    assert r.axis == -1 and r.g_fixed == pytest.approx(1.0 / 2e4, rel=1e-15)


def test_unknown_reasons():
    loc = local_inputs(CS)
    # 구동 입력 셋 -> 미상
    m, why = block_gain_model_of(local_inputs((("M1", "nmos", "out", "a", "gnd"), ("M2", "nmos", "out", "b", "gnd"),
                                       ("M3", "nmos", "out", "c", "gnd"))),
                         block_spec(("out",), ("M1", "M2", "M3"), ("a", "b", "c"), ("out",), ("a", "b", "c", "out"), excite=()))
    assert m is None and why == "block_input_pattern_unsupported"
    # 출력 없음
    m, why = block_gain_model_of(loc, block_spec(("out",), ("M1", "M2"), ("in",), (), ("in", "out"), ground=("gnd", "vdd", "pb")))
    assert m is None and why == "block_output_missing"
    # θ 전류 대표의 상자 없음
    m, why = block_gain_model_of(local_inputs(CS, current_box={}), _cs_spec())
    assert m is None and why == "current_box_missing"
    # θ 저항 상자 없음
    loc_r = local_inputs((("M1", "nmos", "out", "in", "gnd"),), passives=(("R1", "resistor", "out", "vdd"),),
                         element_value={"R1": None}, resistor_box={},
                         basis_rows={"M1": (("I0", 1.0),), "R1": (("I0", 1.0),)})
    m, why = block_gain_model_of(loc_r, block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), passives=("R1",)))
    assert m is None and why == "resistor_box_missing"


def test_name_bijection_keeps_axis_structure():
    ren = {"out": "n7", "in": "a_in", "pb": "zb"}
    dev = {"M1": "X9", "M2": "A0"}
    cs2 = tuple((dev[n], k, ren.get(d, d), ren.get(g, g), ren.get(s, s)) for n, k, d, g, s in reversed(CS))
    m1, _ = block_gain_model_of(local_inputs(CS), _cs_spec())
    m2, _ = block_gain_model_of(local_inputs(cs2), block_spec(("n7",), ("X9", "A0"), ("a_in",), ("n7",), ("a_in", "n7"),
                                                       ground=("gnd", "vdd", "zb")))
    assert _kinds(m1) == _kinds(m2) and m1.pi == m2.pi


def test_deterministic():
    a, _ = block_gain_model_of(local_inputs(CS), _cs_spec())
    b, _ = block_gain_model_of(local_inputs(CS), _cs_spec())
    assert (a.pi, _kinds(a), a.nodes, a.driven, a.patterns, a.outputs) == (b.pi, _kinds(b), b.nodes, b.driven, b.patterns, b.outputs)


# =====================================================================================================================
# [UB-1 + NL-1, card 20261104-ub1-nl1] 행 모드 U_b -- interface card T-2·T-2b·T-3·T-3a·T-3b·T-4d·T-8·T-9 (C-2·C-3·C-4).
# oracle (a): toy LUT 해석식(x = gm/ID = 20 − 8·VGS, y = gds/ID = 0.1, z = gmb/ID = 4·VS; gb4_hand) 위에서 KCL 을 손으로 푼 닫힌 식.
# 값 선언 저항은 고정 컨덕턴스, 행 값 = LUT 마디 값(gm = x·I, gds = y·I, gmb = z·I). oracle (b): `u7_hand.ref_solve`(독립 정방향 풀이).
# =====================================================================================================================

from gmid_engine.metrics import ParamTables, block_local_gain, row_gains  # noqa: E402

from . import u7_hand as H  # noqa: E402
from .gb4_hand import LAM, W_KEY, memo_of, write_lut, x_of, z_of  # noqa: E402

UB1_W_KEYS = {"nmos": W_KEY, "pmos": W_KEY}


@pytest.fixture(scope="module")
def ub1_tables(tmp_path_factory):
    return ParamTables(memo_of(write_lut(tmp_path_factory.mktemp("ub1_rows_toy"))), UB1_W_KEYS, GRIDS)


def _ub1_loc(devs, passives=(), **kw):
    """passives = ((이름, kind, t0, t1, 값), ...) 값 선언 수동소자. 기본 θ 전류 I0 한 원소(계수 1)."""
    basis = {d[0]: (("I0", 1.0),) for d in devs}
    basis.update({p[0]: (("I0", 1.0),) for p in passives})
    return local_inputs(devs, passives=tuple(p[:4] for p in passives), element_value={p[0]: p[4] for p in passives},
                        basis_rows=basis, **kw)


def _ub1_ax(m, kind, name=None):
    hits = [k for k, a in enumerate(m.axes) if a.kind == kind and (name is None or name in a.label)]
    assert len(hits) == 1, (kind, name, [(a.kind, a.label) for a in m.axes])
    return hits[0]


def _ub1_idx(m, picks):
    """picks = {(축 종류, 소자 이름 | None): index} -> (1, 축 수) 행. 나머지 축은 index 0."""
    row = np.zeros((1, len(m.axes)), int)
    for (kind, name), k in picks.items():
        row[0, _ub1_ax(m, kind, name)] = k
    return row


def _ub1_cs_row(passives, outputs=("out",), nodes=("in", "out"), pass_names=("RL",), devs=None, members=("M1",)):
    """CS 형 블록의 행 모드 모델(입력 구성: LocalInputs·BlockSpec)."""
    devs = devs or (("M1", "nmos", "out", "in", "gnd"),)
    loc = _ub1_loc(devs, passives)
    spec = block_spec(("out",), members, ("in",), outputs, nodes, passives=pass_names)
    m, why = block_gain_model_of(loc, spec)
    assert why is None
    return m


def test_ub1_row_mode_omits_unfixed_load_and_bounds_sealed(ub1_tables):
    """T-2 (a) + C-4: 행 모드는 비멤버 M2 를 스탬프하지 않고 omitted_load 에 넣는다 -> 행 값 = gm1/(gds1 + G1) (I 축은 연속).
    같은 값의 봉인 값(M2 스탬프) |gain| = gm1/(gds1 + G1 + g_in) 이하이고 비 = (gds1 + G1 + g_in)/(gds1 + G1), g_in = gm2 + gmb2 + gds2."""
    r1, r2, gm2, gds2, gmb2 = 2e4, 3e4, 0.9e-3, 1.5e-5, 2.2e-4
    devs = (("M1", "nmos", "x", "in", "gnd"), ("M2", "nmos", "out", "vb", "x"))
    loc = _ub1_loc(devs, (("R1", "resistor", "vdd", "x", r1), ("R2", "resistor", "vdd", "out", r2)))
    spec = block_spec(("x",), ("M1",), ("in",), ("x",), ("in", "x"), ground=("gnd", "vdd", "vb"), passives=("R1",), others=("out",))
    m, why = block_gain_model_of(loc, spec)
    assert why is None and tuple(m.nodes) == ("x",)
    assert getattr(m, "omitted_load", None) == ("M2",)
    assert getattr(m, "decomposed_only", None) is False
    ig, ic = 4, 9
    cur = np.geomspace(1e-6, 1e-4, NG)[ic]
    gm1, gds1, g1 = x_of(VGS_GRID[ig]) * cur, LAM * cur, 1.0 / r1
    row = row_gains(m, ub1_tables, _ub1_idx(m, {("vgs", "M1"): ig, ("current", None): ic}))[0]
    assert row == pytest.approx(gm1 / (gds1 + g1), rel=1e-9)
    nets = ("gnd", "vdd", "vb", "in", "x", "out")
    mm = (H.mos("M1", "x", "in", "gnd", "gnd", gm1, gds1), H.mos("M2", "out", "vb", "x", "gnd", gm2, gds2, gmb2))
    ss = H.circuit(nets, mm, (H.res("R1", "vdd", "x", r1), H.res("R2", "vdd", "out", r2)), ("gnd", "vdd", "vb"), ("in",))
    sealed = block_local_gain(ss, H.block(("x",), ("in",), ("x",), ("in", "x"), members=("M1", "R1")), others=("out",))
    assert row >= abs(sealed.gain)
    assert row / abs(sealed.gain) == pytest.approx((gds1 + g1 + gm2 + gmb2 + gds2) / (gds1 + g1), rel=1e-9)


def test_ub1_row_mode_feedback_resistor_marks_decomposed_only():
    """T-2b (a): CS + 되먹임 Rf(in–out) -> 모델의 decomposed_only True."""
    devs = (("M1", "nmos", "out", "in", "gnd"),)
    loc = _ub1_loc(devs, (("RL", "resistor", "vdd", "out", 3e4), ("Rf", "resistor", "in", "out", 1e5)))
    m, why = block_gain_model_of(loc, block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), passives=("RL",)))
    assert why is None
    assert getattr(m, "decomposed_only", None) is True


def test_ub1_row_mode_dead_end_branch_dropped(ub1_tables):
    """T-3 (a) 행 모드: CS + Rz(out–mz) 막다른 가지는 U_b 에서 빠진다 -> nodes == ("out",), 있는·없는 모델의 행 값이 같고 gm/(gds + G) 와 같다."""
    ig, ic, rl = 6, 3, 3e4
    cur = np.geomspace(1e-6, 1e-4, NG)[ic]
    want = x_of(VGS_GRID[ig]) * cur / (LAM * cur + 1.0 / rl)
    for extra in ((), (("Rz", "resistor", "out", "mz", 5e3),)):
        m = _ub1_cs_row((("RL", "resistor", "vdd", "out", rl),) + extra)
        assert tuple(m.nodes) == ("out",)
        row = row_gains(m, ub1_tables, _ub1_idx(m, {("vgs", "M1"): ig, ("current", None): ic}))[0]
        assert row == pytest.approx(want, rel=1e-9)


def test_ub1_row_mode_output_exception_and_gate_reader(ub1_tables):
    """T-3a (a): 출력이 mz 면 mz ∈ nodes 이고 |V(mz)| = |V(out)|(Rz 전류 0) -> 행 = gm/(gds + G).
    T-3b (a): mz 를 gate 로 읽는 M2(d o2, g mz, s gnd), R2(vdd–o2), 출력 o2: 행 = [gm1/(gds + G1)]·[gm2/(gds + G2)], mz ∈ nodes."""
    rl, rz, r2, ig1, ig2, ic = 3e4, 5e3, 2.5e4, 3, 7, 5
    cur = np.geomspace(1e-6, 1e-4, NG)[ic]
    gm1, gm2, gds = x_of(VGS_GRID[ig1]) * cur, x_of(VGS_GRID[ig2]) * cur, LAM * cur
    base = (("RL", "resistor", "vdd", "out", rl), ("Rz", "resistor", "out", "mz", rz))
    ma = _ub1_cs_row(base, outputs=("mz",), nodes=("in", "out", "mz"), pass_names=("RL", "Rz"))
    assert "mz" in ma.nodes
    ra = row_gains(ma, ub1_tables, _ub1_idx(ma, {("vgs", "M1"): ig1, ("current", None): ic}))[0]
    assert ra == pytest.approx(gm1 / (gds + 1.0 / rl), rel=1e-9)
    devs = (("M1", "nmos", "out", "in", "gnd"), ("M2", "nmos", "o2", "mz", "gnd"))
    mb = _ub1_cs_row(base + (("R2", "resistor", "vdd", "o2", r2),), outputs=("o2",), nodes=("in", "out", "mz", "o2"),
                     pass_names=("R2", "RL", "Rz"), devs=devs, members=("M1", "M2"))
    assert "mz" in mb.nodes
    rb = row_gains(mb, ub1_tables, _ub1_idx(mb, {("vgs", "M1"): ig1, ("vgs", "M2"): ig2, ("current", None): ic}))[0]
    assert rb == pytest.approx(gm1 / (gds + 1.0 / rl) * gm2 / (gds + 1.0 / r2), rel=1e-9)


def test_ub1_row_mode_rejects_charge_node():
    """T-4d (a): 게이트 전용 용량 넷 n(C1 in–n, C2 n–gnd; attach 없음 = 0)을 가진 블록은 행 모드에서 모델이 없다:
    (None, "charge_node_row_mode")."""
    devs = (("M1", "nmos", "out", "n", "gnd"),)
    loc = _ub1_loc(devs, (("C1", "capacitor", "in", "n", 2e-12), ("C2", "capacitor", "n", "gnd", 3e-12),
                          ("RL", "resistor", "vdd", "out", 3e4)))
    m, why = block_gain_model_of(loc, block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), passives=("C1", "C2", "RL")))
    assert m is None and why == "charge_node_row_mode"


def test_ub1_both_modes_same_unknown_set_and_value(ub1_tables):
    """T-8 + C-3 (a)(b): sf 형 toy M5(d n5, g n5, s vdd) diode, M6(d y, g n5, s n5), 입력 M1(d y, g in, s gnd), 블록 nodes (in, y), members (M1, M5, M6).
    봉인 node_v 키 − 구동 = 행 nodes = {y, n5}. 값이 같으면 행 값 = 봉인 |gain| = 독립 ref_solve 의 |V(y)|."""
    devs = (("M1", "nmos", "y", "in", "gnd"), ("M5", "pmos", "n5", "n5", "vdd"), ("M6", "pmos", "y", "n5", "n5"))
    loc = local_inputs(devs)
    spec = block_spec(("y",), ("M1", "M5", "M6"), ("in",), ("y",), ("in", "y"), ground=("gnd", "vdd"))
    m, why = block_gain_model_of(loc, spec)
    assert why is None
    ig = {"M1": 4, "M5": 6, "M6": 9}
    isb = 2
    picks = {("vgs", n): k for n, k in ig.items()}
    picks[("vsb", "M6")] = isb
    row = row_gains(m, ub1_tables, _ub1_idx(m, picks))[0]
    gm = {n: x_of(VGS_GRID[k]) for n, k in ig.items()}
    gmb6 = z_of(VS_GRID[isb])
    rows = [H.mos("M1", "y", "in", "gnd", "gnd", gm["M1"], LAM), H.mos("M5", "n5", "n5", "vdd", "vdd", gm["M5"], LAM),
            H.mos("M6", "y", "n5", "n5", "vdd", gm["M6"], LAM, gmb6)]
    ref = H.ref_solve(rows, [], {"gnd": 0.0, "vdd": 0.0, "in": 1.0})
    ss = H.circuit(("gnd", "vdd", "in", "y", "n5"), rows, (), ("gnd", "vdd"), ("in",))
    sealed = block_local_gain(ss, H.block(("y",), ("in",), ("y",), ("in", "y"), members=("M1", "M5", "M6")))
    assert set(dict(sealed.node_v)) - {"in"} == {"y", "n5"} == set(m.nodes)
    assert abs(sealed.gain) == pytest.approx(abs(ref["y"]), rel=1e-9)
    assert row == pytest.approx(abs(ref["y"]), rel=1e-9)


def test_ub1_row_mode_follower_omitted_load(ub1_tables):
    """T-9 (a) 행 모드: 팔로워 M1(d vdd, g in, s out), 비멤버 M2(d out, g vb, s gnd) -> omitted_load == ("M2",),
    행 = gm1/(gm1 + gmb1 + gds1) = x/(x + y + z)."""
    devs = (("M1", "nmos", "vdd", "in", "out"), ("M2", "nmos", "out", "vb", "gnd"))
    spec = block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), ground=("gnd", "vdd", "vb"))
    m, why = block_gain_model_of(local_inputs(devs), spec)
    assert why is None
    assert getattr(m, "omitted_load", None) == ("M2",)
    ig, isb = 5, 2
    x, z = x_of(VGS_GRID[ig]), z_of(VS_GRID[isb])
    row = row_gains(m, ub1_tables, _ub1_idx(m, {("vgs", "M1"): ig, ("vsb", "M1"): isb}))[0]
    assert row == pytest.approx(x / (x + LAM + z), rel=1e-9)
