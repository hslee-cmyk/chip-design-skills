"""metrics/block_gain_rows.py -- `row_gains(model, tables, idx, cont=None) -> ndarray (B,)` (metrics CONTRACT 10.3, 설계 41 4.2 '행마다 블록 국소 모델을 풀어 gain').

oracle (a)·(b): 손 `BlockModel` + 해석식 toy LUT(x = 20 − 8·VGS, y = 0.1, z = 4·VS -- gb4_hand) 위에서
- CS(전류원 부하) gain = gm1/(gds1 + gds2) = x1/(y1 + y2)  (손 계산, 같은 전류라 I 가 약분)
- 소스 팔로워(이상 전류원 부하) gain = gm/(gm + gds + gmb) = x/(x + y + z)
- 5T OTA(3 미지 노드 tail·x·out, 차동 ±½ 여기) gain = 이 test 의 독립 KCL 풀이(`solve_lin`, numpy) -- 피검 MNA 와 별개 구현
- CS + 저항 부하 gain = x·I/(y·I + G)
행 = 축 index 조합(B, 축 수). 유효하지 않은 행(전류 ≤ 0, 특이 행렬)은 NaN.
"""
from __future__ import annotations

import numpy as np
import pytest

from gmid_engine.metrics import ParamTables, row_gains

from .gb4_hand import (GRIDS, L_GRID, LAM, VDS_GRID, VGS_GRID, VS_GRID, W_KEY, axis, cs_model, follower_model, memo_of, model,
                       mosl, solve_lin, write_lut)

G = np.asarray(VGS_GRID)
S = np.asarray(VS_GRID)


@pytest.fixture(scope="module")
def tables(tmp_path_factory):
    return ParamTables(memo_of(write_lut(tmp_path_factory.mktemp("rows_toy"))), GRIDS, side="upper", z_side="max")


def _rand_rows(m, n, seed):
    rnd = np.random.default_rng(seed)
    return np.stack([rnd.integers(0, a.size, n) for a in m.axes], axis=1)


def test_cs_gain_is_gm_over_gds_sum(tables):
    m = cs_model()
    idx = _rand_rows(m, 40, 1)
    g = row_gains(m, tables, idx)
    x1 = 20.0 - 8.0 * G[idx[:, 0]]
    assert g.shape == (40,)
    assert np.allclose(g, x1 / (LAM + LAM), rtol=1e-9)


def test_follower_gain_is_gm_over_total_source_conductance(tables):
    m = follower_model()
    idx = _rand_rows(m, 60, 2)
    g = row_gains(m, tables, idx)
    x = 20.0 - 8.0 * G[idx[:, 0]]
    z = 4.0 * S[idx[:, 3]]
    assert np.allclose(g, np.abs(x / (x + LAM + z)), rtol=1e-9)


def _ota_model():
    """5T OTA: M1 nmos (x, inp, tail), M2 nmos (out, inn, tail), M3 pmos diode (x, x, vdd), M4 pmos (out, x, vdd).
    꼬리 = 이상 전류원(컨덕턴스 0) -> tail 은 미지 노드. 각 가지 전류 = 공통 배율의 ½. 축(소자마다): vgs, L, vds(+ M1·M2 vsb)."""
    axes = []
    mos = []
    spec = (("M1", "nmos", "x", "inp", "tail", "gnd", True), ("M2", "nmos", "out", "inn", "tail", "gnd", True),
            ("M3", "pmos", "x", "x", "vdd", "vdd", False), ("M4", "pmos", "out", "x", "vdd", "vdd", False))
    for name, kind, d, g, s, b, vsb in spec:
        iv = len(axes)
        axes.append(axis("vgs", (name,), VGS_GRID))
        il = len(axes)
        axes.append(axis("L", (name,), L_GRID))
        idd = len(axes)
        axes.append(axis("vds", (name,), VDS_GRID))
        isb = -1
        if vsb:
            isb = len(axes)
            axes.append(axis("vsb", (name,), VS_GRID))
        mos.append(mosl(name, kind, d, g, s, b, iv, il, idd, isb, current=((-1, 0.5),)))
    m = model(("out",), ("tail", "x", "out"), ("inp", "inn"), ((("inp", 0.5), ("inn", -0.5)),), (("out", 1),), mos, axes,
              normalized=("I0",))
    return m, spec


