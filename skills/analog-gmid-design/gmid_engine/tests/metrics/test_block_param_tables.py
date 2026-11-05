"""metrics/block_param_tables.py -- `ParamTables(memo, w_keys, grids)`, `.lookup(kind, i_l, i_d, i_s, i_v) -> (x, y, z)`
(metrics CONTRACT 10.3 '소자 파라미터', 설계 41 4.2 '소자 파라미터는 LUT memo 에서 한 번만 조회').

oracle (a): 해석식 toy LUT(gb4_hand 모듈 문서)라 격자 마디에서 x = gm/ID = f'(VGS), y = gds/ID = LAM, z = gmb/ID = 2A·VS 가 닫힌 식이다.
강반전 분지(정점 마디 이상)만 유효 -- 정점이 격자 안쪽에 있는 toy(f' 가 VGS = 0.5 에서 최대)로 분지 밖 마디가 NaN 임을 본다(lut 3절 분지 규칙).
"""
from __future__ import annotations

import numpy as np
import pytest

from gmid_engine.metrics import ParamTables

from .gb4_hand import (A, GRIDS, L_GRID, LAM, VDS_GRID, VGS_GRID, VS_GRID, W_KEY, branch_start, fp_default, memo_of,
                       write_lut)


# 정점이 안쪽인 gm/ID: f'(g) = 10 + 10g − 10g² (g = 0.5 에서 최대 12.5), f = 10g + 5g² − 10g³/3. VGS 격자 0..1.5 (0.125 간격)
PEAK_VGS = tuple(0.125 * i for i in range(13))
PEAK_GRIDS = (L_GRID, PEAK_VGS, VDS_GRID, VS_GRID)


def f_peak(g):
    return 10.0 * g + 5.0 * g * g - 10.0 * g ** 3 / 3.0


def fp_peak(g):
    return 10.0 + 10.0 * g - 10.0 * g * g


@pytest.fixture(scope="module")
def toy(tmp_path_factory):
    return write_lut(tmp_path_factory.mktemp("pt_toy"))


@pytest.fixture(scope="module")
def peak(tmp_path_factory):
    return write_lut(tmp_path_factory.mktemp("pt_peak"), grids=PEAK_GRIDS, f=f_peak, fp=fp_peak)


def _all_index(grids):
    nl, ng, nd, ns = (len(g) for g in grids)
    il, iv, idd, iss = np.meshgrid(np.arange(nl), np.arange(ng), np.arange(nd), np.arange(ns), indexing="ij")
    return il.ravel(), idd.ravel(), iss.ravel(), iv.ravel()


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_lookup_matches_closed_form_on_every_grid_node(toy, kind):
    t = ParamTables(memo_of(toy), GRIDS, side="upper", z_side="max")
    il, idd, iss, iv = _all_index(GRIDS)
    x, y, z = t.lookup(kind, il, idd, iss, iv)
    vgs = np.asarray(VGS_GRID)[iv]
    vs = np.asarray(VS_GRID)[iss]
    assert np.allclose(x, fp_default(vgs), rtol=1e-9, atol=0)
    assert np.allclose(y, LAM, rtol=1e-9, atol=0)
    assert np.allclose(z, 2.0 * A * vs, rtol=1e-9, atol=1e-12)


def test_nodes_below_gm_id_peak_are_invalid(peak):
    t = ParamTables(memo_of(peak), PEAK_GRIDS, side="upper", z_side="max")
    p = branch_start(fp_peak, PEAK_VGS)
    assert p == 4                                      # 손: f' 최대 g = 0.5 = 격자 index 4
    il, idd, iss, iv = _all_index(PEAK_GRIDS)
    x, y, z = t.lookup("nmos", il, idd, iss, iv)
    below = iv < p
    assert np.isnan(x[below]).all() and np.isnan(y[below]).all() and np.isnan(z[below]).all()
    vgs = np.asarray(PEAK_VGS)[iv[~below]]
    assert np.allclose(x[~below], fp_peak(vgs), rtol=1e-9)
    assert np.allclose(y[~below], LAM, rtol=1e-9)


def test_lookup_shape_follows_index_arrays(toy):
    t = ParamTables(memo_of(toy), GRIDS, side="upper", z_side="max")
    il = np.zeros((2, 3), int)
    x, y, z = t.lookup("nmos", il, il, il + 1, il + 2)
    assert x.shape == y.shape == z.shape == (2, 3)
    assert np.allclose(x, fp_default(VGS_GRID[2]), rtol=1e-9)
    assert np.allclose(z, 2.0 * A * VS_GRID[1], atol=1e-12)


