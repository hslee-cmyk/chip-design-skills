"""`tol_vdsat_table` / `TolVdsatTable` -- CONTRACT 5.2 [r6].

- 열 = column_source(..., "VDSAT")(없으면 lut_column_unavailable, 표 없음). 축·bin 지도 = 출처 표의 것, `origin` 속성.
- 셀 (i_L, k_VDS): 축 a 마다 내부 격자점을 빼고 두 이웃 **선형** 추정(운영 vdsat 와 같은 방법), 점 조건 = 그 점·축 방향 두 이웃이 출처
  on_mask(None 이면 모든 점), L 축은 bin 안 내부 앵커에서만. 점 값 |VDSAT_loo − VDSAT|. `vdsat_loo_v` = 환산 전 셀 최댓값,
  `vdsat_v` = 점 값 / 2^2 의 최댓값과 외부 bin 값의 최댓값(셀 None 이면 None). loo_orders 네 줄(축 이름순, linear 2, 0.25).
- 외부 값 l_bin_checks = ((model, vdsat_v), ...): None(기본) = midpoint rows 의 (model, vdsat_v), () = 없음, 셀 단위(VDS 별 수열,
  수 하나·None 허용), 길이 다르면 ValueError, 중복·앵커 2개 bin 아님·빈 지도에 값 -> ValueError. 상태 이름은 5절과 같다.
- at(L, vds, metric="vdsat") = 5절 at 규칙, context table "tol_vdsat", 다른 metric -> ValueError. memo derived 키 (kind, w_key, 정규화).
기대값: conftest `vdsat_loo_cell_ref`(npz 직접), 중점 toy 닫힌 식(L 방향 LOO = 0.05·(Lu_i − Lu_{i−1})(Lu_{i+1} − Lu_i)·(1 + d)).
"""
import bisect
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import (TOL_VDSAT_METRICS, LBinMap, TolVdsatCell, TolVdsatTable, midpoint_l_bin_checks,
                             tol_vdsat_table)

from sizing.conftest import W_KEY, write_r4_lut

from .conftest import (BIN_ANCHOR_BIN_LO, BIN_L, T_KEYS, T_MID_L, T_WIDTHS, build_t, detail_of, gamma_n, mid_file,
                       mid_toy_arrays, midpoint_ref, new_memo, r6_toy_cap_arrays, t_spec, vdsat_loo_cell_ref)

M = "toyn__model."
BIN_AB = (0, 0, 0, 1, 1, 3, 3, 4)                     # conftest 머리 표(폭 1e-6 슬라이스, 손계산)
LOO_ORDERS = (("vdsat", "L", "linear", 2, 0.25), ("vdsat", "VDS", "linear", 2, 0.25),
              ("vdsat", "VGS", "linear", 2, 0.25), ("vdsat", "VS", "linear", 2, 0.25))
MID_L = (3.5e-6, 7.5e-6)                              # bin B (3·4), D (7·8) 의 중점


def l_interior(ab, i):
    return bool(ab) and 0 < i < len(ab) - 1 and ab[i - 1] == ab[i] == ab[i + 1]


def _ref_table(grids, V, on, ab):
    return [[vdsat_loo_cell_ref(grids, V, on, i, k, l_interior(ab, i)) for k in range(len(grids[2]))]
            for i in range(len(grids[0]))]


def _check_cells(t, ref, ext=None):
    """셀 대조: vdsat_loo_v = 독립 환산 전 최댓값(유도 반올림 상한 안), vdsat_v = 독립 /4 와 외부 값(그 행·그 k)의 최댓값."""
    for i, row in enumerate(ref):
        for k, (loo, scaled, bnd) in enumerate(row):
            c = t.cells[i][k]
            assert isinstance(c, TolVdsatCell)
            if loo is None:
                assert c.vdsat_loo_v is None and c.vdsat_v is None, (i, k)
                continue
            assert abs(c.vdsat_loo_v - loo) <= bnd, (i, k, c.vdsat_loo_v, loo, bnd)
            e = None if ext is None else ext.get(i, (None,) * len(row))[k]
            if e is not None and e > scaled:
                assert c.vdsat_v == e, (i, k, c.vdsat_v, e)
            else:
                assert abs(c.vdsat_v - scaled) <= bnd / 4, (i, k, c.vdsat_v, scaled)


# ---------------------------------------------------------------------------
# toy
# ---------------------------------------------------------------------------

