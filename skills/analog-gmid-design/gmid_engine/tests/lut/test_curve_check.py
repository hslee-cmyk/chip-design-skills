"""`curve_report` -- CONTRACT 4절·7절: 슬라이스·L 앵커마다 CurveRow, 격자점 곡선만, ID·GM 0 이하 점이 있는 곡선은 n_skipped,
행 순서 (kind, w_key) 정렬 후 L 오름차순. memo 영역 derived.
"""
import numpy as np
import pytest

from gmid_engine.lut import CurveReport, CurveRow, curve_report

from .conftest import TOY_L, new_memo, rel_close, standard_toy_slices


def test_contract_toy_row0(toy, toy_memo):
    rep = curve_report(toy_memo)
    assert isinstance(rep, CurveReport)
    assert rep.lut_fp == toy.fp
    r = rep.rows[0]
    assert isinstance(r, CurveRow)
    assert (r.kind, r.w_key, r.L) == ("nmos", 100, 1e-6)
    assert r.n_curves == 4 and r.n_skipped == 0 and r.n_branch_nonmonotonic == 0
    assert rel_close(r.gm_id_max, 20.0, 1e-12)
    assert rel_close(r.gm_gds_max, 200.0, 1e-12)


def test_row_order_and_count(toy_memo):
    rows = curve_report(toy_memo).rows
    assert [(r.kind, r.w_key, r.L) for r in rows] == [("nmos", wk, L) for wk in (100, 200) for L in TOY_L]


def test_nonpositive_point_curve_is_skipped(toy_build):
    sl = standard_toy_slices()
    a = sl[0][2]
    a["ID"][0, 0, 0, 0] = 0.0          # L=1e-6, VDS 0.5, VS 0 곡선 한 개에 0 점
    a["GM"][0, 2, 1, 1] = -1e-9        # L=1e-6, VDS 1.0, VS 0.5 곡선 한 개에 음수 GM
    m = new_memo(toy_build(slices=sl).load())
    rows = curve_report(m).rows
    r0 = rows[0]
    assert (r0.kind, r0.w_key, r0.L) == ("nmos", 100, 1e-6)
    assert r0.n_skipped == 2
    # 계약은 n_curves 가 건너뛴 곡선을 포함하는지 적지 않았다 -- 구현은 '검사한 곡선 수'(합 = (VDS, VS) 곡선 4 개)
    assert r0.n_curves + r0.n_skipped == 4 and r0.n_curves == 2
    assert rows[1].n_skipped == 0
    # 남은 곡선(VDS 0.5·VS 0.5, VDS 1.0·VS 0) 값만: gm/ID 최대 20, gm/gds 최대 200
    assert rel_close(r0.gm_id_max, 20.0, 1e-12)


def test_derived_memo_reuse(toy_memo):
    a = curve_report(toy_memo)
    b = curve_report(toy_memo)
    assert a is b
    st = dict(toy_memo.stats())["derived"]
    assert st.misses == 1 and st.hits == 1


@pytest.mark.lut_realdata
def test_real_rows_against_npz(real_lut, raw_slice):
    memo = new_memo(real_lut)
    rows = curve_report(memo).rows
    keys = sorted(real_lut.slice_map)
    expect_order = []
    for (kind, wk) in keys:
        L = real_lut.slice_map[(kind, wk)].grids[0]
        expect_order += [(kind, wk, float(x)) for x in L]
    assert [(r.kind, r.w_key, r.L) for r in rows] == expect_order
    by = {(r.kind, r.w_key, r.L): r for r in rows}
    for kind, wk in (("nmos", 72), ("pmos", 1000)):
        z = raw_slice(kind, wk)
        ID, GM, GDS = z["ID"], z["GM"], z["GDS"]
        for iL, L in enumerate(z["L"]):
            r = by[(kind, wk, float(L))]
            I, G, D = ID[iL], GM[iL], GDS[iL]           # [VGS, VDS, VS]
            ok = np.all(I > 0, axis=0) & np.all(G > 0, axis=0)
            assert r.n_curves == int(ok.sum()) and r.n_curves + r.n_skipped == ok.size
            assert r.n_skipped == int((~ok).sum())
            if ok.any():
                gmid = (G / np.where(I > 0, I, 1.0))[:, ok]
                gmgds = (G / D)[:, ok]
                assert rel_close(r.gm_id_max, float(gmid.max()), 1e-9), (kind, wk, L)
                assert rel_close(r.gm_gds_max, float(gmgds.max()), 1e-9), (kind, wk, L)
            assert 0 <= r.n_branch_nonmonotonic <= r.n_curves