def test_five_transistor_ota_matches_independent_kcl_solve(tables):
    m, spec = _ota_model()
    idx = _rand_rows(m, 25, 3)
    got = row_gains(m, tables, idx)
    for r in range(idx.shape[0]):
        devs = []
        for k, (name, kind, d, g, s, b, vsb) in enumerate(spec):
            ml = m.mos[k]
            assert ml.name == name
            x = 20.0 - 8.0 * G[idx[r, ml.vgs_axis]]
            z = 4.0 * S[idx[r, ml.vsb_axis]] if ml.vsb_axis >= 0 else 0.0
            i = 0.5
            devs.append((d, g, s, b, x * i, LAM * i, z * i))
        v = solve_lin(("tail", "x", "out"), {"inp": 0.5, "inn": -0.5, "vdd": 0.0, "gnd": 0.0}, devs)
        assert got[r] == pytest.approx(abs(v["out"]), rel=1e-9)


def test_continuous_axis_values_override_with_cont(tables):
    # CS + 저항 부하 R1(out, vdd): 축 0 vgs, 1 L, 2 vds, 3 current(A), 4 resistor(S). gain = x·I/(y·I + G)
    from gmid_engine.metrics import ResLocal
    axes = (axis("vgs", ("M1",), VGS_GRID), axis("L", ("M1",), L_GRID), axis("vds", ("M1",), VDS_GRID),
            axis("current", ("I0",), np.geomspace(1e-6, 1e-4, 5), True), axis("resistor", ("R1",), np.geomspace(1e-5, 1e-3, 5), True))
    m = model(("out",), ("out",), ("in",), ((("in", 1.0),),), (("out", 1),),
              (mosl("M1", "nmos", "out", "in", "gnd", "gnd", 0, 1, 2, -1, current=((3, 1.0),)),), axes,
              res=(ResLocal("R1", "out", "vdd", 4, None),))
    idx = np.array([[0, 0, 3, 0, 0], [5, 1, 6, 4, 4], [18, 0, 0, 2, 1]])
    g = row_gains(m, tables, idx)
    i = np.geomspace(1e-6, 1e-4, 5)[idx[:, 3]]
    gg = np.geomspace(1e-5, 1e-3, 5)[idx[:, 4]]
    x = 20.0 - 8.0 * G[idx[:, 0]]
    assert np.allclose(g, x * i / (LAM * i + gg), rtol=1e-9)
    cont = {3: np.array([2e-5, 3e-6, 7e-5]), 4: np.array([4e-4, 2e-5, 1e-3])}
    g2 = row_gains(m, tables, idx, cont)
    assert np.allclose(g2, x * cont[3] / (LAM * cont[3] + cont[4]), rtol=1e-9)
    # 고정 저항(axis −1): g_fixed 그대로
    m_fixed = model(("out",), ("out",), ("in",), ((("in", 1.0),),), (("out", 1),),
                    (mosl("M1", "nmos", "out", "in", "gnd", "gnd", 0, 1, 2, -1, current=((3, 1.0),)),), axes[:4],
                    res=(ResLocal("R1", "out", "vdd", -1, 1e-4),))
    g3 = row_gains(m_fixed, tables, idx[:, :4])
    assert np.allclose(g3, x * i / (LAM * i + 1e-4), rtol=1e-9)


def test_nonpositive_current_row_is_nan(tables):
    m = cs_model()
    bad = model(m.key, m.nodes, m.driven, m.patterns, m.outputs,
                tuple(mosl(x.name, x.kind, x.d, x.g, x.s, x.bulk, x.vgs_axis, x.l_axis, x.vds_axis, x.vsb_axis,
                           current=((-1, -1.0),)) for x in m.mos), m.axes, normalized=m.normalized)
    g = row_gains(bad, tables, np.zeros((3, len(m.axes)), int))
    assert np.isnan(g).all()


def test_singular_row_is_nan(tables):
    # 미지 노드 'fl' 에 아무 소자도 닿지 않는다 -> 특이 행렬 -> NaN
    m = cs_model()
    sing = model(m.key, ("out", "fl"), m.driven, m.patterns, m.outputs, m.mos, m.axes, normalized=m.normalized)
    g = row_gains(sing, tables, np.zeros((2, len(m.axes)), int))
    assert np.isnan(g).all()


def test_no_unknown_nodes_gives_weighted_drive_sum(tables):
    # 미지수가 없으면 출력 = 구동 넷의 가중 합; 두 패턴 중 큰 쪽(차동 출력 +a −b): (+½, −½) -> 1, (+½, +½) -> 0
    m = model(("a", "b"), (), ("a", "b"), ((("a", 0.5), ("b", -0.5)), (("a", 0.5), ("b", 0.5))), (("a", 1), ("b", -1)), (), ())
    g = row_gains(m, tables, np.zeros((1, 0), int))
    assert g[0] == pytest.approx(1.0, abs=1e-15)


def test_deterministic(tables):
    m = follower_model()
    idx = _rand_rows(m, 30, 4)
    assert np.array_equal(row_gains(m, tables, idx), row_gains(m, tables, idx), equal_nan=True)
