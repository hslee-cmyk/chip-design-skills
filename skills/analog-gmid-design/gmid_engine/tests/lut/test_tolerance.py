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
from gmid_engine.lut import TOL_V_METRICS, LBinMap, TolVCell, TolVTable, tol_v_table

from .conftest import (BIN_ANCHOR_BIN_HI, BIN_ANCHOR_BIN_LO, BIN_L, TOY_L, TOY_VDS, bin_toy_raw, branch_solve_vgs,
                       detail_of, new_memo, parse_model_bins, rel_close, same_bounds, toy_slice_arrays, um)

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


def l_loo_rows(anchor_bin):
    """[r4] L 방향 LOO 를 만드는 앵커 i 집합(5절 'L 축 규칙'): 0 < i < n−1 이고 앵커 i−1·i·i+1 의 bin 이 같다.
    anchor_bin 은 test 쪽에서 독립으로 정한 앵커별 bin 표시(ngspice showmod 또는 toy 모델 파일 손계산)."""
    if not anchor_bin:
        return frozenset()
    n = len(anchor_bin)
    return frozenset(i for i in range(1, n - 1) if anchor_bin[i - 1] == anchor_bin[i] == anchor_bin[i + 1])


def independent_cell(z, i, k, l_rows=frozenset()):
    """셀 (i, k) -> (gm_id_inverse 최댓값|None, id_equivalent 최댓값|None, n_targets, n_inverse_failed).

    l_rows: [r4] L 방향 LOO 를 넣을 앵커 집합(`l_loo_rows`). 비어 있으면 r2 정의(VGS·VDS·VS 축만)."""
    ID, GM = np.asarray(z["ID"], dtype=float), np.asarray(z["GM"], dtype=float)
    Lg = np.asarray(z["L"], dtype=float)
    VGS, VDS, VS = (np.asarray(z[a], dtype=float) for a in ("VGS", "VDS", "VS"))
    on = (ID > 0) & (GM > 0)
    fI, fG = float(ID[ID > 0].min()), float(GM[GM > 0].min())
    lI = np.log(np.clip(ID[i], fI, None))          # [VGS, VDS, VS]
    lG = np.log(np.clip(GM[i], fG, None))
    oi = on[i]
    use_l = i in l_rows
    if use_l:
        lIm, lIp = np.log(np.clip(ID[i - 1], fI, None)), np.log(np.clip(ID[i + 1], fI, None))
        lGm, lGp = np.log(np.clip(GM[i - 1], fG, None)), np.log(np.clip(GM[i + 1], fG, None))
        om, op_ = on[i - 1], on[i + 1]
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
            if use_l and om[g, k, s] and op_[g, k, s]:
                eq.append(abs(_loo(lIm[g, k, s], lIp[g, k, s], Lg, i) - lI[g, k, s]) / gmid)
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
        if use_l and om[:, k, s].all() and op_[:, k, s].all():
            side.append(np.exp(_loo(lGm[:, k, s], lGp[:, k, s], Lg, i)
                               - _loo(lIm[:, k, s], lIp[:, k, s], Lg, i)))
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
    # [r4, test author 복원 2026-10-07] 등호 강도 복원. 기대값 = 이 파일의 독립 구현(`independent_cell` + `l_loo_rows`,
    # L 방향 LOO 앵커 = ngspice showmod 로 정한 bin 에서 앵커 4·5(0.35·0.425 µm))을 pmos w_key 1000 의 576 셀 전부에 돌린 값.
    # (r2 값 445 mV·201 mV·56,389·733,056 은 L 방향 LOO 가 없던 정의 -- r4 에서 0.35 µm 행 492 mV 가 최댓값이 된다.)
    # 셀 단위 등호 대조는 test_real_cells_match_independent·test_real_l_rows_cells_match_independent.
    assert abs(max(invs) - 0.49207258763504047) <= 1e-9          # 독립 구현 pmos max(앵커 0.35 µm 행)
    assert abs(max(eqs) - 0.20112031777415645) <= 1e-9           # 독립 구현 pmos max
    assert sum(c.n_inverse_failed for c in defined) == 65335     # 독립 구현 역산 실패 시도
    assert sum(c.n_targets for c in defined) == 779455           # 독립 구현 역산 시도


