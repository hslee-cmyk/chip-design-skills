"""`tol_v_table` / `TolVTable` -- CONTRACT 5절 [r5]: LOO 추정 = 운영 보간과 같은 방법(ln ID 의 VGS 축 Hermite(기울기 GM/ID)·
VDS 축 Hermite(기울기 GDS/ID, 두 이웃 vds_slope_ok 일 때, 아니면 선형)·VS·L 선형; gm/ID 곡선 LOO: VGS 축 = 마디 j 를 뺀 곡선,
VDS 축 = ln ID 위 식 + gm/ID 선형, VS·L 선형), Richardson 환산 = 그 (지표, 축, 방법) 의 차수 p 로 2^p 나눔
(id_equivalent: L 2·VGS 4·VDS 4(선형 폴백 2)·VS 2, gm_id_inverse: L 2·VGS 3·VDS 2·VS 2), 환산 전 값 `*_loo_v` 기록,
`loo_orders` 표. 셀별 TolVCell, 모든 L 앵커가 셀, 축 양끝 규칙, at() = L 위치(4.0) + VDS 두 칸 최댓값.

셀 값은 conftest 의 독립 구현(`tol_cell_ref` -- npz 직접, 계약 5절 식·3절 칸 선택 + 칸 안 Hermite 미분 근)과 대조한다.
끝의 ngspice 칸 중앙 표본 test(계약 5절 '환산 검증 test')는 셀 tol 이 실제 칸 중앙 오차의 상한인지 확인한다.
"""
import bisect
import json
import math
import os
import re
import shutil
import subprocess

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import (TOL_V_METRICS, LBinMap, TolVCell, TolVTable, midpoint_l_bin_checks, op_point,
                             tol_v_table)

from .conftest import (BIN_ANCHOR_BIN_HI, BIN_ANCHOR_BIN_LO, BIN_L, TOY_L, TOY_VDS, RefSlice, bin_toy_raw, detail_of,
                       hermite_val, midpoint_ref, new_memo, parse_model_bins, r4_toy_slice_arrays, rel_close, same_bounds,
                       sha256_file, tol_cell_ref, toy_slice_arrays, um)

LOO_ORDERS_EXPECTED = (
    ("gm_id_inverse", "L", "linear", 2, 0.25),
    ("gm_id_inverse", "VDS", "linear_slope", 2, 0.25),
    ("gm_id_inverse", "VGS", "hermite_slope", 3, 0.125),
    ("gm_id_inverse", "VS", "linear", 2, 0.25),
    ("id_equivalent", "L", "linear", 2, 0.25),
    ("id_equivalent", "VDS", "hermite", 4, 0.0625),
    ("id_equivalent", "VGS", "hermite", 4, 0.0625),
    ("id_equivalent", "VS", "linear", 2, 0.25),
)
FIELDS = (("gm_id_inverse_v", "inv"), ("id_equivalent_v", "eq"),
          ("gm_id_inverse_loo_v", "inv_loo"), ("id_equivalent_loo_v", "eq_loo"))


def _cell_matches(c, ref):
    """허용 차 = 독립 구현이 셀마다 유도한 상한(conftest `hermite_root_bound`·`tol_cell_ref` 의 γ_n 유도 -- 임의 상수 없음):
    gm_id_inverse = 시도마다 (두 경로 residual 반올림 / |p''(근)| + bisection 분해능 2 ulp + 뺄셈 1 ulp) 의 최댓값,
    id_equivalent = 점마다 (추정·뺄셈 반올림 / gm/ID + 나눗셈 상대 오차) 의 최댓값. 시도·실패 수는 정확히."""
    assert (c.n_targets, c.n_inverse_failed) == (ref["n_t"], ref["n_f"])
    for attr, key in FIELDS:
        got, exp = getattr(c, attr), ref[key]
        if exp is None:
            assert got is None, attr
        else:
            tol = ref[key + "_bound"] if key in ("inv", "eq") else ref[key.replace("_loo", "_loo_bound")]
            assert got is not None and abs(got - exp) <= tol, (attr, got, exp, tol)


# ---------------------------------------------------------------------------
# toy (CONTRACT 7.1 r5 toy, 7.2 r4 toy)
# ---------------------------------------------------------------------------