def test_curves_are_built_once_per_entry(toy):
    # 행 memo: 같은 (kind, L, VDS, VS) 항목은 한 번만 만든다; 만든 곡선 수 상한 = kind 마다 |L|·|VDS|·|VS| (계약 10.3, 모듈 문서 `loads`)
    t = ParamTables(memo_of(toy), GRIDS, side="upper", z_side="max")
    il, idd, iss, iv = _all_index(GRIDS)
    t.lookup("nmos", il, idd, iss, iv)
    first = t.loads
    assert 0 < first <= len(L_GRID) * len(VDS_GRID) * len(VS_GRID)
    t.lookup("nmos", il, idd, iss, iv)
    assert t.loads == first
    t.lookup("pmos", il[:5], idd[:5], iss[:5], iv[:5])
    assert first < t.loads <= 2 * len(L_GRID) * len(VDS_GRID) * len(VS_GRID)


# ---- [UB-1 E-16, interface T-5e 실제 표] bin 지도 toy (lut/conftest 머리 표: L 앵커 1 1.5 2 | 3 4 | 7 8 | 9 µm,
# anchor_bin = (0, 0, 0, 1, 1, 3, 3, 4) -- 손으로 정한 표). oracle (d)(c): 같은 bin 이웃 쌍만 참, 앵커 사이 L 조회는 앵커 두 값의 선형 중점.

@pytest.fixture(scope="module")
def bin_env(tmp_path_factory):
    from lut.conftest import TOY_SPEC, BinToy, bin_model_text, new_memo
    lut = BinToy(tmp_path_factory.mktemp("ub1_bin_tables"), bin_model_text()).load(TOY_SPEC)
    memo = new_memo(lut)
    grids = lut.slice_map[("nmos", 100)].grids
    return memo, ParamTables(memo, grids, side="upper", z_side="max"), grids


def test_ub1_same_l_bin_follows_anchor_bin_map(bin_env):
    _memo, t, _grids = bin_env
    bins = (0, 0, 0, 1, 1, 3, 3, 4)
    for a in range(len(bins) - 1):
        assert bool(t.same_l_bin("nmos", a, a + 1)) == (bins[a] == bins[a + 1]), a
    assert [a for a in range(7) if t.same_l_bin("nmos", a, a + 1)] == [0, 1, 3, 5]


def test_ub1_lookup_at_l_between_anchors_in_same_bin(bin_env):
    from gmid_engine.lut import derived
    memo, t, grids = bin_env
    iv = np.arange(len(grids[1]))
    zero = np.zeros_like(iv)
    x, y, z = t.lookup_at_l("nmos", np.full(iv.shape, 1.25e-6), zero, zero, iv)
    row = derived(memo, "param_row", "nmos", 100, 1.25e-6, grids[2][0], grids[3][0])          # 입력(피검 아님)
    vgs, rx, ry, rz = row
    assert np.isfinite(x).any()
    for k in range(len(iv)):
        j = [m for m, v in enumerate(vgs) if v == grids[1][k]]
        if j:
            assert (x[k], y[k], z[k]) == pytest.approx((rx[j[0]], ry[j[0]], rz[j[0]]), rel=1e-9, abs=1e-12)
        else:
            assert np.isnan(x[k])
    a = t.lookup("nmos", np.zeros_like(iv), zero, zero, iv)              # L = 1.0 µm 앵커
    b = t.lookup("nmos", np.ones_like(iv), zero, zero, iv)               # L = 1.5 µm 앵커
    fin = np.isfinite(x)
    assert np.allclose(x[fin], 0.5 * (a[0][fin] + b[0][fin]), rtol=1e-9)
    at = t.lookup_at_l("nmos", np.full(iv.shape, grids[0][1]), zero, zero, iv)               # 앵커 L 이면 lookup 과 같다
    assert np.allclose(at[0], b[0], rtol=1e-12, equal_nan=True) and np.allclose(at[1], b[1], rtol=1e-12, equal_nan=True)


def test_ub1_lookup_at_l_across_bins_is_nan(bin_env):
    _memo, t, grids = bin_env
    iv = np.arange(len(grids[1]))
    zero = np.zeros_like(iv)
    for v in t.lookup_at_l("nmos", np.full(iv.shape, 2.5e-6), zero, zero, iv):                # 앵커 2 µm(bin A)과 3 µm(bin B) 사이
        assert np.isnan(v).all()


def test_ub1_map_less_table_has_no_same_bin_neighbours(toy):
    t = ParamTables(memo_of(toy), GRIDS, side="upper", z_side="max")
    assert [t.same_l_bin("nmos", a, a + 1) for a in range(len(L_GRID) - 1)] == [False] * (len(L_GRID) - 1)