@pytest.fixture(scope="module")
def real_pmos_l_rows(real_lut, ngspice_bins):
    """pmos w_key 1000 의 L 방향 LOO 앵커 -- 앵커별 bin 을 ngspice showmod 로 정해 독립으로 고른다(엔진 지도 미사용)."""
    sl = real_lut.slice_map[("pmos", 1000)]
    b = ngspice_bins.query("pfet_01v8", [(um(sl.w_m), um(L)) for L in sl.grids[0]])
    uniq = sorted(set(b))
    return l_loo_rows(tuple(uniq.index(x) for x in b))


@pytest.mark.lut_realdata
def test_real_l_rows_are_contract_anchors(real_pmos_l_rows):
    assert real_pmos_l_rows == frozenset({4, 5})                 # 0.35·0.425 µm (CONTRACT 5절 r4 실측)


@pytest.mark.lut_realdata
@pytest.mark.parametrize("i,k", [(0, 8), (11, 30), (1, 48), (4, 14), (6, 24), (7, 24), (8, 1), (10, 40), (5, 0),
                                 (4, 30), (5, 24), (5, 48), (3, 20), (6, 40)])
def test_real_cells_match_independent(real_table, raw_slice, real_pmos_l_rows, i, k):
    # [r4, test author 복원] bin 안 내부 앵커(4·5) 셀도 등호 대조: 독립 구현에 L 방향 LOO(5절 'L 축 규칙')를 넣었다.
    z = raw_slice("pmos", 1000)
    inv, eq, n_t, n_f = independent_cell(z, i, k, real_pmos_l_rows)
    c = real_table.cells[i][k]
    assert (real_table.l_loo[i] == "in_bin_interior") == (i in real_pmos_l_rows)
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


# ---------------------------------------------------------------------------
# [r4] 같은 bin 안 L 방향 LOO (5절 'L 축 규칙'), 상태, 외부 l_bin_checks, at() 의 L 위치(4.0)
# ---------------------------------------------------------------------------

def _independent_table(z, l_rows):
    nL, nV = len(z["L"]), len(z["VDS"])
    return [[independent_cell(z, i, k, l_rows) for k in range(nV)] for i in range(nL)]


def _assert_cells_equal(t, exp):
    for i, row in enumerate(exp):
        for k, (inv, eq, n_t, n_f) in enumerate(row):
            c = t.cells[i][k]
            assert (c.n_targets, c.n_inverse_failed) == (n_t, n_f), (i, k)
            for got, want in ((c.gm_id_inverse_v, inv), (c.id_equivalent_v, eq)):
                if want is None:
                    assert got is None, (i, k)
                else:
                    assert abs(got - want) <= 1e-12 * max(1.0, abs(want)), (i, k, got, want)


BIN_TOY_L_LOO_LO = ("bin_edge", "in_bin_interior", "bin_edge", "bin_missing_external", "bin_missing_external",
                    "bin_missing_external", "bin_missing_external", "bin_single_point")
BIN_TOY_L_LOO_BINS_LO = (("toyn__model.0", (0, 1, 2), "computed"), ("toyn__model.1", (3, 4), "missing_external"),
                         ("toyn__model.3", (5, 6), "missing_external"), ("toyn__model.4", (7,), "single_point"))