def test_contract_toy_r6_row(toy_build):
    """7.1 r6: 기준 LUT VDSAT_n = 0.1 + 0.2·VGS (선형 자료) -> 모든 셀 vdsat_v 0 수준, origin "cap_table"; w_key 200 -> 열 없음."""
    m = new_memo(toy_build("r6t", cap=r6_toy_cap_arrays()).load())
    t = tol_vdsat_table(m, "nmos", 100)
    assert isinstance(t, TolVdsatTable) and t.origin == "cap_table"
    assert (t.kind, t.w_key) == ("nmos", 100)
    for row in t.cells:
        for c in row:
            assert c.vdsat_v is not None and abs(c.vdsat_v) <= 8 * gamma_n() * 0.3
    with pytest.raises(SealViolationError) as ei:
        tol_vdsat_table(m, "nmos", 200)
    assert detail_of(ei.value)["reason"] == "lut_column_unavailable"


def test_contract_toy_r6_unavailable(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        tol_vdsat_table(toy_memo, "nmos", 100)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_column_unavailable" and det["column"] == "VDSAT"
    assert dict(toy_memo.stats())["derived"].hits == 0


def test_loo_orders_and_metrics(mid_toy_build):
    t = tol_vdsat_table(new_memo(mid_toy_build("lo").load()), "nmos", 100, ())
    assert tuple(tuple(r) for r in t.loo_orders) == LOO_ORDERS
    assert TOL_VDSAT_METRICS == ("vdsat",)
    with pytest.raises(ValueError):
        t.at(3e-6, 0.75, "id_equivalent")


def test_mid_toy_cells_match_independent_and_hand_l_direction(mid_toy_build):
    """외부 값 없음(()): 셀 = 독립 구현. L 방향 LOO 는 bin A 의 내부 앵커 1(1.5 µm)에만 -- 손계산 0.05·(1.5 − 1)(2 − 1.5)·(1 + d)
    = 0.0125·(1 + d) (VGS·VS 방향은 VDSAT 이 선형/무관이라 0, VDS 는 2 점이라 내부점 없음). 다른 행은 0 수준(판별)."""
    mt = mid_toy_build("cells")
    t = tol_vdsat_table(new_memo(mt.load()), "nmos", 100, ())
    z = mt.slice_arrays[0]
    grids = (BIN_L, tuple(z["VGS"]), tuple(z["VDS"]), tuple(z["VS"]))
    on = (z["ID"] > 0) & (z["GM"] > 0)
    _check_cells(t, _ref_table(grids, z["VDSAT"], on, BIN_AB))
    for k, d in enumerate(z["VDS"]):
        hand = 0.0125 * (1 + d)
        assert abs(t.cells[1][k].vdsat_loo_v - hand) <= 8 * gamma_n() * 1.0
        assert t.cells[1][k].vdsat_v == t.cells[1][k].vdsat_loo_v / 4
        for i in (0, 2, 3, 7):
            assert t.cells[i][k].vdsat_loo_v <= 8 * gamma_n() * 2.0 < hand
    assert tuple(t.l_loo) == ("bin_edge", "in_bin_interior", "bin_edge", "bin_missing_external", "bin_missing_external",
                              "bin_missing_external", "bin_missing_external", "bin_single_point")
    assert tuple(t.l_loo_bins) == ((M + "0", (0, 1, 2), "computed"), (M + "1", (3, 4), "missing_external"),
                                   (M + "3", (5, 6), "missing_external"), (M + "4", (7,), "single_point"))
    assert t.l_bins == mt.load().slice_map[("nmos", 100)].l_bins
    assert tuple(t.L_anchors) == BIN_L and tuple(t.vds_grid) == tuple(z["VDS"])


def test_point_condition_on_mask(mid_toy_build):
    """점 조건 = 그 점·축 방향 두 이웃이 출처 on_mask: ID 0 점 하나를 두면 그 점을 쓰는 LOO 가 빠진다(독립 구현과 같다).
    판별: 그 점의 VDSAT 을 크게 바꿔도 셀 값이 그 점에 끌려가지 않는다."""
    def mod(arrs):
        a = arrs[0]
        a["ID"] = a["ID"].copy()
        a["ID"][1, 1, 0, 0] = 0.0
        a["VDSAT"] = a["VDSAT"].copy()
        a["VDSAT"][1, 1, 0, 0] = 5.0                               # off 점의 큰 값
    mt = mid_toy_build("onm", slice_mod=mod)
    t = tol_vdsat_table(new_memo(mt.load()), "nmos", 100, ())
    z = mt.slice_arrays[0]
    on = (z["ID"] > 0) & (z["GM"] > 0)
    assert not on[1, 1, 0, 0]
    grids = (BIN_L, tuple(z["VGS"]), tuple(z["VDS"]), tuple(z["VS"]))
    _check_cells(t, _ref_table(grids, z["VDSAT"], on, BIN_AB))
    assert t.cells[1][0].vdsat_loo_v < 1.0                          # 5.0 이 들어갔다면 ~4.9


def test_default_external_from_midpoints_per_vds(mid_toy_build):
    """기본(None) = 중점 rows 의 (model, vdsat_v), VDS 별: bin B·D 중점 3.5·7.5 µm -> 0.05·0.25·(1 + d) = (0.01875, 0.025).
    그 bin 두 앵커 행의 셀 (i, k) 에 k 번째 원소만(정의된 셀 값과의 최댓값). 상태 external."""
    mt = mid_toy_build("ext", mid={0: MID_L})
    m = new_memo(mt.load())
    t = tol_vdsat_table(m, "nmos", 100)
    base = tol_vdsat_table(m, "nmos", 100, ())
    z = mt.slice_arrays[0]
    hand = tuple(0.0125 * (1 + d) for d in z["VDS"])
    rows = {r.model: r for r in midpoint_l_bin_checks(m, "nmos", 100).rows}
    for mo in (M + "1", M + "3"):
        for k in range(2):
            assert abs(rows[mo].vdsat_v[k] - hand[k]) <= 8 * gamma_n() * 2.0
    ext = {i: rows[M + "1"].vdsat_v for i in (3, 4)}
    ext.update({i: rows[M + "3"].vdsat_v for i in (5, 6)})
    grids = (BIN_L, tuple(z["VGS"]), tuple(z["VDS"]), tuple(z["VS"]))
    on = (z["ID"] > 0) & (z["GM"] > 0)
    _check_cells(t, _ref_table(grids, z["VDSAT"], on, BIN_AB), ext)
    for i in (3, 4, 5, 6):
        for k in range(2):
            assert t.cells[i][k].vdsat_loo_v == base.cells[i][k].vdsat_loo_v       # 환산 전 필드에는 안 들어간다
            assert t.cells[i][k].vdsat_v == max(base.cells[i][k].vdsat_v, ext[i][k])
            assert t.cells[i][k].vdsat_v > base.cells[i][k].vdsat_v                 # 실제로 올라갔다
    assert t.cells[3][0].vdsat_v != t.cells[3][1].vdsat_v                            # 셀 단위(VDS 별 다른 값)
    assert tuple(s for _, _, s in t.l_loo_bins) == ("computed", "external", "external", "single_point")
    assert tuple(t.l_bin_checks) == tuple(sorted((r.model, tuple(r.vdsat_v)) for r in rows.values()))


def test_external_scalar_sequence_none_and_memo_key(mid_toy_build):
    """수 하나 = 모든 k 같은 값(같은 memo 키 -> 같은 객체), 원소 None = 그 k 외부 몫 없음, 정규화 = model 정렬·k 별 tuple."""
    m = new_memo(mid_toy_build("seq").load())
    base = tol_vdsat_table(m, "nmos", 100, ())
    a = tol_vdsat_table(m, "nmos", 100, ((M + "3", 0.5), (M + "1", 0.25)))
    b = tol_vdsat_table(m, "nmos", 100, ((M + "1", (0.25, 0.25)), (M + "3", [0.5, 0.5])))
    assert a is b
    assert tuple(a.l_bin_checks) == ((M + "1", (0.25, 0.25)), (M + "3", (0.5, 0.5)))
    c = tol_vdsat_table(m, "nmos", 100, ((M + "1", (None, 0.25)),))
    assert c is not a
    for i in (3, 4):
        assert c.cells[i][0] == base.cells[i][0]
        assert c.cells[i][1].vdsat_v == 0.25
    assert tuple(s for _, _, s in c.l_loo_bins)[1:3] == ("external", "missing_external")
    d = tol_vdsat_table(m, "nmos", 100, ((M + "1", None),))
    assert all(d.cells[i][k] == base.cells[i][k] for i in range(len(BIN_L)) for k in range(2))


@pytest.mark.parametrize("checks", [
    ((M + "1", (0.1, 0.2, 0.3)),),                       # 길이 3 ≠ VDS 2
    ((M + "1", (0.1,)),),                                # 길이 1
    ((M + "1", 0.1), (M + "1", 0.2)),                     # 같은 model 두 번
    ((M + "0", 0.1),),                                   # 앵커 3개 bin
    ((M + "4", 0.1),),                                   # 앵커 1개 bin
    ((M + "2", 0.1),),                                   # 앵커 0개 bin
    (("no_such_model", 0.1),),
])
def test_external_invalid(mid_toy_build, checks):
    m = new_memo(mid_toy_build("inv").load())
    with pytest.raises(ValueError):
        tol_vdsat_table(m, "nmos", 100, checks)


def test_external_on_empty_map_invalid(toy_build):
    m = new_memo(toy_build("emp", cap=r6_toy_cap_arrays(), empty_bins=True).load())
    with pytest.raises(ValueError):
        tol_vdsat_table(m, "nmos", 100, (("anything", 0.1),))
    t = tol_vdsat_table(m, "nmos", 100)
    assert tuple(t.l_loo) == ("bins_unavailable",) * 3 and tuple(t.l_loo_bins) == ()
    assert t.l_bins == LBinMap((), None, (), ())


@pytest.mark.parametrize("L,rows", [(1.25e-6, (0, 1)), (3.5e-6, (3, 4)), (3e-6, (3,)), (7.5e-6, (5, 6))])
def test_at_rows_and_cells(mid_toy_build, L, rows):
    t = tol_vdsat_table(new_memo(mid_toy_build("at").load()), "nmos", 100, ())
    Va = list(t.vds_grid)
    for vds in (0.5, 0.75, 1.0):
        kk = min(bisect.bisect_right(Va, vds) - 1, len(Va) - 2)
        vals = [t.cells[i][b].vdsat_v for i in rows for b in (kk, kk + 1)]
        # [LM-1e §5 셀 결합] 모두 정의되면 max, 하나라도 None 이면 None
        assert t.at(L, vds) == (None if any(v is None for v in vals) else max(vals))
        assert t.at(L, vds, "vdsat") == t.at(L, vds)


@pytest.mark.parametrize("L,vds,reason", [(2.5e-6, 0.75, "lut_l_cross_bin"), (4.5e-6, 0.75, "lut_l_bin_unbracketed"),
                                          (5.5e-6, 0.75, "lut_l_outside_model_bins"),
                                          (3e-6, 1.1, "lut_axis_out_of_range")])
def test_at_rejects_with_context(mid_toy_build, L, vds, reason):
    t = tol_vdsat_table(new_memo(mid_toy_build("atr").load()), "nmos", 100, ())
    with pytest.raises(SealViolationError) as ei:
        t.at(L, vds)
    det = detail_of(ei.value)
    assert det["reason"] == reason
    assert det["table"] == "tol_vdsat" and det["kind"] == "nmos" and det["w_key"] == 100


def test_memo_derived_once(mid_toy_build):
    m = new_memo(mid_toy_build("memo").load())
    a = tol_vdsat_table(m, "nmos", 100, ())
    st = dict(m.stats())["derived"]
    assert tol_vdsat_table(m, "nmos", 100, ()) is a
    st2 = dict(m.stats())["derived"]
    assert (st2.misses, st2.hits) == (st.misses, st.hits + 1)


# ---------------------------------------------------------------------------
# 실데이터 (LUT v2 + 중점 파일, 기본 외부 값)
# ---------------------------------------------------------------------------

def _real_ref(real_lut, raw_slice, raw_mid, kind, suf, wk, with_ext=True):
    z = raw_slice(kind, wk)
    ab = tuple(real_lut.slice_map[(kind, wk)].l_bins.anchor_bin)
    grids = tuple(tuple(float(x) for x in z[a]) for a in ("L", "VGS", "VDS", "VS"))
    on = (z["ID"] > 0) & (z["GM"] > 0)
    ref = _ref_table(grids, z["VDSAT"], on, ab)
    ext = {}
    if with_ext and (kind, wk) in real_lut.midpoints:                  # [LM-1e] 중점 파일은 폭마다(`widths` 안 슬라이스 전부)
        mid = raw_mid(kind, wk)
        Lg = list(grids[0])
        for mi, Lm in enumerate(float(x) for x in mid["L"]):
            k = bisect.bisect_right(Lg, Lm)
            if 0 < k < len(Lg) and ab[k - 1] == ab[k] and ab.count(ab[k]) == 2 and Lg[k - 1] < Lm < Lg[k]:
                r = midpoint_ref(z, mid, "", mi, k - 1, k, z["VDSAT"], on)
                ext[k - 1] = ext[k] = tuple(r["vdsat"])
    return ref, ext


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,suf,wk", [("nmos", "_n", 1000), ("pmos", "_p", 1000), ("nmos", "_n", 72), ("pmos", "_p", 84)])
def test_real_cells_match_independent(real_lut, raw_slice, raw_mid, kind, suf, wk):
    """전 셀 = 독립 구현(npz 직접; L 방향은 엔진 bin 지도 -- 지도 자체는 test__helpers_bins 가 ngspice 로 확인) + 중점 외부 값(5.1 독립).
    [LM-1e] 다른 폭(72·84)도 `widths` 안이라 자기 중점 파일을 가진다: 앵커 2개 bin 마다 외부 값이 들고 missing_external 은 없다(D7).
    [2026-10-08 중점 변경, CONTRACT 8절] w_key 1000: 중점 0.165·0.85·1.75·3.25 µm -> 앵커 2개 bin 4개(.26 (0, 1)·.23 (10, 11)·
    .22 (12, 13)·.21 (14, 15)) 모두 external."""
    t = tol_vdsat_table(new_memo(real_lut), kind, wk)
    assert t.origin == "slice"
    ref, ext = _real_ref(real_lut, raw_slice, raw_mid, kind, suf, wk)
    _check_cells(t, ref, ext)
    sts = [s for _, _, s in t.l_loo_bins]
    if wk == 1000:
        assert sorted(ext) == [0, 1, 10, 11, 12, 13, 14, 15]
        assert sts == ["external", "computed", "computed", "external", "external", "external",
                       "single_point", "single_point"]
    else:
        # D7: 앵커 2개 bin 마다 두 앵커 사이 중점이 있어 적재됐다 -> 외부 값이 든 bin 만 있고 missing_external 은 없다
        assert sts.count("external") >= 1 and "missing_external" not in sts
        assert sorted(ext) == sorted(i for _, idx, s in t.l_loo_bins if s == "external" for i in idx)
    vals = sorted(c.vdsat_v for row in t.cells for c in row if c.vdsat_v is not None)
    print("%s %d vdsat_v p50/p90/max = %.3g/%.3g/%.3g mV" % (kind, wk, 1e3 * np.percentile(vals, 50),
                                                             1e3 * np.percentile(vals, 90), 1e3 * vals[-1]))


def printed_close(got, text, scale):
    """계약에 적힌 숫자 문자열(단위 scale)과 그 표기의 마지막 자리 반 단위 안에서 같은가."""
    dec = len(text.split(".")[1]) if "." in text else 0
    return abs(got / scale - float(text)) <= 0.5 * 10 ** (-dec)


def _ref_cell_values(real_lut, raw_slice, raw_mid, kind, suf, wk):
    """독립 셀 값(5.2: 환산 후 = 환산 전/4 와 그 행·k 의 외부 값의 최댓값)과 셀마다의 허용 차(유도 반올림 상한/4) -- {(i, k): (값, 상한)}."""
    ref, ext = _real_ref(real_lut, raw_slice, raw_mid, kind, suf, wk)
    out = {}
    for i, row in enumerate(ref):
        for k, (loo, scaled, bnd) in enumerate(row):
            if loo is None:
                continue
            e = ext.get(i, (None,) * len(row))[k]
            out[(i, k)] = (e, 0.0) if (e is not None and e > scaled) else (scaled, bnd / 4)
    return out


# CONTRACT 8절 표(2026-10-08) vdsat 열(mV) 의 bin 별 최댓값 중 최대 -- nmos .21 6.39, pmos .26 32.5 (oracle (d) 계약 기록값)
CONTRACT_8_VDSAT_MAX = {"nmos": "6.39", "pmos": "32.5"}


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,suf,wk,p50,p90,mx", [("nmos", "_n", 1000, None, None, CONTRACT_8_VDSAT_MAX["nmos"]),
                                                     ("pmos", "_p", 1000, None, None, CONTRACT_8_VDSAT_MAX["pmos"]),
                                                     ("nmos", "_n", 72, None, None, None),
                                                     ("pmos", "_p", 84, None, None, None)])
