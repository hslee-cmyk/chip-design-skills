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
