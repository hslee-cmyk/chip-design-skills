"""`tol_v_table` / `TolVTable` -- CONTRACT 5절 [r2 전면 교체]: 보간 축 VGS·VDS·VS leave-one-out, 모든 L 앵커가 셀을 가짐,
셀별 TolVCell(전역 최댓값으로 줄이지 않음), 두 지표, 축 양끝 격자점 규칙, n_targets = (목표, 축) 역산 시도 수,
at() = L 앵커 이산 키 + VDS 두 칸 최댓값, metric·축 오류.

실데이터 셀 값은 이 파일의 독립 구현(npz 직접, 계약의 LOO 식 lnX_{j−1} + t·(lnX_{j+1} − lnX_{j−1}), 3절 분지 규칙)과 대조한다.
"""
import bisect
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import TOL_V_METRICS, TolVCell, TolVTable, tol_v_table

from .conftest import TOY_L, TOY_VDS, branch_solve_vgs, detail_of, new_memo, rel_close, toy_slice_arrays

GM_INV_TOY = abs(0.5 * 10.0 / (20.0 - math.sqrt(80.0)) - 0.5)          # 0.0477458


def test_contract_toy_cells(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    assert isinstance(t, TolVTable)
    assert (t.kind, t.w_key) == ("nmos", 100)
    assert tuple(t.L_anchors) == TOY_L and tuple(t.vds_grid) == TOY_VDS
    assert len(t.cells) == 3 and all(len(row) == 2 for row in t.cells)
    assert rel_close(GM_INV_TOY, 0.0477458, 1e-5)
    for i in range(3):                       # 모든 L 앵커(양끝 포함)가 셀을 가진다
        for k in range(2):
            c = t.cells[i][k]
            assert isinstance(c, TolVCell)
            assert c.id_equivalent_v is not None and abs(c.id_equivalent_v) < 1e-12
            assert rel_close(c.gm_id_inverse_v, GM_INV_TOY, 1e-9)
            assert (c.n_targets, c.n_inverse_failed) == (2, 0)


def test_contract_toy_at(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    assert abs(t.at(2e-6, 0.75, "id_equivalent")) < 1e-12
    assert rel_close(t.at(2e-6, 0.75, "gm_id_inverse"), GM_INV_TOY, 1e-9)
    # 끝 앵커·VDS 끝점도 정의된 값, 1 ulp 이내 L 은 그 앵커
    assert rel_close(t.at(3e-6, 1.0, "gm_id_inverse"), GM_INV_TOY, 1e-9)
    assert rel_close(t.at(1e-6 + math.ulp(1e-6), 0.5, "gm_id_inverse"), GM_INV_TOY, 1e-9)


def test_at_rejects_non_anchor_l(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    for L in (1.5e-6, 1e-6 + 2 * math.ulp(1e-6)):
        with pytest.raises(SealViolationError) as ei:
            t.at(L, 0.75, "id_equivalent")
        det = detail_of(ei.value)
        assert det["reason"] == "lut_l_not_anchor"
        assert det["value"] == L and det["below"] == 1e-6 and det["above"] == 2e-6
        assert det["table"] == "tol_v" and det["kind"] == "nmos" and det["w_key"] == 100


def test_at_bad_metric_and_axes(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    with pytest.raises(ValueError):
        t.at(2e-6, 0.75, "worst")
    for L, vds, axis in ((0.5e-6, 0.75, "L"), (4e-6, 0.75, "L"), (2e-6, 1.2, "VDS"), (2e-6, 0.4, "VDS"),
                         (float("nan"), 0.75, "L")):
        with pytest.raises(SealViolationError) as ei:
            t.at(L, vds, "id_equivalent")
        det = detail_of(ei.value)
        assert det["reason"] == "lut_axis_out_of_range" and det["table"] == "tol_v" and det["axis"] == axis


def test_no_inner_points_all_none(curve_lut):
    # VGS 2 점, VDS·VS 2 점: 어떤 축에도 내부 격자점이 없다 -> LOO 추정 0 -> 모든 셀 None, 시도 0
    memo, _ = curve_lut((0.0, 1.0), (1e-7, 1e-6), (20.0, 10.0))
    t = tol_v_table(memo, "nmos", 100)
    assert len(t.cells) == 2
    assert all(c == TolVCell(None, None, 0, 0) for row in t.cells for c in row)
    for metric in TOL_V_METRICS:
        assert t.at(1e-6, 0.7, metric) is None


def test_deterministic_and_memo(toy, toy_memo):
    a = tol_v_table(toy_memo, "nmos", 100)
    assert tol_v_table(toy_memo, "nmos", 100) is a
    b = tol_v_table(new_memo(toy), "nmos", 100)
    assert a.cells == b.cells


# ---------------------------------------------------------------------------
# 독립 구현 (CONTRACT 5절 r2)
# ---------------------------------------------------------------------------

def _loo(lo, hi, xs, j):
    t = (xs[j] - xs[j - 1]) / (xs[j + 1] - xs[j - 1])
    return lo + t * (hi - lo)


def independent_cell(z, i, k):
    """셀 (i, k) -> (gm_id_inverse 최댓값|None, id_equivalent 최댓값|None, n_targets, n_inverse_failed)."""
    ID, GM = np.asarray(z["ID"], dtype=float), np.asarray(z["GM"], dtype=float)
    VGS, VDS, VS = (np.asarray(z[a], dtype=float) for a in ("VGS", "VDS", "VS"))
    on = (ID > 0) & (GM > 0)
    fI, fG = float(ID[ID > 0].min()), float(GM[GM > 0].min())
    lI = np.log(np.clip(ID[i], fI, None))          # [VGS, VDS, VS]
    lG = np.log(np.clip(GM[i], fG, None))
    oi = on[i]
    nG, nV, nS = len(VGS), len(VDS), len(VS)
    eq = []
    for g in range(nG):
        for s in range(nS):
            if not oi[g, k, s]:
                continue
            gmid = math.exp(lG[g, k, s] - lI[g, k, s])
            if 0 < g < nG - 1 and oi[g - 1, k, s] and oi[g + 1, k, s]:
                eq.append(abs(_loo(lI[g - 1, k, s], lI[g + 1, k, s], VGS, g) - lI[g, k, s]) / gmid)
            if 0 < k < nV - 1 and oi[g, k - 1, s] and oi[g, k + 1, s]:
                eq.append(abs(_loo(lI[g, k - 1, s], lI[g, k + 1, s], VDS, k) - lI[g, k, s]) / gmid)
            if 0 < s < nS - 1 and oi[g, k, s - 1] and oi[g, k, s + 1]:
                eq.append(abs(_loo(lI[g, k, s - 1], lI[g, k, s + 1], VS, s) - lI[g, k, s]) / gmid)
    inv, n_t, n_f = [], 0, 0
    for s in range(nS):
        if not oi[:, k, s].all():
            continue
        g = np.exp(lG[:, k, s] - lI[:, k, s])
        p = int(np.argmax(g))
        side = []
        if 0 < k < nV - 1 and oi[:, k - 1, s].all() and oi[:, k + 1, s].all():
            side.append(np.exp(_loo(lG[:, k - 1, s], lG[:, k + 1, s], VDS, k)
                               - _loo(lI[:, k - 1, s], lI[:, k + 1, s], VDS, k)))
        if 0 < s < nS - 1 and oi[:, k, s - 1].all() and oi[:, k, s + 1].all():
            side.append(np.exp(_loo(lG[:, k, s - 1], lG[:, k, s + 1], VS, s)
                               - _loo(lI[:, k, s - 1], lI[:, k, s + 1], VS, s)))
        for j in range(p, nG):
            if not all(g[j] > g[r] for r in range(j + 1, nG)):
                continue
            curves = []
            if 0 < j < nG - 1:
                gv = g.copy()
                gv[j] = math.exp(_loo(lG[j - 1, k, s], lG[j + 1, k, s], VGS, j)
                                 - _loo(lI[j - 1, k, s], lI[j + 1, k, s], VGS, j))
                curves.append(gv)
            curves += side
            for c in curves:
                n_t += 1
                root = branch_solve_vgs(c, VGS, float(g[j]))
                if root is None:
                    n_f += 1
                else:
                    inv.append(abs(root - VGS[j]))
    return (max(inv) if inv else None), (max(eq) if eq else None), n_t, n_f


def test_independent_impl_reproduces_toy_row():
    """독립 구현 자체가 계약 7절 toy 값을 내는지(대조 기준 검증)."""
    z = toy_slice_arrays(1e-6)
    for i in range(3):
        for k in range(2):
            inv, eq, n_t, n_f = independent_cell(z, i, k)
            assert rel_close(inv, GM_INV_TOY, 1e-12) and abs(eq) < 1e-12 and (n_t, n_f) == (2, 0)


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
    defined = [c for r in t.cells for c in r if c.gm_id_inverse_v is not None or c.id_equivalent_v is not None]
    assert len(defined) == 576                                   # 계약 실측: 12 앵커 × 48 VDS
    assert all(t.cells[i][0] == TolVCell(None, None, 0, 0) for i in range(nL))   # VDS = 0 열은 ID 0
    assert all(t.cells[i][-1].gm_id_inverse_v is not None for i in range(nL))   # VDS 끝 열도 VGS·VS 방향으로 정의
    eqs = [c.id_equivalent_v for c in defined if c.id_equivalent_v is not None]
    invs = [c.gm_id_inverse_v for c in defined if c.gm_id_inverse_v is not None]
    assert eqs and invs, "두 지표 모두 셀 값이 있어야 한다"
    assert len(set(eqs)) > len(eqs) // 2 and len(set(invs)) > len(invs) // 2     # 셀별 값
    assert max(invs) == pytest.approx(0.445, abs=0.0015)         # 계약 실측 pmos max 445 mV
    assert max(eqs) == pytest.approx(0.201, abs=0.0015)          # 계약 실측 pmos max 201 mV
    assert sum(c.n_inverse_failed for c in defined) == 56389     # 계약 실측 역산 실패 시도
    assert sum(c.n_targets for c in defined) == 733056


@pytest.mark.lut_realdata
@pytest.mark.parametrize("i,k", [(0, 8), (11, 30), (1, 48), (4, 14), (6, 24), (7, 24), (8, 1), (10, 40), (5, 0)])
def test_real_cells_match_independent(real_table, raw_slice, i, k):
    z = raw_slice("pmos", 1000)
    inv, eq, n_t, n_f = independent_cell(z, i, k)
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
def test_real_at_is_max_of_two_cells(real_table):
    t = real_table
    La, Va = list(t.L_anchors), list(t.vds_grid)
    for i, vds in ((3, 0.6), (0, 0.01), (11, 1.79), (5, float(Va[20])), (7, 1.8)):
        L = La[i]
        kk = min(bisect.bisect_right(Va, vds) - 1, len(Va) - 2)
        for metric, attr in (("gm_id_inverse", "gm_id_inverse_v"), ("id_equivalent", "id_equivalent_v")):
            vals = [getattr(t.cells[i][b], attr) for b in (kk, kk + 1)]
            vals = [v for v in vals if v is not None]
            exp = max(vals) if vals else None
            assert t.at(L, vds, metric) == exp, (L, vds, metric)