def test_real_contract_measured(real_lut, raw_slice, raw_mid, kind, suf, wk, p50, p90, mx):
    """계약 5.2 실측(셀 vdsat_v p50/p90/max, mV 표기 자릿수 안). 분위수 정의 = numpy 기본(선형).
    [2026-10-08 중점 변경] w_key 1000 은 앵커 2개 bin 4개 모두 외부 값을 받아 5.2 의 옛 실측(0.93/1.88/2.49, 1.08/10.2/32.5 mV)이
    더는 계약 값이 아니다(5.2 문장은 갱신되지 않았다 -- 보고). 그래서 w_key 1000 의 p50·p90 은 (b) 독립 셀 값(`_ref_cell_values`)의
    분위수와 셀 상한 안에서 같고(분위수는 원소별 섭동에 1-Lipschitz), max 는 (d) CONTRACT 8절 표 vdsat 열 최대(외부 값 > LOO/4 셀 값).
    다른 폭(72·84)은 중점 폭이 아니라 바뀌지 않아 5.2 실측 그대로."""
    t = tol_vdsat_table(new_memo(real_lut), kind, wk)
    vals = np.asarray([c.vdsat_v for row in t.cells for c in row if c.vdsat_v is not None])
    if p50 is None:
        ref = _ref_cell_values(real_lut, raw_slice, raw_mid, kind, suf, wk)
        rv = np.asarray([v for v, _ in ref.values()])
        rb = max(b for _, b in ref.values())
        assert len(rv) == len(vals)
        for q in (50, 90):
            assert abs(np.percentile(vals, q) - np.percentile(rv, q)) <= rb, (kind, q)
        if mx is not None:                      # (d) CONTRACT 8절 기록값은 w_key 1000 만(다른 폭의 옛 실측은 외부 값 없던 때의 것이라 독립 값(b)으로 대체)
            assert printed_close(vals.max(), mx, 1e-3), (kind, wk, vals.max(), mx)
        return
    for got, want in ((np.percentile(vals, 50), p50), (np.percentile(vals, 90), p90), (vals.max(), mx)):
        assert printed_close(got, want, 1e-3), (kind, wk, got, want)


