"""`tol_v_table` / `TolVTable` -- CONTRACT 5절: 셀별 TolVCell(전역 최댓값으로 줄이지 않음), 두 지표 모두, 양끝 앵커 None,
LOO(이웃 두 L 앵커) 곡선, 분지 목표, at() 의 네 셀 최댓값 규칙, metric·축 오류.

실데이터 셀 값은 이 파일의 독립 구현(npz 직접, 2점 L 선형 LOO, 3절 분지 규칙)과 대조한다.
"""
import bisect
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import TOL_V_METRICS, TolVCell, TolVTable, tol_v_table

from .conftest import TOY_L, TOY_VDS, branch_solve_vgs, detail_of, new_memo, rel_close

ID_EQ_TOY = math.log(2 / math.sqrt(3)) / 4


def test_contract_toy_cells(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    assert isinstance(t, TolVTable)
    assert (t.kind, t.w_key) == ("nmos", 100)
    assert tuple(t.L_anchors) == TOY_L and tuple(t.vds_grid) == TOY_VDS
    assert len(t.cells) == 3 and all(len(row) == 2 for row in t.cells)
    for k in range(2):
        c = t.cells[1][k]
        assert isinstance(c, TolVCell)
        assert rel_close(c.id_equivalent_v, ID_EQ_TOY, 1e-9)
        assert rel_close(c.id_equivalent_v, 0.0359603, 1e-5)
        assert c.n_targets == 6
        # 정점 목표(g = 20)는 반올림에 따라 해 없음으로 셀 수 있다(계약: 현 구현 1) -- VS 2 개라 정점 목표는 2 개
        assert 0 <= c.n_inverse_failed <= 2
        assert c.gm_id_inverse_v is not None and c.gm_id_inverse_v < 1e-9
        assert t.cells[0][k] == TolVCell(None, None, 0, 0)
        assert t.cells[2][k] == TolVCell(None, None, 0, 0)


def test_contract_toy_at(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    assert rel_close(t.at(1.5e-6, 0.75, "id_equivalent"), ID_EQ_TOY, 1e-9)
    # 오른쪽 끝 칸(L 2.5e-6): 앵커 1·2 -> 앵커 1 값만 남는다
    assert rel_close(t.at(2.5e-6, 1.0, "id_equivalent"), ID_EQ_TOY, 1e-9)
    assert t.at(3e-6, 0.5, "gm_id_inverse") < 1e-9


def test_at_bad_metric_and_axes(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    with pytest.raises(ValueError):
        t.at(1.5e-6, 0.75, "worst")
    for L, vds, axis in ((0.5e-6, 0.75, "L"), (1.5e-6, 1.2, "VDS"), (float("nan"), 0.75, "L")):
        with pytest.raises(SealViolationError) as ei:
            t.at(L, vds, "id_equivalent")
        det = detail_of(ei.value)
        assert det["reason"] == "lut_axis_out_of_range" and det["table"] == "tol_v" and det["axis"] == axis


def test_all_none_at_returns_none(toy_build):
    # L 앵커 2 개뿐이면 내부 앵커가 없다 -> 모든 셀 None, at() 도 None
    from .conftest import curve_slice_arrays, curve_cap_arrays
    vgs = (0.0, 0.5, 1.0)
    a = curve_slice_arrays(1e-6, vgs, (1e-7, 1e-6, 1e-5), (20.0, 10.0, 4.0))
    m = new_memo(toy_build("two", slices=[("c.npz", "toyn", a)], cap=curve_cap_arrays(vgs)).load())
    t = tol_v_table(m, "nmos", 100)
    assert all(c == TolVCell(None, None, 0, 0) for row in t.cells for c in row)
    for metric in TOL_V_METRICS:
        assert t.at(1.5e-6, 0.7, metric) is None


def test_deterministic_and_memo(toy, toy_memo):
    a = tol_v_table(toy_memo, "nmos", 100)
    assert tol_v_table(toy_memo, "nmos", 100) is a
    b = tol_v_table(new_memo(toy), "nmos", 100)
    assert a.cells == b.cells


# ---------------------------------------------------------------------------
# 실데이터: 독립 구현과 셀 대조
# ---------------------------------------------------------------------------

def _independent_cell(z, i, k):
    """CONTRACT 5절 셀 (i, k) 를 npz 에서 직접. 반환 (gm_id_inverse 최댓값|None, id_equivalent 최댓값|None, n_targets, n_failed)."""
    L = z["L"]
    VGS = z["VGS"]
    ID, GM = z["ID"], z["GM"]
    fI = float(ID[ID > 0].min())
    fG = float(GM[GM > 0].min())
    f = (L[i] - L[i - 1]) / (L[i + 1] - L[i - 1])
    inv, eq, n_t, n_f = [], [], 0, 0
    for s in range(ID.shape[3]):
        cols = [(ID[j, :, k, s], GM[j, :, k, s]) for j in (i - 1, i, i + 1)]
        if not all(np.all(a > 0) and np.all(b > 0) for a, b in cols):
            continue
        lI = [np.log(np.clip(a, fI, None)) for a, _ in cols]
        lG = [np.log(np.clip(b, fG, None)) for _, b in cols]
        lI_loo = (1 - f) * lI[0] + f * lI[2]
        lG_loo = (1 - f) * lG[0] + f * lG[2]
        g = np.exp(lG[1] - lI[1])
        g_loo = np.exp(lG_loo - lI_loo)
        p = int(np.argmax(g))
        for j in range(p, len(g)):
            if not all(g[j] > g[r] for r in range(j + 1, len(g))):
                continue
            n_t += 1
            eq.append(abs(lI_loo[j] - lI[1][j]) / g[j])
            root = branch_solve_vgs(g_loo, VGS, float(g[j]))
            if root is None:
                n_f += 1
            else:
                inv.append(abs(root - VGS[j]))
    return (max(inv) if inv else None), (max(eq) if eq else None), n_t, n_f


@pytest.fixture(scope="module")
def real_table(real_lut):
    return tol_v_table(new_memo(real_lut), "pmos", 1000)


@pytest.mark.lut_realdata
def test_real_table_shape_and_per_cell(real_table, raw_slice):
    z = raw_slice("pmos", 1000)
    t = real_table
    nL, nV = len(z["L"]), len(z["VDS"])
    assert tuple(t.L_anchors) == tuple(float(x) for x in z["L"])
    assert tuple(t.vds_grid) == tuple(float(x) for x in z["VDS"])
    assert len(t.cells) == nL and all(len(r) == nV for r in t.cells)
    assert all(isinstance(c, TolVCell) for r in t.cells for c in r)
    for k in range(nV):
        assert t.cells[0][k] == TolVCell(None, None, 0, 0)
        assert t.cells[-1][k] == TolVCell(None, None, 0, 0)
    inner = [c for r in t.cells[1:-1] for c in r]
    eqs = [c.id_equivalent_v for c in inner if c.id_equivalent_v is not None]
    invs = [c.gm_id_inverse_v for c in inner if c.gm_id_inverse_v is not None]
    assert eqs and invs, "두 지표 모두 셀 값이 있어야 한다"
    # 셀별 값: 하나의 전역 최댓값으로 줄어 있지 않다
    assert len(set(eqs)) > len(eqs) // 2 and len(set(invs)) > len(invs) // 2
    assert sum(1 for v in eqs if v < max(eqs)) >= len(eqs) - 1


@pytest.mark.lut_realdata
@pytest.mark.parametrize("i,k", [(1, 8), (4, 14), (6, 24), (7, 24), (8, 14), (10, 40), (5, 2)])
def test_real_cells_match_independent(real_table, raw_slice, i, k):
    z = raw_slice("pmos", 1000)
    inv, eq, n_t, n_f = _independent_cell(z, i, k)
    c = real_table.cells[i][k]
    assert (c.n_targets, c.n_inverse_failed) == (n_t, n_f), (i, k)
    if eq is None:
        assert c.id_equivalent_v is None
    else:
        assert rel_close(c.id_equivalent_v, eq, 1e-9)
    if inv is None:
        assert c.gm_id_inverse_v is None
    else:
        assert abs(c.gm_id_inverse_v - inv) <= 1e-9 * max(1.0, inv)


@pytest.mark.lut_realdata
def test_real_at_is_max_of_four_cells(real_table):
    t = real_table
    La, Va = list(t.L_anchors), list(t.vds_grid)
    for L, vds in ((1.2e-6, 0.6), (0.16e-6, 0.01), (3.9e-6, 1.79), (float(La[5]), float(Va[20]))):
        j = min(bisect.bisect_right(La, L) - 1, len(La) - 2)
        kk = min(bisect.bisect_right(Va, vds) - 1, len(Va) - 2)
        for metric, attr in (("gm_id_inverse", "gm_id_inverse_v"), ("id_equivalent", "id_equivalent_v")):
            vals = [getattr(t.cells[a][b], attr) for a in (j, j + 1) for b in (kk, kk + 1)]
            vals = [v for v in vals if v is not None]
            exp = max(vals) if vals else None
            assert t.at(L, vds, metric) == exp, (L, vds, metric)