def test_bin_toy_cells_match_independent(bin_toy, bin_memo):
    t = tol_v_table(bin_memo, "nmos", 100)
    assert l_loo_rows(BIN_ANCHOR_BIN_LO) == frozenset({1})
    _assert_cells_equal(t, _independent_table(bin_toy_raw(), l_loo_rows(BIN_ANCHOR_BIN_LO)))
    # 손계산: 앵커 1.5 µm 행만 L 방향 몫. lnID 의 L 방향 LOO 오차 = |½(ln 1 + ln ½) − ln(1/1.5)|, gm/ID 최소 = 4·(1 + 0.15)
    hand = abs(0.5 * math.log(0.5) + math.log(1.5)) / (4.0 * 1.15)
    for k in range(2):
        assert rel_close(t.cells[1][k].id_equivalent_v, hand, 1e-12)
        assert t.cells[1][k].n_targets == 8                 # VS 2 × (VGS 축 목표 1 + L 축 목표 3)
        for i in (0, 2, 3, 7):
            assert abs(t.cells[i][k].id_equivalent_v) < 1e-12 and t.cells[i][k].n_targets == 2
    assert t.l_bins == bin_toy.slice_map[("nmos", 100)].l_bins
    assert tuple(t.l_loo) == BIN_TOY_L_LOO_LO
    assert tuple(t.l_loo_bins) == BIN_TOY_L_LOO_BINS_LO


def test_bin_toy_upper_width_rows(bin_toy, bin_memo):
    """폭 2e-6 슬라이스(위 W 범위: A' [1, 4]·D' (4, 10]): L 방향 LOO 앵커 = 1·2·3·6."""
    t = tol_v_table(bin_memo, "nmos", 200)
    rows = l_loo_rows(BIN_ANCHOR_BIN_HI)
    assert rows == frozenset({1, 2, 3, 6})
    _assert_cells_equal(t, _independent_table(bin_toy_raw(2.0, 2e-6), rows))
    assert tuple(t.l_loo) == ("bin_edge", "in_bin_interior", "in_bin_interior", "in_bin_interior", "bin_edge",
                              "bin_edge", "in_bin_interior", "bin_edge")
    assert tuple(t.l_loo_bins) == (("toyn__model.5", (0, 1, 2, 3, 4), "computed"),
                                   ("toyn__model.6", (5, 6, 7), "computed"))