@pytest.mark.lut_realdata
def test_real_contract_at_example(real_lut, raw_slice, raw_mid):
    """계약 5.2 예 `tol_vdsat_table(nmos, 1000).at(1e-6, 0.9)`. [2026-10-08 중점 변경] L = 1 µm 은 앵커 2개 bin .23(0.7·1 µm)의 앵커라
    이제 중점 0.85 µm 의 외부 값을 받는다 -- 5.2 의 옛 값 0.93 mV 는 외부 값 없던 때의 것(5.2 문장 미갱신 -- 보고).
    기대값 = (b) 독립 셀 값(`_ref_cell_values`)으로 5절 at 규칙(앵커 행 하나 × VDS 칸 두 셀의 최댓값)을 다시 계산, 허용 차 = 그 셀 상한.
    판별: 같은 조회를 외부 값 없는 표(l_bin_checks=())로 하면 5.2 의 옛 예 0.93 mV 이고, 기본 표 값은 그 이상이다."""
    m = new_memo(real_lut)
    t = tol_vdsat_table(m, "nmos", 1000)
    v = t.at(1e-6, 0.9)
    z = raw_slice("nmos", 1000)
    Lg = [float(x) for x in z["L"]]
    Va = [float(x) for x in z["VDS"]]
    rows = [i for i, a in enumerate(Lg) if abs(1e-6 - a) <= math.ulp(a)]
    assert len(rows) == 1
    kk = min(bisect.bisect_right(Va, 0.9) - 1, len(Va) - 2)
    ref = _ref_cell_values(real_lut, raw_slice, raw_mid, "nmos", "_n", 1000)
    cells = [ref[(rows[0], b)] for b in (kk, kk + 1) if (rows[0], b) in ref]
    exp = max(c[0] for c in cells)
    assert abs(v - exp) <= max(c[1] for c in cells), (v, exp)
    v0 = tol_vdsat_table(m, "nmos", 1000, ()).at(1e-6, 0.9)
    assert printed_close(v0, "0.93", 1e-3), v0                       # (d) 5.2 옛 예 = 외부 값 없는 값
    assert v >= v0                                                   # 5.2: 외부 값은 셀 값과의 최댓값에만 들어간다