def test_contract_toy_cells(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    assert isinstance(t, TolVTable)
    assert (t.kind, t.w_key) == ("nmos", 100)
    assert tuple(t.L_anchors) == TOY_L and tuple(t.vds_grid) == TOY_VDS
    assert len(t.cells) == 3 and all(len(row) == 2 for row in t.cells)
    rs = RefSlice(toy_slice_arrays(1e-6))
    for i in range(3):                       # 모든 L 앵커(양끝 포함)가 셀을 가진다
        for k in range(2):
            c = t.cells[i][k]
            assert isinstance(c, TolVCell)
            # 0 수준(부동소수): VGS 축 Hermite LOO 가 2차식을 정확히 재현, VDS·VS 축은 2점이라 내부점 없음.
            # 참값 0 이므로 |값| ≤ |값 − 독립| + |독립 − 0| ≤ 2·(유도 상한)
            ref = tol_cell_ref(rs, i, k)
            for attr, key in FIELDS:
                v = getattr(c, attr)
                b = ref[key + "_bound"] if key in ("inv", "eq") else ref[key.replace("_loo", "_loo_bound")]
                assert v is not None and 0.0 <= v <= 2 * b, (i, k, attr, v, b)
            assert (c.n_targets, c.n_inverse_failed) == (2, 0)
            _cell_matches(c, ref)
    # 판별: 옛 선형 LOO 였다면 id_equivalent 환산 전 = |ln ID(0.5) 의 선형 추정 − 참값|/14 = 1.5/14
    assert rel_close(abs(0.5 * (0.0 + 14.0) - 8.5) / 14.0, 0.107, 2e-3)


def test_contract_toy_at(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    rs = RefSlice(toy_slice_arrays(1e-6))
    for metric, key in (("gm_id_inverse", "inv_bound"), ("id_equivalent", "eq_bound")):
        for i, L in ((1, 2e-6), (2, 3e-6)):
            b = max(tol_cell_ref(rs, i, k)[key] for k in range(2))       # at = 두 칸 최댓값 -> 상한도 두 칸 최댓값
            v = t.at(L, 0.75 if i == 1 else 1.0, metric)
            assert v is not None and 0.0 <= v <= 2 * b, (metric, L, v, b)
        assert t.at(1e-6 + math.ulp(1e-6), 0.5, metric) == t.at(1e-6, 0.5, metric)
    with pytest.raises(SealViolationError) as ei:
        t.at(1.5e-6, 0.75, "id_equivalent")
    assert detail_of(ei.value)["reason"] == "lut_l_not_anchor"


def test_loo_orders(toy_memo):
    """CONTRACT 5절 표·7.1 행: 8줄, 환산 배수 0.25·0.25·0.125·0.25·0.25·0.0625·0.0625·0.25 (지표·축 이름순)."""
    t = tol_v_table(toy_memo, "nmos", 100)
    lo = tuple(tuple(r) for r in t.loo_orders)
    assert lo == LOO_ORDERS_EXPECTED
    assert [r[4] for r in lo] == [0.25, 0.25, 0.125, 0.25, 0.25, 0.0625, 0.0625, 0.25]
    assert all(r[4] == 2.0 ** -r[3] for r in lo)


def test_r4_toy_cells(r4toy_memo):
    """CONTRACT 7.2 행: cells[0][0] id_equivalent_loo_v = |ln1e-6 − Hermite(ln1e-7, ln1e-5, 20, 4, H 1, t ½)|/10 = 0.2,
    id_equivalent_v = 0.2/16 = 0.0125. 모든 셀 = 독립 구현."""
    t = tol_v_table(r4toy_memo, "nmos", 100)
    c = t.cells[0][0]
    rs = RefSlice(r4_toy_slice_arrays(1e-6))
    r00 = tol_cell_ref(rs, 0, 0)
    assert abs(c.id_equivalent_loo_v - 0.2) <= r00["eq_loo_bound"]          # 닫힌 값과의 차 ≤ 유도 상한
    assert abs(c.id_equivalent_v - 0.0125) <= r00["eq_bound"]
    for i in range(3):
        for k in range(2):
            _cell_matches(t.cells[i][k], tol_cell_ref(rs, i, k))
    # gm_id_inverse 는 VGS 축(hermite_slope p 3) 하나뿐: 환산 후 = 환산 전 / 8 (2 의 거듭제곱 나눔은 정확),
    # LOO 는 FC 검사로 거르지 않는다(위반 칸 [0, 0.5] 를 품는 곡선에서도 값이 있다)
    assert c.gm_id_inverse_v == c.gm_id_inverse_loo_v / 8.0
    assert c.gm_id_inverse_v > 0.0


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
    assert all(c.gm_id_inverse_loo_v is None and c.id_equivalent_loo_v is None for row in t.cells for c in row)
    for metric in TOL_V_METRICS:
        assert t.at(1e-6, 0.7, metric) is None


def test_vds_linear_fallback_order(toy_build):
    """VDS 축 id_equivalent: 두 이웃 vds_slope_ok 가 아니면 선형 추정, 차수 p 2(환산 1/4). VDS 3점 곡선으로 확인."""
    from .conftest import CURVE_L, CURVE_VS, curve_cap_arrays
    vgs = (0.0, 0.5, 1.0)
    VDS3 = (0.5, 1.0, 1.5)
    ID = np.empty((2, 3, 3, 2))
    # 자료가 맞는 곡면: ln ID = ln1e-7 + 20v − 6v² + 0.3d² -> GM/ID = 20 − 12v, GDS/ID = 0.6d (Hermite 는 2차식 정확)
    v_ = np.asarray(vgs)
    for k, d in enumerate(VDS3):
        ID[:, :, k, :] = (1e-7 * np.exp(20 * v_ - 6 * v_ * v_) * math.exp(0.3 * d * d))[None, :, None]
    GM = ID * (20.0 - 12.0 * v_)[None, :, None, None]
    GDS = ID * (0.6 * np.asarray(VDS3))[None, None, :, None]
    GDS[0, 1, 0, 0] = 0.0                       # (L 0, VGS 0.5, VDS 0.5, VS 0) GDS 0 -> 그 위 점 VDS 방향 선형
    a = {"W": np.float64(1e-6), "L": np.asarray(CURVE_L), "VGS": np.asarray(vgs), "VDS": np.asarray(VDS3),
         "VS": np.asarray(CURVE_VS), "ID": ID, "GM": GM, "GDS": GDS, "VTH": np.full(ID.shape, 0.4),
         "meta_json": np.str_('{"model_files_sha256": {}}'), "corner": np.str_("tt"), "temp_c": np.float64(27.0)}
    cap = curve_cap_arrays(vgs)
    cap["VDS"] = np.asarray(VDS3)
    cap["CGG_n"] = np.full((2, 3, 3, 2), 1e-15)
    cap["CGD_n"] = np.full((2, 3, 3, 2), 2e-16)
    lut = toy_build("vds3", slices=[("v.npz", "toyn", a)], cap=cap).load()
    t = tol_v_table(new_memo(lut), "nmos", 100)
    rs = RefSlice(a)
    assert not rs.vds_ok[0, 1, 0, 0]
    for i in range(2):
        for k in range(3):
            _cell_matches(t.cells[i][k], tol_cell_ref(rs, i, k))
    # 손계산(i 0, k 1, VS 0, VGS 0.5): 선형 LOO 오차 = |½(0.3·0.25 + 0.3·2.25) − 0.3| = 0.075, gm/ID 14
    # -> 환산 전 0.075/14, 환산 후 /4. 다른 점은 Hermite(VDS·VGS) 가 2차식을 정확히 재현 -> 0 수준.
    c = t.cells[0][1]
    r01 = tol_cell_ref(rs, 0, 1)
    assert abs(c.id_equivalent_loo_v - 0.075 / 14.0) <= r01["eq_loo_bound"] + abs(r01["eq_loo"] - 0.075 / 14.0)
    assert abs(r01["eq_loo"] - 0.075 / 14.0) <= r01["eq_loo_bound"]          # 손계산 값 = 독립 구현(상한 안)
    assert c.id_equivalent_v == c.id_equivalent_loo_v / 4.0                  # 선형 폴백 p 2 -> 정확히 /4
    # 같은 셀의 L 1 행(GDS 정상)은 Hermite 라 0 수준(≤ 2·상한) -- 폴백이 없으면 L 0 행도 이 값이 된다(판별)
    r11 = tol_cell_ref(rs, 1, 1)
    assert t.cells[1][1].id_equivalent_loo_v <= 2 * r11["eq_loo_bound"]
    assert c.id_equivalent_loo_v > 2 * r11["eq_loo_bound"]


def test_deterministic_and_memo(toy, toy_memo):
    a = tol_v_table(toy_memo, "nmos", 100)
    assert tol_v_table(toy_memo, "nmos", 100) is a
    b = tol_v_table(new_memo(toy), "nmos", 100)
    assert a.cells == b.cells


def test_independent_impl_reproduces_contract_rows():
    """독립 구현 자체가 계약 7.1·7.2 값을 내는지(대조 기준 검증)."""
    rs5 = RefSlice(toy_slice_arrays(1e-6))
    rs4 = RefSlice(r4_toy_slice_arrays(1e-6))
    for i in range(3):
        for k in range(2):
            r = tol_cell_ref(rs5, i, k)
            assert all(r[key] <= r[key + "_bound"] for key in ("inv", "eq", "inv_loo", "eq_loo"))   # 참값 0
            assert (r["n_t"], r["n_f"]) == (2, 0)
    r = tol_cell_ref(rs4, 0, 0)
    assert abs(r["eq_loo"] - 0.2) <= r["eq_loo_bound"] and abs(r["eq"] - 0.0125) <= r["eq_bound"]


# ---------------------------------------------------------------------------
# 실데이터
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_table(real_lut):
    """[r6] 기본 l_bin_checks=None -> 중점 파일 값(5.1)이 앵커 2개 bin 의 외부 값으로 들어간 표."""
    return tol_v_table(new_memo(real_lut), "pmos", 1000)


@pytest.fixture(scope="module")
def real_table_noext(real_lut):
    """l_bin_checks=() (외부 값 없음 -- r5 기본 동작)."""
    return tol_v_table(new_memo(real_lut), "pmos", 1000, ())


def l_loo_rows(anchor_bin):
    """[r4] L 방향 LOO 를 만드는 앵커 i 집합(5절 'L 축 규칙'): 0 < i < n−1 이고 앵커 i−1·i·i+1 의 bin 이 같다.
    anchor_bin 은 test 쪽에서 독립으로 정한 앵커별 bin 표시(ngspice showmod 또는 toy 모델 파일 손계산)."""
    if not anchor_bin:
        return frozenset()
    n = len(anchor_bin)
    return frozenset(i for i in range(1, n - 1) if anchor_bin[i - 1] == anchor_bin[i] == anchor_bin[i + 1])


@pytest.fixture(scope="module")
def real_pmos_anchor_bin(real_lut, ngspice_bins):
    """pmos w_key 1000 앵커별 bin 표시 -- ngspice showmod 로 정한 bin(엔진 지도 미사용)."""
    sl = real_lut.slice_map[("pmos", 1000)]
    b = ngspice_bins.query("pfet_01v8", [(um(sl.w_m), um(L)) for L in sl.grids[0]])
    uniq = sorted(set(b))
    return tuple(uniq.index(x) for x in b)


@pytest.fixture(scope="module")
def real_pmos_l_rows(real_pmos_anchor_bin):
    return l_loo_rows(real_pmos_anchor_bin)


@pytest.fixture(scope="module")
def real_mid_ext(raw_slice, raw_mid, real_pmos_anchor_bin):
    """[r6] 5.1 의 pmos w_key 1000 외부 값 독립 계산: 중점 0.165 µm 를 감싸는 앵커 2개 bin(showmod 로 정한 bin 표시)의 앵커 쌍.
    반환 {앵커 index: (inv[k], eq[k])} -- 그 bin 두 앵커 행에 들어갈 VDS 별 값."""
    z = raw_slice("pmos", 1000)
    Lg = [float(x) for x in z["L"]]
    ab = real_pmos_anchor_bin
    out = {}
    for m, Lm in enumerate(float(x) for x in raw_mid["L"]):
        if any(abs(Lm - a) <= math.ulp(a) for a in Lg) or not (Lg[0] < Lm < Lg[-1]):
            continue
        k = bisect.bisect_right(Lg, Lm)
        i0, i1 = k - 1, k
        if ab[i0] != ab[i1] or ab.count(ab[i0]) != 2:
            continue                                     # 감싸는 쌍이 같은 bin 이고 그 bin 의 앵커가 정확히 2개일 때만(5.1 1~6)
        ref = midpoint_ref(z, raw_mid, "_p", m, i0, i1)
        out[i0] = out[i1] = (ref["inv"], ref["eq"], ref["inv_bound"], ref["eq_bound"])
    return out


@pytest.fixture(scope="module")
def real_ref_cells(raw_slice, real_pmos_anchor_bin, real_mid_ext):
    """pmos w_key 1000 전 셀 독립 계산(역산 근 포함). L 방향 LOO 앵커는 ngspice showmod 로 정한 bin 에서.
    [r6] 앵커 2개 bin 행에는 5.1 독립 외부 값(VDS 별)을 정의된 환산 후 셀 값과의 최댓값으로 넣는다(5절, 환산 없음)."""
    z = raw_slice("pmos", 1000)
    rs = RefSlice(z)
    cells = [[tol_cell_ref(rs, i, k, real_pmos_anchor_bin) for k in range(len(z["VDS"]))] for i in range(len(z["L"]))]
    for i, (inv, eq, invb, eqb) in real_mid_ext.items():
        for k, r in enumerate(cells[i]):
            for key, ext, eb in (("inv", inv[k], invb[k]), ("eq", eq[k], eqb[k])):
                if r[key] is not None and ext is not None and ext > r[key]:
                    r[key] = ext
                    r[key + "_bound"] = eb
    return cells


@pytest.mark.lut_realdata
def test_real_l_rows_are_contract_anchors(real_pmos_l_rows, real_pmos_anchor_bin):
    """[r6] CONTRACT 5절 r6 실측 bin 상태: .25 (앵커 2·3·4)·.24 (5~9) computed -> 내부 앵커 3·6·7·8(0.2·0.3·0.35·0.425 µm).
    .26 (0·1)·.23·.22·.21 은 앵커 2개, .20·.19 는 1개."""
    assert real_pmos_l_rows == frozenset({3, 6, 7, 8})
    sizes = [real_pmos_anchor_bin.count(b) for b in sorted(set(real_pmos_anchor_bin))]
    assert sizes == [2, 3, 5, 2, 2, 2, 1, 1]


@pytest.mark.lut_realdata
def test_real_table_totals_match_independent(real_table, real_ref_cells, real_pmos_l_rows):
    """[r5] 셀 최댓값은 유도 상한 안에서 같고, 시도·실패 합계는 정확히(독립 구현 값 -- [r6] LUT v2 는 옛 실측 779,455 (67,164) 와 다르다).
    [r6] 셀 값에는 중점 외부 값(.26 행)이 들어 있다(독립 5.1 구현)."""
    t = real_table
    assert all((t.l_loo[i] == "in_bin_interior") == (i in real_pmos_l_rows) for i in range(len(t.L_anchors)))
    for key, attr in (("inv", "gm_id_inverse_v"), ("eq", "id_equivalent_v"),
                      ("inv_loo", "gm_id_inverse_loo_v"), ("eq_loo", "id_equivalent_loo_v")):
        refs = [r for row in real_ref_cells for r in row if r[key] is not None]
        got = max(getattr(c, attr) for row in t.cells for c in row if getattr(c, attr) is not None)
        exp = max(r[key] for r in refs)
        bnd = max(r[key + "_bound" if key in ("inv", "eq") else key.replace("_loo", "_loo_bound")] for r in refs)
        assert abs(got - exp) <= bnd, (key, got, exp, bnd)
        print("pmos 1000 셀 최댓값 %s = %.17g (독립 %.17g)" % (key, got, exp))
    n_t = sum(c.n_targets for row in t.cells for c in row)
    n_f = sum(c.n_inverse_failed for row in t.cells for c in row)
    assert (n_t, n_f) == (sum(r["n_t"] for row in real_ref_cells for r in row),
                          sum(r["n_f"] for row in real_ref_cells for r in row))
    print("pmos 1000 역산 시도 %d (실패 %d)" % (n_t, n_f))


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
    assert len(defined) == 18 * 48 == nL * (nV - 1)              # [r6] 18 앵커 × 48 VDS (VDS = 0 열은 ID 0)
    assert all(t.cells[i][0] == TolVCell(None, None, 0, 0) for i in range(nL))
    assert all(t.cells[i][-1].gm_id_inverse_v is not None for i in range(nL))
    assert tuple(tuple(r) for r in t.loo_orders) == LOO_ORDERS_EXPECTED


@pytest.mark.lut_realdata
def test_real_all_cells_match_independent(real_table, real_ref_cells):
    """전 셀(18 × 49): n_targets·n_inverse_failed 정확히, 네 값(환산 후·환산 전) -- 허용 차는 `_cell_matches`."""
    n_t = n_f = 0
    for i, row in enumerate(real_ref_cells):
        for k, ref in enumerate(row):
            c = real_table.cells[i][k]
            try:
                _cell_matches(c, ref)
            except AssertionError as e:
                raise AssertionError("cell (%d, %d): %s" % (i, k, e))
            n_t += c.n_targets
            n_f += c.n_inverse_failed
    print("pmos w_key 1000 역산 시도 %d (실패 %d)" % (n_t, n_f))


@pytest.mark.lut_realdata
def test_real_scaled_values_are_loo_over_two_pow_p(real_table_noext):
    """환산 후 ≤ 환산 전 / 2^p_min(= /4) 이고 ≥ 환산 전 / 2^p_max(id_equivalent /16, gm_id_inverse /8) -- 셀 최댓값의 범위 성질.
    [r6] 외부 값은 환산 후 값에만 들어가므로(5절) 이 성질은 외부 값 없는 표(l_bin_checks=())에서 본다."""
    for row in real_table_noext.cells:
        for c in row:
            if c.id_equivalent_v is not None:
                assert c.id_equivalent_loo_v / 16 <= c.id_equivalent_v <= c.id_equivalent_loo_v / 4   # 2^p 나눔은 정확
            if c.gm_id_inverse_v is not None:
                assert c.gm_id_inverse_loo_v / 8 <= c.gm_id_inverse_v <= c.gm_id_inverse_loo_v / 4


@pytest.mark.lut_realdata
def test_real_default_external_equals_explicit_midpoint_rows(real_lut, real_table, real_table_noext, real_mid_ext):
    """[r6] 5절: 기본 l_bin_checks=None = midpoint_l_bin_checks(...).rows 의 (model, gm_id_inverse_v, id_equivalent_v).
    명시해 준 표와 같은 객체(memo 키 = 정규화 형식)이고, 외부 값 없는 표와는 중점이 든 앵커 2개 bin 의 행만 다르다.
    [2026-10-08 중점 변경] 그 행 = showmod 로 정한 앵커 2개 bin 중 중점을 감싸는 것(oracle (a) `real_mid_ext`) =
    .26 (0, 1)·.23 (10, 11)·.22 (12, 13)·.21 (14, 15) -- 18점 격자 index(승인 L 파일 순서)."""
    m = new_memo(real_lut)
    rows = midpoint_l_bin_checks(m, "pmos", 1000).rows
    assert len(rows) == 4
    explicit = tuple((r.model, r.gm_id_inverse_v, r.id_equivalent_v) for r in rows)
    t_def = tol_v_table(m, "pmos", 1000)
    assert tol_v_table(m, "pmos", 1000, explicit) is t_def
    assert tuple(t_def.l_bin_checks) == tuple((mo, tuple(a), tuple(b)) for mo, a, b in explicit)
    st = {mo: idx for mo, idx, _ in real_table.l_loo_bins}
    ext_rows = set(i for r in rows for i in st[r.model])
    assert ext_rows == set(real_mid_ext)
    assert ext_rows == {0, 1, 10, 11, 12, 13, 14, 15}
    for i in range(len(real_table.cells)):
        for k in range(len(real_table.cells[i])):
            if i not in ext_rows:
                assert real_table.cells[i][k] == real_table_noext.cells[i][k]
    assert any(real_table.cells[i][k] != real_table_noext.cells[i][k] for i in ext_rows for k in range(49))


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


@pytest.mark.lut_realdata
def test_real_external_l_values_not_converted(real_lut, real_table, real_table_noext):
    """5절 [r5]: 외부 L 값(l_bin_checks)은 환산하지 않고 환산 후 셀 값과의 최댓값에만 들어가며 환산 전 필드에는 안 들어간다.
    [r6] 비교 기준 = 외부 값 없는 표(l_bin_checks=()) -- 기본 표는 앵커 2개 bin 모두에 중점 값이 들어 있어([2026-10-08])
    missing_external bin 은 외부 값 없는 표에서 고른다."""
    st = dict((m, (idx, s)) for m, idx, s in real_table_noext.l_loo_bins)
    model, (idx, s) = next((m, v) for m, v in st.items() if v[1] == "missing_external")
    ext = 0.5                                       # 셀 값보다 큰 외부 값(V) -- 환산되면 0.5/4 등으로 보일 것
    t2 = tol_v_table(new_memo(real_lut), "pmos", 1000, l_bin_checks=((model, ext, ext),))
    n = 0
    for i in range(len(t2.cells)):
        for k, c2 in enumerate(t2.cells[i]):
            c1 = real_table_noext.cells[i][k]
            assert (c2.n_targets, c2.n_inverse_failed) == (c1.n_targets, c1.n_inverse_failed)
            assert (c2.gm_id_inverse_loo_v, c2.id_equivalent_loo_v) == (c1.gm_id_inverse_loo_v, c1.id_equivalent_loo_v)
            for attr in ("gm_id_inverse_v", "id_equivalent_v"):
                v1, v2 = getattr(c1, attr), getattr(c2, attr)
                if i in idx and v1 is not None:
                    assert v2 == max(v1, ext), (i, k, attr)
                    n += 1
                else:
                    assert v2 == v1
    assert n > 0
    assert dict((m, s2) for m, _, s2 in t2.l_loo_bins)[model] == "external"


@pytest.mark.lut_realdata
def test_real_l_rows_cells_match_independent(real_table, real_ref_cells, real_pmos_l_rows, raw_slice):
    """L 방향 LOO 가 들어가는 행([r6] 0.2·0.3·0.35·0.425 µm)의 모든 VDS 셀 -- 독립 구현과 유도 상한 안에서 같다.
    판별: 그 행의 시도 수는 L 방향 없는 독립 계산보다 많다(L 방향 몫이 실제로 들어갔다)."""
    assert real_pmos_l_rows == frozenset({3, 6, 7, 8})
    rs = RefSlice(raw_slice("pmos", 1000))
    for i in sorted(real_pmos_l_rows):
        for k, ref in enumerate(real_ref_cells[i]):
            _cell_matches(real_table.cells[i][k], ref)
        no_l = tol_cell_ref(rs, i, 24, None, with_roots=False)
        assert real_table.cells[i][24].n_targets > no_l["n_t"]


@pytest.mark.lut_realdata
def test_real_statuses_match_ngspice_bins(real_table, real_table_noext, real_lut, ngspice_bins, raw_mid):
    """앵커·bin 상태: 앵커 bin 을 showmod 로 묶어 앵커 수로 정한다(3개 이상 computed, 2개 missing_external, 1개 single_point).
    [r6] 기본 표(중점 외부 값): 앵커 2개 bin 중 중점 파일의 L 이 두 앵커 사이에 있는 bin 만 external.
    [2026-10-08 중점 변경, CONTRACT 8절] 중점 0.165·0.85·1.75·3.25 µm -> .26·.23·.22·.21 모두 external, missing_external 없음.
    외부 값 없는 표는 r5 와 같다(앵커 2개 bin 모두 missing_external)."""
    sl = real_lut.slice_map[("pmos", 1000)]
    Lg = [float(x) for x in sl.grids[0]]
    mids = [float(x) for x in raw_mid["L"]]
    b = ngspice_bins.query("pfet_01v8", [(um(sl.w_m), um(L)) for L in sl.grids[0]])
    names = parse_model_bins(ngspice_bins.pm3("pfet_01v8"))
    groups = []
    for i, g in enumerate(b):
        if groups and same_bounds(groups[-1][0], g):
            groups[-1][1].append(i)
        else:
            groups.append((g, [i]))
    for table, use_mid in ((real_table_noext, False), (real_table, True)):
        exp_bins, exp_loo = [], [None] * len(b)
        for g, idx in groups:
            name = [n for n, bnd in names.items() if same_bounds(bnd, g)]
            assert len(name) == 1
            st = "computed" if len(idx) >= 3 else ("missing_external" if len(idx) == 2 else "single_point")
            if st == "missing_external" and use_mid and any(Lg[idx[0]] < m < Lg[idx[1]] for m in mids):
                st = "external"
            exp_bins.append((name[0], tuple(idx), st))
            for j, i in enumerate(idx):
                exp_loo[i] = ({"missing_external": "bin_missing_external", "external": "bin_external",
                               "single_point": "bin_single_point"}.get(st)
                              or ("bin_edge" if j in (0, len(idx) - 1) else "in_bin_interior"))
        assert tuple(table.l_loo_bins) == tuple(exp_bins), use_mid
        assert tuple(table.l_loo) == tuple(exp_loo), use_mid
    ext = sorted(m.rsplit(".", 1)[1] for m, _, s in real_table.l_loo_bins if s == "external")
    assert ext == ["21", "22", "23", "26"]                                   # (d) CONTRACT 8절
    assert [m for m, _, s in real_table.l_loo_bins if s == "missing_external"] == []
    assert sorted(m.rsplit(".", 1)[1] for m, _, s in real_table_noext.l_loo_bins
                  if s == "missing_external") == ["21", "22", "23", "26"]


@pytest.mark.lut_realdata
def test_real_at_in_bin_and_cross_bin(real_table):
    t = real_table
    La = list(t.L_anchors)
    i0 = min(range(len(La)), key=lambda i: abs(La[i] - 0.35e-6))
    assert abs(La[i0] - 0.35e-6) <= math.ulp(0.35e-6) and abs(La[i0 + 1] - 0.425e-6) <= math.ulp(0.425e-6)
    L = 0.5 * (La[i0] + La[i0 + 1])                     # 0.3875 µm, 같은 bin 0.35·0.425 ([r6] 앵커 7·8)
    for metric, attr in (("gm_id_inverse", "gm_id_inverse_v"), ("id_equivalent", "id_equivalent_v")):
        vals = [getattr(t.cells[i][k], attr) for i in (i0, i0 + 1) for k in (24, 25)]
        vals = [v for v in vals if v is not None]
        assert t.at(L, 0.9, metric) == max(vals)
    with pytest.raises(SealViolationError) as ei:
        t.at(0.6e-6, 0.9, "gm_id_inverse")                # 0.5(bin .24)·0.7(bin .23) 사이, bin (0.5, 1] 앵커 2개
    det = detail_of(ei.value)
    assert det["reason"] == "lut_l_cross_bin" and det["table"] == "tol_v" and det["w_key"] == 1000


# ---------------------------------------------------------------------------
# [r4] 같은 bin 안 L 방향 LOO (5절 'L 축 규칙'), 상태, 외부 l_bin_checks, at() 의 L 위치(4.0) -- bin toy
#   [r5] 셀 값 기대값은 r5 독립 구현(tol_cell_ref, L 축 선형·VGS/VDS Hermite·Richardson)으로 바꿨다.
# ---------------------------------------------------------------------------

BIN_TOY_L_LOO_LO = ("bin_edge", "in_bin_interior", "bin_edge", "bin_missing_external", "bin_missing_external",
                    "bin_missing_external", "bin_missing_external", "bin_single_point")
BIN_TOY_L_LOO_BINS_LO = (("toyn__model.0", (0, 1, 2), "computed"), ("toyn__model.1", (3, 4), "missing_external"),
                         ("toyn__model.3", (5, 6), "missing_external"), ("toyn__model.4", (7,), "single_point"))


def _assert_table_matches_ref(t, z, anchor_bin):
    rs = RefSlice(z)
    for i in range(len(z["L"])):
        for k in range(len(z["VDS"])):
            _cell_matches(t.cells[i][k], tol_cell_ref(rs, i, k, anchor_bin))


def test_bin_toy_cells_match_independent(bin_toy, bin_memo):
    t = tol_v_table(bin_memo, "nmos", 100)
    assert l_loo_rows(BIN_ANCHOR_BIN_LO) == frozenset({1})
    _assert_table_matches_ref(t, bin_toy_raw(), BIN_ANCHOR_BIN_LO)
    for k in range(2):
        assert t.cells[1][k].n_targets == 8                 # VS 2 × (VGS 축 목표 1 + L 축 목표 3)
        for i in (0, 2, 3, 7):
            assert t.cells[i][k].n_targets == 2
    assert t.l_bins == bin_toy.slice_map[("nmos", 100)].l_bins
    assert tuple(t.l_loo) == BIN_TOY_L_LOO_LO
    assert tuple(t.l_loo_bins) == BIN_TOY_L_LOO_BINS_LO


def test_bin_toy_l_direction_hand_value(bin_toy_build):
    """[r5] L 방향 LOO 손계산(기울기 자료가 맞는 bin toy -- VGS Hermite LOO 는 2차식 정확이라 0, L 방향만 남는다):
    앵커 1.5 µm 행 ln ID 의 L 방향 선형 LOO 오차 = |½(ln 1 + ln ½) − ln(1/1.5)| (VGS 몫 c(L)·q(v) 는 L 에 선형이라 정확),
    gm/ID 최소 = c(1.5)·8 = 1.15·8 -> 환산 전 그 값, 환산 후 /4 (L 축 linear p 2)."""
    m = new_memo(bin_toy_build("bt_cons", consistent=True).load())
    t = tol_v_table(m, "nmos", 100)
    hand = abs(0.5 * math.log(0.5) + math.log(1.5)) / (8.0 * 1.15)
    z = bin_toy_raw(consistent=True)
    rs = RefSlice(z)
    for k in range(2):
        ref = tol_cell_ref(rs, 1, k, BIN_ANCHOR_BIN_LO)
        _cell_matches(t.cells[1][k], ref)
        assert abs(ref["eq_loo"] - hand) <= ref["eq_loo_bound"]
        assert abs(t.cells[1][k].id_equivalent_loo_v - hand) <= 2 * ref["eq_loo_bound"]
        assert t.cells[1][k].id_equivalent_v == t.cells[1][k].id_equivalent_loo_v / 4
        # L 방향 몫이 없는 행은 0 수준(판별: 같은 자료에서 L 방향 몫만 hand 를 만든다)
        for i in (0, 2):
            r0 = tol_cell_ref(rs, i, k, BIN_ANCHOR_BIN_LO)
            assert t.cells[i][k].id_equivalent_loo_v <= 2 * r0["eq_loo_bound"] < hand


def test_bin_toy_upper_width_rows(bin_toy, bin_memo):
    """폭 2e-6 슬라이스(위 W 범위: A' [1, 4]·D' (4, 10]): L 방향 LOO 앵커 = 1·2·3·6."""
    t = tol_v_table(bin_memo, "nmos", 200)
    rows = l_loo_rows(BIN_ANCHOR_BIN_HI)
    assert rows == frozenset({1, 2, 3, 6})
    _assert_table_matches_ref(t, bin_toy_raw(2.0, 2e-6), BIN_ANCHOR_BIN_HI)
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
            # [r5] 외부 값은 환산 전 필드에 들어가지 않는다
            assert (c.gm_id_inverse_loo_v, c.id_equivalent_loo_v) == (b.gm_id_inverse_loo_v, b.id_equivalent_loo_v)
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


# ---------------------------------------------------------------------------
# [r5] 환산 검증: ngspice 칸 중앙 표본 (CONTRACT 5절 '환산 검증 test', 실데이터 마커)
#   판정(오케스트레이터 결정): 표본 점마다 e ≤ 그 셀 tol(at(L, vds, "id_equivalent")) -- tol 은 실제 오차의 상한.
#   e / tol 분포와 LOO/2^4 대비 칸 중앙 오차의 비는 기록만 한다(계약 (b) 의 비 0.5~2 하한·상한 판정은 채택하지 않음).
#   (c) 같은 넷리스트를 격자점에서 돌린 값 = LUT 값(설정 동일성).
# ---------------------------------------------------------------------------

NGSPICE_DEFAULT = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
SAMPLE_L_UM = (0.15, 0.35, 1.0, 4.0)
SAMPLE_VS_INDEX = (0, 2)
DEVCELL = {"nmos": ("nfet_01v8", +1, -1), "pmos": ("pfet_01v8", -1, +1)}     # (cell, 극성, 바디 부호) -- 슬라이스 생성기와 같음
QUANTS = ("id", "gm", "gds", "vth")
GEN_GRID_TOL_V = None          # 슬라이스 생성기(manifest 폴더의 manifest["generator"])의 GRID_TOL_V 를 읽어 채운다


_GEN_SEARCH = (r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\engine\lut_slices",)   # 계약 8절의 슬라이스 생성기 위치


def _load_generator_grid_tol(manifest_path):
    """스윕 전압 검사 허용 = 슬라이스 생성기 선언 GRID_TOL_V(근거 하나 -- 값을 옮겨 적지 않는다).
    [r6] LUT v2 manifest 폴더(git 밖 데이터 폴더)에는 생성기가 없다 -> manifest 폴더, GMID_LUT_GENERATOR_DIR, 계약 8절 위치 순으로
    찾되 **manifest 의 generator_sha256 과 같은 파일만** 쓴다(다른 판의 생성기로 바꿔 읽지 않는다)."""
    global GEN_GRID_TOL_V
    with open(manifest_path, encoding="utf-8") as f:
        man = json.load(f)
    gen, gsha = man["generator"], man["generator_sha256"]
    dirs = [os.path.dirname(manifest_path)] + [d for d in (os.environ.get("GMID_LUT_GENERATOR_DIR"),) if d]
    dirs += list(_GEN_SEARCH)
    cands = [os.path.join(d, gen) for d in dirs if os.path.isfile(os.path.join(d, gen))]
    hit = [p for p in cands if sha256_file(p) == gsha]
    if not hit:
        pytest.fail("manifest generator_sha256 %s 와 같은 슬라이스 생성기 %s 를 찾지 못함(후보 %r)" % (gsha, gen, cands),
                    pytrace=False)
    src = open(hit[0], encoding="utf-8").read()
    m = re.search(r"^GRID_TOL_V\s*=\s*([0-9.eE+-]+)", src, re.M)
    assert m, "생성기에 GRID_TOL_V 없음"
    GEN_GRID_TOL_V = float(m.group(1))


def _ngspice():
    p = os.environ.get("GMID_NGSPICE", NGSPICE_DEFAULT)
    if not os.path.isfile(p):
        p = shutil.which("ngspice_con") or ""
    if not p:
        pytest.fail("ngspice_con 없음 (GMID_NGSPICE=%r) -- 실데이터 test 는 skip 하지 않는다" % NGSPICE_DEFAULT, pytrace=False)
    return p


def _read_raw(path):
    b = open(path, "rb").read()
    i = b.index(b"Binary:\n")
    hdr = b[:i].decode("latin1").splitlines()
    nv = npt = None
    names, invars = [], False
    for ln in hdr:
        if ln.startswith("No. Variables:"):
            nv = int(ln.split(":")[1])
        elif ln.startswith("No. Points:"):
            npt = int(ln.split(":")[1])
        elif ln.startswith("Variables:"):
            invars = True
        elif invars and ln.strip():
            names.append(ln.split()[1])
    a = np.frombuffer(b[i + 8:], dtype="<f8", count=nv * npt).reshape(npt, nv)
    out = {}
    for k, n in enumerate(names):
        mm = re.search(r"\[(\w+)\]", n)
        out[mm.group(1) if mm else n] = a[:, k]
    return out


def _netlist(meta, cell, pol, body_sign, w_um, l_um, vs_list, sweeps, workdir, stem):
    """슬라이스 생성기 build_netlist 와 같은 소자·기하·극성·바디 부호. sweeps = [(tag, vds_start, vds_stop, vds_step,
    vgs_start, vgs_stop, vgs_step)] (크기, 극성은 여기서 곱함)."""
    inst = "@m.xdut.msky130_fd_pr__%s" % cell
    ad, pd = w_um * 0.5, w_um + 2.0
    lines = ["* r5 tol_V cell-midpoint sample %s W=%gum L=%gum" % (cell, w_um, l_um)]
    for rel in meta["model_files_sha256"]:
        if rel.endswith(".spice"):
            lines.append('.include "%s"' % os.path.join(meta["pdk_root"], rel).replace("\\", "/"))
    lines += ["vgs g 0 dc 0", "vds d 0 dc 0", "vb b 0 dc 0",
              "xdut d g 0 b sky130_fd_pr__%s l=%su w=%su ad=%sp as=%sp pd=%su ps=%su nf=1"
              % (cell, repr(l_um), repr(w_um), "%.6g" % ad, "%.6g" % ad, "%.6g" % pd, "%.6g" % pd),
              ".save v(g) v(d) " + " ".join("%s[%s]" % (inst, q) for q in QUANTS),
              ".control", "set filetype=binary"]
    raws = []
    for si, vs in vs_list:
        vb = round(body_sign * vs, 9) + 0.0
        lines.append("alter vb dc = %.9g" % vb)
        for tag, d0, d1, ds, g0, g1, gs in sweeps:
            lines.append("dc vds %.12g %.12g %.12g vgs %.12g %.12g %.12g"
                         % (pol * d0, pol * d1, pol * ds, pol * g0, pol * g1, pol * gs))
            rp = os.path.join(workdir, "%s_vs%d_%s.raw" % (stem, si, tag)).replace(os.sep, "/")
            lines.append("write %s" % rp)
            raws.append((si, tag, rp))
    lines += ["quit", ".endc", ".end"]
    return "\n".join(lines) + "\n", raws


def _run_spice(z, kind, iL, workdir):
    """(kind, L 앵커 iL) 하나: VS 표본마다 세 스윕(VGS 칸 중앙 / VDS 칸 중앙 / 격자점) -> {(si, tag): {q: [vgs, vds]}}."""
    cell, pol, body = DEVCELL[kind]
    meta = json.loads(str(z["meta_json"]))
    VGS, VDS, VS = (np.asarray(z[a], dtype=float) for a in ("VGS", "VDS", "VS"))
    hg, hd = float(VGS[1] - VGS[0]), float(VDS[1] - VDS[0])
    # 균일 격자 확인 -- 허용 = 슬라이스 생성기의 GRID_TOL_V(dc 스윕 전압과 축 값의 허용 차, 생성기 선언값)
    assert np.abs(np.diff(VGS) - hg).max() <= GEN_GRID_TOL_V and np.abs(np.diff(VDS) - hd).max() <= GEN_GRID_TOL_V
    w_um = round(float(z["W"]) * 1e6, 6)
    l_um = round(float(z["L"][iL]) * 1e6, 6)
    sweeps = {"gmid": (VDS[0], VDS[-1], hd, VGS[0] + hg / 2, VGS[-1] - hg / 2, hg),
              "dmid": (VDS[0] + hd / 2, VDS[-1] - hd / 2, hd, VGS[0], VGS[-1], hg),
              "grid": (VDS[0], VDS[-1], hd, VGS[0], VGS[-1], hg)}
    axes = {"gmid": (VGS[:-1] + hg / 2, VDS), "dmid": (VGS, VDS[:-1] + hd / 2), "grid": (VGS, VDS)}
    stem = "%s_L%d" % (kind, iL)
    net, raws = _netlist(meta, cell, pol, body, w_um, l_um, [(si, float(VS[si])) for si in SAMPLE_VS_INDEX],
                         [(t,) + tuple(float(x) for x in v) for t, v in sweeps.items()], workdir, stem)
    cir = os.path.join(workdir, stem + ".cir")
    log = os.path.join(workdir, stem + ".log")
    with open(cir, "w") as f:
        f.write(net)
    with open(log, "w") as fo:
        subprocess.run([_ngspice(), "-b", cir], cwd=workdir, stdout=fo, stderr=subprocess.STDOUT, timeout=600, check=False)
    text = open(log, encoding="utf-8", errors="replace").read()
    bad = [ln for ln in text.splitlines() if re.search(r"\b(error|fatal)\b", ln, re.I)]
    assert not bad, "ngspice 오류 %s" % bad[:3]
    out = {}
    for si, tag, rp in raws:
        r = _read_raw(rp)
        gax, dax = axes[tag]
        g, d = r["v(g)"], r["v(d)"]
        assert g.size == len(gax) * len(dax), (tag, g.size)
        g, d = g.reshape(len(gax), len(dax)), d.reshape(len(gax), len(dax))       # 바깥 vgs, 안쪽 vds
        assert (np.abs(pol * g - gax[:, None]).max() <= GEN_GRID_TOL_V
                and np.abs(pol * d - dax[None, :]).max() <= GEN_GRID_TOL_V)
        out[(si, tag)] = {q: np.abs(r[q]).reshape(len(gax), len(dax)) for q in QUANTS}
    return out


@pytest.fixture(scope="module")
def spice_samples(real_lut, raw_slice, real_paths, tmp_path_factory):
    _load_generator_grid_tol(real_paths["manifest"])
    work = tmp_path_factory.mktemp("tolv_spice")
    res = {}
    for kind in ("nmos", "pmos"):
        z = raw_slice(kind, 1000)
        Lum = [round(float(x) * 1e6, 6) for x in z["L"]]
        for l_um in SAMPLE_L_UM:
            iL = Lum.index(l_um)
            res[(kind, iL)] = _run_spice(z, kind, iL, str(work))
    return res


def _peak_vgs(rs, iL, k, s):
    g = np.where(rs.on[iL, :, k, s], rs.gmid[iL, :, k, s], -np.inf)
    return rs.grids[1][int(np.argmax(g))]


@pytest.mark.lut_realdata
def test_ngspice_grid_rerun_equals_lut(spice_samples, raw_slice):
    """(c) 설정 동일성: 같은 넷리스트 격자점 스윕 = LUT ID·GM·GDS·VTH (계약 실측 '차 0' -- 비트 단위 동일)."""
    for (kind, iL), out in spice_samples.items():
        z = raw_slice(kind, 1000)
        for si in SAMPLE_VS_INDEX:
            sp = out[(si, "grid")]
            for q in QUANTS:
                lut = np.asarray(z[q.upper()][iL, :, :, si], dtype=float)
                assert np.array_equal(sp[q], lut), (kind, iL, si, q)


@pytest.mark.lut_realdata
def test_ngspice_cell_midpoint_error_bounded_by_cell_tol(spice_samples, real_lut, raw_slice, record_property):
    """(a) 강반전 분지(VGS ≥ 그 격자 곡선 정점)·VDS ≥ 2 격자칸의 VGS·VDS 칸 중앙 점마다
    e = |ln ID_op_point − ln ID_spice| / (GM/ID)_spice ≤ tol_v_table(...).at(L, vds, "id_equivalent")."""
    memo = new_memo(real_lut, 1 << 16)
    summary = {}
    violations = []
    n_wrong_rejected = {}
    for kind in ("nmos", "pmos"):
        z = raw_slice(kind, 1000)
        rs = RefSlice(z)
        t = tol_v_table(memo, kind, 1000)
        Lg, VGS, VDS, VS = rs.grids
        w_m = rs.w_m
        hg, hd = VGS[1] - VGS[0], VDS[1] - VDS[0]
        for tag in ("gmid", "dmid"):
            ratios, es, loo16 = [], [], []
            for (kk, iL), out in spice_samples.items():
                if kk != kind:
                    continue
                L = Lg[iL]
                for si in SAMPLE_VS_INDEX:
                    sp = out[(si, tag)]
                    vs = VS[si]
                    nGa, nDa = sp["id"].shape
                    for a in range(nGa):
                        for b in range(nDa):
                            if tag == "gmid":
                                vgs, vds = VGS[a] + hg / 2, VDS[b]
                                if b < 2 or vgs < _peak_vgs(rs, iL, b, si):
                                    continue
                            else:
                                vgs, vds = VGS[a], VDS[b] + hd / 2
                                if b < 2 or vgs < max(_peak_vgs(rs, iL, b, si), _peak_vgs(rs, iL, b + 1, si)):
                                    continue
                            I, G = float(sp["id"][a, b]), float(sp["gm"][a, b])
                            if not (I > 0 and G > 0):
                                continue
                            op = op_point(memo, kind, 1000, L, vgs, vds, vs)
                            e = abs(math.log(op.IDu * w_m / L) - math.log(I)) / (G / I)
                            tol = t.at(L, vds, "id_equivalent")
                            assert tol is not None, (kind, L, vds)
                            ratios.append(e / tol)
                            es.append(e)
                            if e > tol:
                                violations.append((kind, tag, L, vgs, vds, vs, e, tol))
                            if tag == "gmid":
                                # 음성 대조: 칸 중앙 대신 왼쪽 격자점 값(반 칸 어긋난 조회)이면 이 판정이 거부해야 한다
                                e_wrong = abs(float(rs.lI[iL, a, b, si]) - math.log(I)) / (G / I)
                                n_wrong_rejected[kind] = n_wrong_rejected.get(kind, 0) + (e_wrong > tol)
            if tag == "gmid":
                # (b) 기록용(판정 아님): 같은 곡선들의 VGS 축 Hermite LOO(간격 2h, 환산 전) / 2^4
                for (kk, iL), out in spice_samples.items():
                    if kk != kind:
                        continue
                    for si in SAMPLE_VS_INDEX:
                        for b in range(2, len(VDS)):
                            c = rs.lI[iL, :, b, si]
                            g = rs.gmid[iL, :, b, si]
                            pk = _peak_vgs(rs, iL, b, si)
                            for j in range(1, len(VGS) - 1):
                                if VGS[j] < pk or not rs.on[iL, j - 1:j + 2, b, si].all():
                                    continue
                                est = hermite_val(c[j - 1], c[j + 1], g[j - 1], g[j + 1], 2 * hg, 0.5)
                                loo16.append(abs(est - c[j]) / g[j] / 16.0)
            arr = np.asarray(ratios)
            rec = {"n": int(arr.size), "ratio_p50": float(np.percentile(arr, 50)), "ratio_p99": float(np.percentile(arr, 99)),
                   "ratio_max": float(arr.max()), "e_p50_V": float(np.percentile(es, 50)), "e_p99_V": float(np.percentile(es, 99))}
            if loo16:
                rec["vgs_loo_over_16_p50_V"] = float(np.percentile(loo16, 50))
                rec["vgs_loo_over_16_p99_V"] = float(np.percentile(loo16, 99))
            summary["%s_%s" % (kind, tag)] = rec
            assert arr.size > 1000, (kind, tag, arr.size)
    summary["wrong_lookup_rejected"] = n_wrong_rejected
    record_property("tolv_midpoint_summary", json.dumps(summary))
    print("tol_V 칸 중앙 표본 e/tol 분포: " + json.dumps(summary, indent=1))
    assert violations == [], "칸 중앙 오차가 셀 tol 을 넘음 %d점, 처음 5: %r" % (len(violations), violations[:5])
    assert all(n_wrong_rejected.get(k, 0) > 1000 for k in ("nmos", "pmos")), n_wrong_rejected