def test_empty_map_statuses(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    assert tuple(t.l_loo) == ("bins_unavailable",) * 3
    assert tuple(t.l_loo_bins) == ()
    assert t.l_bins == LBinMap((), None, (), ())


def test_external_checks_maxed_into_two_anchor_bins(bin_memo):
    base = tol_v_table(bin_memo, "nmos", 100)
    checks = (("toyn__model.1", 0.5, None), ("toyn__model.3", None, 0.25))
    t = tol_v_table(bin_memo, "nmos", 100, checks)
    assert t is not base
    for i in range(len(BIN_L)):
        for k in range(2):
            b, c = base.cells[i][k], t.cells[i][k]
            assert (c.n_targets, c.n_inverse_failed) == (b.n_targets, b.n_inverse_failed)
            inv, eq = b.gm_id_inverse_v, b.id_equivalent_v
            if i in (3, 4) and inv is not None:
                inv = max(inv, 0.5)
            if i in (5, 6) and eq is not None:
                eq = max(eq, 0.25)
            assert (c.gm_id_inverse_v, c.id_equivalent_v) == (inv, eq), (i, k)
    assert t.cells[3][0].gm_id_inverse_v == 0.5 and t.cells[5][1].id_equivalent_v == 0.25   # 실제로 올라갔다
    assert tuple(t.l_loo) == BIN_TOY_L_LOO_LO[:3] + ("bin_external",) * 4 + ("bin_single_point",)
    assert tuple(t.l_loo_bins) == (BIN_TOY_L_LOO_BINS_LO[0], ("toyn__model.1", (3, 4), "external"),
                                   ("toyn__model.3", (5, 6), "external"), BIN_TOY_L_LOO_BINS_LO[3])
    # 한 bin 만 주면 나머지는 missing_external
    t1 = tol_v_table(bin_memo, "nmos", 100, (("toyn__model.3", 0.1, 0.1),))
    assert tuple(t1.l_loo)[3:7] == ("bin_missing_external",) * 2 + ("bin_external",) * 2


def test_external_checks_none_cells_stay_none(bin_toy_build):
    """셀 값이 None 이면 외부 값이 있어도 None. VGS 2 점(내부점 없음)·VDS·VS 2 점, L 앵커 1·2 µm 가 한 bin(앵커 2개):
    어떤 축에도 LOO 가 없어 모든 셀 None -> 외부 값을 줘도 None, 시도 수 0."""
    bt = bin_toy_build(blocks=(("toyn__model.0", 1e-6, 2e-6, 0.5e-6, 3e-6),), L=(1e-6, 2e-6), n_vgs=2)
    m = new_memo(bt.load())
    base = tol_v_table(m, "nmos", 100)
    assert tuple(base.l_loo) == ("bin_missing_external",) * 2
    t = tol_v_table(m, "nmos", 100, (("toyn__model.0", 0.7, 0.7),))
    assert tuple(t.l_loo) == ("bin_external",) * 2
    assert tuple(t.l_loo_bins) == (("toyn__model.0", (0, 1), "external"),)
    assert all(c == TolVCell(None, None, 0, 0) for row in t.cells for c in row)


def test_external_checks_memo_normalized(bin_memo):
    a = tol_v_table(bin_memo, "nmos", 100, (("toyn__model.1", 0.5, None), ("toyn__model.3", None, 0.25)))
    b = tol_v_table(bin_memo, "nmos", 100, (("toyn__model.3", None, 0.25), ("toyn__model.1", 0.5, None)))
    assert a is b
    c = tol_v_table(bin_memo, "nmos", 100, (("toyn__model.1", 0.5, None), ("toyn__model.3", None, 0.26)))
    assert c is not a


@pytest.mark.parametrize("checks", [
    (("toyn__model.1", 0.1, 0.1), ("toyn__model.1", 0.2, 0.2)),     # 같은 model 두 번
    (("toyn__model.0", 0.1, 0.1),),                                  # 앵커 3개 bin
    (("toyn__model.4", 0.1, 0.1),),                                  # 앵커 1개 bin
    (("toyn__model.2", 0.1, 0.1),),                                  # 앵커 0개 bin
    (("no_such_model", 0.1, 0.1),),                                  # 지도에 없는 이름
])
def test_external_checks_invalid(bin_memo, checks):
    with pytest.raises(ValueError):
        tol_v_table(bin_memo, "nmos", 100, checks)


def test_external_checks_on_empty_map_invalid(toy_memo):
    with pytest.raises(ValueError):
        tol_v_table(toy_memo, "nmos", 100, (("anything", 0.1, 0.1),))
    assert tol_v_table(toy_memo, "nmos", 100, ()) is tol_v_table(toy_memo, "nmos", 100)


@pytest.mark.parametrize("L,rows", [(1.25e-6, (0, 1)), (1.75e-6, (1, 2)), (3.5e-6, (3, 4)), (7.5e-6, (5, 6))])
def test_at_in_bin_uses_both_rows(bin_memo, L, rows):
    t = tol_v_table(bin_memo, "nmos", 100)
    for vds in (0.5, 0.75, 1.0):
        for metric, attr in (("gm_id_inverse", "gm_id_inverse_v"), ("id_equivalent", "id_equivalent_v")):
            vals = [getattr(t.cells[i][k], attr) for i in rows for k in (0, 1)]
            vals = [v for v in vals if v is not None]
            assert t.at(L, vds, metric) == (max(vals) if vals else None), (L, vds, metric)


@pytest.mark.parametrize("L,reason", [(2.5e-6, "lut_l_cross_bin"), (6.5e-6, "lut_l_cross_bin"),
                                      (4.5e-6, "lut_l_bin_unbracketed"), (8.5e-6, "lut_l_bin_unbracketed"),
                                      (5.5e-6, "lut_l_outside_model_bins")])
def test_at_rejects_across_bins(bin_memo, L, reason):
    t = tol_v_table(bin_memo, "nmos", 100)
    with pytest.raises(SealViolationError) as ei:
        t.at(L, 0.75, "gm_id_inverse")
    det = detail_of(ei.value)
    assert det["reason"] == reason and det["value"] == L
    assert det["table"] == "tol_v" and det["kind"] == "nmos" and det["w_key"] == 100


def test_at_empty_map_detail(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    with pytest.raises(SealViolationError) as ei:
        t.at(1.5e-6, 0.75, "gm_id_inverse")
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_not_anchor" and det["bins"] == "unavailable"


@pytest.mark.lut_realdata
@pytest.mark.parametrize("k", range(49))
def test_real_l_rows_cells_match_independent(real_table, raw_slice, real_pmos_l_rows, k):
    """L 방향 LOO 가 들어가는 두 행(0.35·0.425 µm)의 모든 VDS 셀 -- 독립 구현과 등호."""
    z = raw_slice("pmos", 1000)
    for i in sorted(real_pmos_l_rows):
        inv, eq, n_t, n_f = independent_cell(z, i, k, real_pmos_l_rows)
        c = real_table.cells[i][k]
        assert (c.n_targets, c.n_inverse_failed) == (n_t, n_f), (i, k)
        assert (c.id_equivalent_v is None) == (eq is None) and (c.gm_id_inverse_v is None) == (inv is None)
        if eq is not None:
            assert rel_close(c.id_equivalent_v, eq, 1e-9)
        if inv is not None:
            assert abs(c.gm_id_inverse_v - inv) <= 1e-9 * max(1.0, inv)


@pytest.mark.lut_realdata
def test_real_statuses_match_ngspice_bins(real_table, real_lut, ngspice_bins):
    """앵커·bin 상태: 앵커 bin 을 showmod 로 묶어 앵커 수로 정한다(3개 이상 computed, 2개 missing_external, 1개 single_point)."""
    sl = real_lut.slice_map[("pmos", 1000)]
    b = ngspice_bins.query("pfet_01v8", [(um(sl.w_m), um(L)) for L in sl.grids[0]])
    names = parse_model_bins(ngspice_bins.pm3("pfet_01v8"))
    groups = []
    for i, g in enumerate(b):
        if groups and same_bounds(groups[-1][0], g):
            groups[-1][1].append(i)
        else:
            groups.append((g, [i]))
    exp_bins, exp_loo = [], [None] * len(b)
    for g, idx in groups:
        name = [n for n, bnd in names.items() if same_bounds(bnd, g)]
        assert len(name) == 1
        st = "computed" if len(idx) >= 3 else ("missing_external" if len(idx) == 2 else "single_point")
        exp_bins.append((name[0], tuple(idx), st))
        for j, i in enumerate(idx):
            exp_loo[i] = ({"missing_external": "bin_missing_external", "single_point": "bin_single_point"}.get(st)
                          or ("bin_edge" if j in (0, len(idx) - 1) else "in_bin_interior"))
    assert tuple(real_table.l_loo_bins) == tuple(exp_bins)
    assert tuple(real_table.l_loo) == tuple(exp_loo)


@pytest.mark.lut_realdata
def test_real_at_in_bin_and_cross_bin(real_table):
    t = real_table
    La = list(t.L_anchors)
    L = 0.5 * (La[4] + La[5])                           # 0.3875 µm, 같은 bin 0.35·0.425
    for metric, attr in (("gm_id_inverse", "gm_id_inverse_v"), ("id_equivalent", "id_equivalent_v")):
        vals = [getattr(t.cells[i][k], attr) for i in (4, 5) for k in (24, 25)]
        vals = [v for v in vals if v is not None]
        assert t.at(L, 0.9, metric) == max(vals)
    with pytest.raises(SealViolationError) as ei:
        t.at(0.6e-6, 0.9, "gm_id_inverse")                # 0.5(bin .24)·0.7(bin .23) 사이, bin (0.5, 1] 앵커 2개
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_cross_bin" and det["table"] == "tol_v" and det["w_key"] == 1000