# ---------------------------------------------------------------------------
# [LM-1e §5] 셀 결합 `at` (A-0v) -- toy R(pmos 의 VDS index 0 열이 꺼짐): VDSAT LOO 셀 0 = None(점 조건: 그 점·이웃이 모두 on 인 점이 없다).
# 결합 셀이 모두 정의되면 max, 하나라도 None 이면 None. oracle: (a) 구성으로 정해진 답 + (d) interface 결합 규칙.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("iL", [0, 1])
def test_cell_combine_a0v_none_cell_makes_none(tmp_path, iL):
    t = tol_vdsat_table(new_memo(write_r4_lut(tmp_path / "roff", off_cols={"pmos": 1})), "pmos", W_KEY)
    L = t.L_anchors[iL]
    row = t.cells[iL]
    assert tuple(t.vds_grid)[:3] == (0.0, 0.25, 0.5)
    # 전제(안 서면 멈춘다): 셀 VDS index 0 = None, index 1·2 ≠ None
    assert row[0].vdsat_v is None and row[1].vdsat_v is not None and row[2].vdsat_v is not None
    for vds in (0.0, 0.1, 0.2499):                                    # 칸 [0, 0.25): 셀 0 = None 포함 -> None (옛 규칙은 셀 1 값)
        assert t.at(L, vds) is None, vds
    hand = max(row[1].vdsat_v, row[2].vdsat_v)                        # 칸 [0.25, 0.5): 두 셀 모두 정의 -> max
    for vds in (0.25, 0.3, 0.4999):
        assert t.at(L, vds) == hand, vds


