"""metrics/block_gain_bound.py -- `block_gain_bound(model, tables, budget, members) -> BlockBound` (metrics CONTRACT 10.3, 설계 41 4.2, D-GB4b·D-NM).

oracle (a) 손 계산(해석식 toy LUT: x = 20 − 8·VGS, y = 0.1, z = 4·VS; VGS 0..1.8 / 0.1, VS (−0.45, 0, 0.45, 0.9, 1.35, 1.8)):
- 소스 팔로워 gain x/(x + y + z) 의 격자 최댓값: z 가 가장 작은 VS = −0.45(z = −1.8)에서 x 가 작을수록 커진다 -> VGS 1.8(x = 5.6):
  A_max = 5.6/3.9. 분해능 b = 최대 행과 격자 이웃(축마다 ±1) gain 비의 dB 최댓값 = VS 이웃 0(z = 0, gain 5.6/5.7) 쪽:
  b = 20·log10((5.6/3.9)/(5.6/5.7)) (VGS 이웃 1.7: 6.4/4.7 -> 0.46 dB 로 더 작고, L·VDS 이웃은 같은 gain).
- CS gain x1/(y1 + y2): VGS 0(x = 20)에서 20/0.2 = 100 -> 40 dB, b = 20·log10(20/19.2) (VGS 이웃 0.1).
- 예산 게이트(41 4.2): Π > N_S 이면 미상(`grid_product_over_budget`), Π = N_S 면 전수(인증).
- CS + θ 저항 부하, 전류·저항 연속 축: gain = x·I/(y·I + G) 는 I 에 증가·G 에 감소라 축 끝(I_max, G_min)이 최대 -> 끝점 인증,
  A_max = 20·1e-4/(0.1·1e-4 + 1e-5) = 100 -> 40 dB.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from gmid_engine.metrics import BlockBound, ParamTables, ResLocal, block_gain_bound

from .gb4_hand import GRIDS, L_GRID, VDS_GRID, VGS_GRID, W_KEY, axis, cs_model, db, follower_model, memo_of, model, mosl, write_lut

W_KEYS = {"nmos": W_KEY, "pmos": W_KEY}
FOL_AMAX = 5.6 / 3.9
FOL_B = db(FOL_AMAX / (5.6 / 5.7))


@pytest.fixture(scope="module")
def tables(tmp_path_factory):
    return ParamTables(memo_of(write_lut(tmp_path_factory.mktemp("bound_toy"))), W_KEYS, GRIDS)


def _cond(bb):
    return {k.split(":")[0]: v for k, v in bb.row_condition}


def test_follower_bound_is_certified_with_hand_max_and_resolution(tables):
    m = follower_model()
    assert m.pi == 19 * 2 * 7 * 6
    bb = block_gain_bound(m, tables, m.pi, ("M1",))
    assert isinstance(bb, BlockBound)
    assert bb.status == "certified" and bb.reason is None
    assert bb.pi == m.pi
    assert bb.a_max_db == pytest.approx(db(FOL_AMAX), abs=1e-9)
    assert bb.b_db == pytest.approx(FOL_B, abs=1e-9)
    cond = _cond(bb)
    assert cond["vgs"] == pytest.approx(1.8, abs=1e-12) and cond["vsb"] == pytest.approx(-0.45, abs=1e-12)
    assert tuple(bb.members) == ("M1",)
    assert bb.n_rows >= m.pi                                  # 전수 평가(41 4.2 'Π ≤ N_S 면 모든 행')


def test_budget_gate_marks_unknown_when_grid_product_exceeds_ns(tables):
    m = follower_model()
    bb = block_gain_bound(m, tables, m.pi - 1, ("M1",))
    assert bb.status == "unknown" and bb.reason == "grid_product_over_budget"
    assert bb.a_max_db is None and bb.b_db is None
    assert bb.pi == m.pi


def test_cs_bound_is_forty_db(tables):
    m = cs_model()
    bb = block_gain_bound(m, tables, m.pi, ("M1", "M2"))
    assert bb.status == "certified"
    assert bb.a_max_db == pytest.approx(40.0, abs=1e-9)
    assert bb.b_db == pytest.approx(db(20.0 / 19.2), abs=1e-9)
    # 최대 행: M1 의 VGS 축(입력 소자 gm/ID 최대 = VGS 0)
    assert dict(bb.row_condition)["vgs:M1"] == pytest.approx(0.0, abs=1e-12)


def test_found_db_never_exceeds_certified_bound(tables):
    # found_db = 좌표 상승 하한 추정(보고만) -- 전수 상한보다 클 수 없다; 예산 밖이어도 보고된다(계약 10.3)
    m = cs_model()
    cert = block_gain_bound(m, tables, m.pi, ("M1", "M2"))
    over = block_gain_bound(m, tables, 1, ("M1", "M2"))
    assert cert.found_db is None or cert.found_db <= cert.a_max_db + 1e-9
    assert over.status == "unknown"
    if over.found_db is not None:
        assert over.found_db <= 40.0 + 1e-9


def test_continuous_axes_endpoint_maximum_is_certified(tables):
    i_grid = np.geomspace(1e-6, 1e-4, 19)
    g_grid = np.geomspace(1e-5, 1e-3, 19)
    axes = (axis("vgs", ("M1",), VGS_GRID), axis("L", ("M1",), L_GRID), axis("vds", ("M1",), VDS_GRID),
            axis("current", ("I0",), i_grid, True), axis("resistor", ("R1",), g_grid, True))
    m = model(("out",), ("out",), ("in",), ((("in", 1.0),),), (("out", 1),),
              (mosl("M1", "nmos", "out", "in", "gnd", "gnd", 0, 1, 2, -1, current=((3, 1.0),)),), axes,
              res=(ResLocal("R1", "out", "vdd", 4, None),))
    bb = block_gain_bound(m, tables, m.pi, ("M1",))
    assert bb.status == "certified"
    assert bb.a_max_db == pytest.approx(db(20.0 * 1e-4 / (0.1 * 1e-4 + 1e-5)), abs=1e-6)
    cond = _cond(bb)
    assert cond["current"] == pytest.approx(1e-4, rel=1e-9) and cond["resistor"] == pytest.approx(1e-5, rel=1e-9)


def test_deterministic(tables):
    m = follower_model()
    a = block_gain_bound(m, tables, m.pi, ("M1",))
    b = block_gain_bound(m, tables, m.pi, ("M1",))
    assert (a.status, a.a_max_db, a.b_db, a.row_condition, a.pi) == (b.status, b.a_max_db, b.b_db, b.row_condition, b.pi)


# =====================================================================================================================
# [UB-1 + NL-1, card 20261104-ub1-nl1] interface card T-2(load_note)·T-2b(decomposed_only_bound)·T-5·T-5a~d (E-16 L bin 안쪽 최대)
# =====================================================================================================================

def _ub1_local(devs, passives):
    from .gb4_hand import local_inputs
    basis = {d[0]: (("I0", 1.0),) for d in devs}
    basis.update({p[0]: (("I0", 1.0),) for p in passives})
    return local_inputs(devs, passives=tuple(p[:4] for p in passives), element_value={p[0]: p[4] for p in passives}, basis_rows=basis)


def test_ub1_bound_load_note_lists_omitted_load(tables):
    """T-2 (a): 행 모드가 비멤버 M2 를 스탬프하지 않으면 모든 BlockBound 반환 자리(certified·over budget)가
    load_note == ("load_admittance_unfixed", ("M2",)). 생략이 없는 CS 는 load_note None."""
    from gmid_engine.metrics import block_gain_model_of
    from .gb4_hand import block_spec
    devs = (("M1", "nmos", "x", "in", "gnd"), ("M2", "nmos", "out", "vb", "x"))
    loc = _ub1_local(devs, (("R1", "resistor", "vdd", "x", 2e4), ("R2", "resistor", "vdd", "out", 3e4)))
    m, why = block_gain_model_of(loc, block_spec(("x",), ("M1",), ("in",), ("x",), ("in", "x"), ground=("gnd", "vdd", "vb"),
                                                 passives=("R1",), others=("out",)))
    assert why is None
    want = ("load_admittance_unfixed", ("M2",))
    assert getattr(block_gain_bound(m, tables, m.pi, ("M1",)), "load_note", "absent") == want
    assert getattr(block_gain_bound(m, tables, 1, ("M1",)), "load_note", "absent") == want           # 예산 초과 반환 자리
    devs1 = (("M1", "nmos", "out", "in", "gnd"),)
    m1, why1 = block_gain_model_of(_ub1_local(devs1, (("RL", "resistor", "vdd", "out", 3e4),)),
                                   block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), passives=("RL",)))
    assert why1 is None
    assert getattr(block_gain_bound(m1, tables, m1.pi, ("M1",)), "load_note", "absent") is None


def test_ub1_bound_decomposed_only_is_unknown(tables):
    """T-2b (a): 되먹임 저항(입력–출력)이 있는 블록의 행 모델은 decomposed_only -> status unknown, reason decomposed_only_bound."""
    from gmid_engine.metrics import block_gain_model_of
    from .gb4_hand import block_spec
    devs = (("M1", "nmos", "out", "in", "gnd"),)
    loc = _ub1_local(devs, (("RL", "resistor", "vdd", "out", 3e4), ("Rf", "resistor", "in", "out", 1e5)))
    m, why = block_gain_model_of(loc, block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out"), passives=("RL",)))
    assert why is None
    bb = block_gain_bound(m, tables, m.pi, ("M1",))
    assert bb.status == "unknown" and bb.reason == "decomposed_only_bound"


# ---- E-16: 같은 bin 이웃 앵커 구간 안쪽 최대. 가짜 표(덕 타이핑) -- 앵커(lookup)는 평탄, lookup_at_l 이 구간 (La, Lb) 안에서 단봉.
# cs_model 한 블록(축 크기 1·1·3·3·1·1): gain = x1/(y1 + y2) = X0·(1 + h·bump(t))/(2·Y0), t = (L − La)/(Lb − La).
# 최대 행은 모두 같은 값(앵커 평탄)이라 L 축 index 0, 이웃 구간 = (La, Lb).
UB1_L = (1e-6, 2e-6, 4e-6)
UB1_X0, UB1_Y0, UB1_H = 12.0, 0.1, 0.5
UB1_T0 = 1.0 / 16.0


def _ub1_parabola(t):
    return 4.0 * t * (1.0 - t)                                    # 중심 t = ½ 에서 1


def _ub1_near_end(t):
    return t * (1.0 - t) ** 15 / (UB1_T0 * (1.0 - UB1_T0) ** 15)    # 단봉, t = 1/16 에서 1(구간 폭 ⅛ 이내), 양 끝 0


def _ub1_dip(t):
    return -4.0 * t * (1.0 - t)                                   # 내부 ≤ 끝(최대는 끝값)


class _Ub1Tables:
    def __init__(self, profile=None, same_bin=True, nan=False):
        self.profile, self.same_bin, self.nan, self.at_l_calls = profile, same_bin, nan, 0

    def lookup(self, kind, i_l, i_d, i_s, i_v):
        shape = np.broadcast(*(np.asarray(a) for a in (i_l, i_d, i_s, i_v))).shape
        return np.full(shape, UB1_X0), np.full(shape, UB1_Y0), np.zeros(shape)

    def lookup_at_l(self, kind, l_m, i_d, i_s, i_v):
        self.at_l_calls += 1
        l = np.asarray(l_m, dtype=float)
        shape = np.broadcast(l, *(np.asarray(a) for a in (i_d, i_s, i_v))).shape
        t = (np.broadcast_to(l, shape) - UB1_L[0]) / (UB1_L[1] - UB1_L[0])
        inside = (t > 0.0) & (t < 1.0)
        bump = np.where(inside, self.profile(np.clip(t, 0.0, 1.0)), 0.0) if kind == "nmos" else np.zeros(shape)
        x = np.full(shape, np.nan) if self.nan else UB1_X0 * (1.0 + UB1_H * bump)
        return x, np.full(shape, UB1_Y0), np.zeros(shape)

    def same_l_bin(self, kind, i_a, i_b):
        return self.same_bin


def _ub1_bound(tb):
    m = cs_model((UB1_L, (0.5,), (0.9,), (0.0,)))
    return block_gain_bound(m, tb, m.pi, ("M1", "M2"))


def test_ub1_e16_interior_maximum_of_same_bin_interval():
    """T-5 (a): 앵커 평탄, (La, Lb) 안 포물선 x = X0(1 + h·4t(1−t)) -> certified, a_max = db(X0(1 + h)/(2·Y0)), 최대 행 L 값 = 구간 중심."""
    bb = _ub1_bound(_Ub1Tables(_ub1_parabola))
    assert bb.status == "certified"
    assert bb.a_max_db == pytest.approx(db(UB1_X0 * (1.0 + UB1_H) / (2.0 * UB1_Y0)), abs=1e-5)
    assert dict(bb.row_condition)["L:M1"] == pytest.approx(0.5 * (UB1_L[0] + UB1_L[1]), rel=1e-3)


def test_ub1_e16_other_bin_interval_not_looked_at():
    """T-5a (a): same_l_bin 거짓이면 앵커 값 그대로 db(X0/(2·Y0)), lookup_at_l 호출 0."""
    tb = _Ub1Tables(_ub1_parabola, same_bin=False)
    bb = _ub1_bound(tb)
    assert bb.status == "certified"
    assert bb.a_max_db == pytest.approx(db(UB1_X0 / (2.0 * UB1_Y0)), abs=1e-9)
    assert tb.at_l_calls == 0


def test_ub1_e16_nan_interior_is_unknown():
    """T-5b (a): 안쪽 값이 NaN 이면 인증하지 않는다: unknown / bin_interior_unchecked."""
    bb = _ub1_bound(_Ub1Tables(_ub1_parabola, nan=True))
    assert bb.status == "unknown" and bb.reason == "bin_interior_unchecked"


def test_ub1_e16_interior_not_above_ends_keeps_anchor_value():
    """T-5c (a): 안쪽 ≤ 끝이면 a_max = 앵커 값 db(X0/(2·Y0)) 그대로."""
    bb = _ub1_bound(_Ub1Tables(_ub1_dip))
    assert bb.status == "certified"
    assert bb.a_max_db == pytest.approx(db(UB1_X0 / (2.0 * UB1_Y0)), abs=1e-9)


def test_ub1_e16_extremum_near_interval_end():
    """T-5d (a): 극값이 구간 폭 ⅛ 이내(t = 1/16)인 단봉 -> a_max = db(X0(1 + h)/(2·Y0)). 구간을 ¼ 간격으로 표본하는 구현은 끝값(약 +0.14h)에 그쳐 red."""
    bb = _ub1_bound(_Ub1Tables(_ub1_near_end))
    assert bb.status == "certified"
    assert bb.a_max_db == pytest.approx(db(UB1_X0 * (1.0 + UB1_H) / (2.0 * UB1_Y0)), abs=1e-5)