# ---------------------------------------------------------------------------
# [LM-1e §3 T-8] toy T 의 `tol_vdsat_table`: 행 3~6 = max(5.2 LOO 독립 구현 값, VDSAT 외부 값), 나머지 행 = LOO.
# 외부 값 = conftest `midpoint_ref` 의 vdsat(중점 VDSAT 와 슬라이스 선형 보간 차의 최댓값, 닫힌 식: 0.05·(Lu_m − Lu0)(Lu1 − Lu_m)·(1 + d)).
# ---------------------------------------------------------------------------

def _vd_bound(v):
    return 8 * gamma_n() * v


@pytest.mark.parametrize("idx", [0, 1])
def test_lm1e_t8_vdsat_cells_are_max_of_loo_and_ext(mid_toy_build, idx):
    W, sc = T_WIDTHS[idx]
    lut = build_t(mid_toy_build, "t8", {0: T_MID_L, 1: T_MID_L}).load(t_spec(0.6e-6))
    t = tol_vdsat_table(new_memo(lut), "nmos", T_KEYS[idx])
    z = mid_toy_arrays(W, sc, {})
    mid = mid_file(W, sc, T_MID_L)
    on = (z["ID"] > 0) & (z["GM"] > 0)
    grids = (BIN_L, tuple(z["VGS"]), tuple(z["VDS"]), tuple(z["VS"]))
    ref = _ref_table(grids, z["VDSAT"], on, BIN_AB)
    ext = {}
    for mi, i0, i1 in ((0, 3, 4), (1, 5, 6)):                          # 3.5 µm -> model.1 앵커 3·4, 7.5 µm -> model.3 앵커 5·6(0 시작 index)
        r = midpoint_ref(z, mid, "", mi, i0, i1, z["VDSAT"], on)
        ext[i0] = ext[i1] = tuple(r["vdsat"])
    lifted = 0
    for i, row in enumerate(ref):
        for k, (loo, scaled, bnd) in enumerate(row):
            c = t.cells[i][k]
            assert abs(c.vdsat_loo_v - loo) <= bnd, (i, k)             # 외부 값은 환산 전 필드에 들어가지 않는다
            e = ext.get(i, (None,) * len(row))[k]
            if e is not None and e > scaled:
                assert abs(c.vdsat_v - e) <= _vd_bound(8.0) + bnd / 4, (i, k, c.vdsat_v, e)
                lifted += 1
            else:
                assert abs(c.vdsat_v - scaled) <= bnd / 4, (i, k, c.vdsat_v, scaled)
    assert lifted > 0, "판별: 외부 값이 어느 셀도 올리지 못하면 이 test 가 외부 값을 구별하지 못한다"
    assert tuple(s for _, _, s in t.l_loo_bins) == ("computed", "external", "external", "single_point")
