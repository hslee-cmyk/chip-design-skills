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
from gmid_engine.lut import TOL_V_METRICS, TolVCell, TolVTable, op_point, tol_v_table

from .conftest import (TOY_L, TOY_VDS, RefSlice, detail_of, hermite_val, new_memo, r4_toy_slice_arrays, rel_close,
                       tol_cell_ref, toy_slice_arrays)

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


def _cell_matches(c, ref, rel=1e-9, abs_=1e-12):
    """id_equivalent: 상대 1e-9(닫힌 식 값). gm_id_inverse: 역산 근 차 절대 1e-8 V. 근거(실측): 정점 근처 평탄 목표에서
    근의 반올림 민감도 = 미분 반올림 / p'' 라, 미분 계산 경로가 다른(기저 함수 대 de Casteljau) 독립 bisection 과 환산 전
    최대 1.5e-9 V 차가 났다(pmos 1000 셀 (5, 14)). 셀 값(수십~수백 mV)보다 7자리 작다."""
    assert (c.n_targets, c.n_inverse_failed) == (ref["n_t"], ref["n_f"])
    for attr, key in FIELDS:
        got, exp = getattr(c, attr), ref[key]
        if exp is None:
            assert got is None, attr
        else:
            tol = max(abs_, rel * abs(exp)) if key.startswith("eq") else 1e-8
            assert got is not None and abs(got - exp) <= tol, (attr, got, exp)


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
            # 0 수준(부동소수): VGS 축 Hermite LOO 가 2차식을 정확히 재현, VDS·VS 축은 2점이라 내부점 없음
            for attr, _ in FIELDS:
                v = getattr(c, attr)
                assert v is not None and 0.0 <= v < 1e-12, (i, k, attr, v)
            assert (c.n_targets, c.n_inverse_failed) == (2, 0)
            _cell_matches(c, tol_cell_ref(rs, i, k))
    # 판별: 옛 선형 LOO 였다면 id_equivalent 환산 전 = |ln ID(0.5) 의 선형 추정 − 참값|/14 = 1.5/14
    assert rel_close(abs(0.5 * (0.0 + 14.0) - 8.5) / 14.0, 0.107, 2e-3)


def test_contract_toy_at(toy_memo):
    t = tol_v_table(toy_memo, "nmos", 100)
    for metric in TOL_V_METRICS:
        v = t.at(2e-6, 0.75, metric)
        assert v is not None and 0.0 <= v < 1e-12
        assert t.at(3e-6, 1.0, metric) < 1e-12
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
    assert rel_close(c.id_equivalent_loo_v, 0.2, 1e-12)
    assert rel_close(c.id_equivalent_v, 0.0125, 1e-12)
    rs = RefSlice(r4_toy_slice_arrays(1e-6))
    for i in range(3):
        for k in range(2):
            _cell_matches(t.cells[i][k], tol_cell_ref(rs, i, k))
    # gm_id_inverse 는 VGS 축(hermite_slope p 3) 하나뿐: 환산 후 = 환산 전 / 8, LOO 는 FC 검사로 거르지 않는다
    assert rel_close(c.gm_id_inverse_v, c.gm_id_inverse_loo_v / 8.0, 1e-12)
    assert c.gm_id_inverse_v > 0.01


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
    assert rel_close(c.id_equivalent_loo_v, 0.075 / 14.0, 1e-9)
    assert rel_close(c.id_equivalent_v, 0.075 / 14.0 / 4.0, 1e-9)
    # 같은 셀의 L 1 행(GDS 정상)은 Hermite 라 0 수준 -- 폴백이 없으면 이 값이 된다(판별)
    assert t.cells[1][1].id_equivalent_loo_v < 1e-12


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
            assert all(r[key] < 1e-12 for key in ("inv", "eq", "inv_loo", "eq_loo")) and (r["n_t"], r["n_f"]) == (2, 0)
    r = tol_cell_ref(rs4, 0, 0)
    assert rel_close(r["eq_loo"], 0.2, 1e-12) and rel_close(r["eq"], 0.0125, 1e-12)


# ---------------------------------------------------------------------------
# 실데이터
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_table(real_lut):
    return tol_v_table(new_memo(real_lut), "pmos", 1000)


@pytest.fixture(scope="module")
def real_ref_cells(real_lut, raw_slice):
    """pmos w_key 1000 전 셀 독립 계산(역산 근 포함 -- 약 1분)."""
    z = raw_slice("pmos", 1000)
    rs = RefSlice(z)
    ab = tuple(real_lut.slice_map[("pmos", 1000)].l_bins.anchor_bin)
    return [[tol_cell_ref(rs, i, k, ab) for k in range(len(z["VDS"]))] for i in range(len(z["L"]))]


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
    assert len(defined) == 576                                   # 12 앵커 × 48 VDS (VDS = 0 열은 ID 0)
    assert all(t.cells[i][0] == TolVCell(None, None, 0, 0) for i in range(nL))
    assert all(t.cells[i][-1].gm_id_inverse_v is not None for i in range(nL))
    assert tuple(tuple(r) for r in t.loo_orders) == LOO_ORDERS_EXPECTED


@pytest.mark.lut_realdata
def test_real_all_cells_match_independent(real_table, real_ref_cells):
    """전 셀(12 × 49): n_targets·n_inverse_failed 정확히, 네 값(환산 후·환산 전) -- 허용 차는 `_cell_matches`."""
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
def test_real_scaled_values_are_loo_over_two_pow_p(real_table):
    """환산 후 ≤ 환산 전 / 2^p_min(= /4) 이고 ≥ 환산 전 / 2^p_max(id_equivalent /16, gm_id_inverse /8) -- 셀 최댓값의 범위 성질."""
    for row in real_table.cells:
        for c in row:
            if c.id_equivalent_v is not None:
                assert c.id_equivalent_loo_v / 16 * (1 - 1e-12) <= c.id_equivalent_v <= c.id_equivalent_loo_v / 4 * (1 + 1e-12)
            if c.gm_id_inverse_v is not None:
                assert c.gm_id_inverse_loo_v / 8 * (1 - 1e-12) <= c.gm_id_inverse_v <= c.gm_id_inverse_loo_v / 4 * (1 + 1e-12)


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
def test_real_external_l_values_not_converted(real_lut, real_table):
    """5절 [r5]: 외부 L 값(l_bin_checks)은 환산하지 않고 환산 후 셀 값과의 최댓값에만 들어가며 환산 전 필드에는 안 들어간다."""
    st = dict((m, (idx, s)) for m, idx, s in real_table.l_loo_bins)
    model, (idx, s) = next((m, v) for m, v in st.items() if v[1] == "missing_external")
    ext = 0.5                                       # 셀 값보다 큰 외부 값(V) -- 환산되면 0.5/4 등으로 보일 것
    t2 = tol_v_table(new_memo(real_lut), "pmos", 1000, l_bin_checks=((model, ext, ext),))
    n = 0
    for i in range(len(t2.cells)):
        for k, c2 in enumerate(t2.cells[i]):
            c1 = real_table.cells[i][k]
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
    assert np.allclose(np.diff(VGS), hg, atol=1e-12) and np.allclose(np.diff(VDS), hd, atol=1e-12)
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
        assert np.abs(pol * g - gax[:, None]).max() <= 1e-9 and np.abs(pol * d - dax[None, :]).max() <= 1e-9
        out[(si, tag)] = {q: np.abs(r[q]).reshape(len(gax), len(dax)) for q in QUANTS}
    return out


@pytest.fixture(scope="module")
def spice_samples(real_lut, raw_slice, tmp_path_factory):
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
    """(c) 설정 동일성: 같은 넷리스트 격자점 스윕 = LUT ID·GM·GDS·VTH."""
    worst = 0.0
    for (kind, iL), out in spice_samples.items():
        z = raw_slice(kind, 1000)
        for si in SAMPLE_VS_INDEX:
            sp = out[(si, "grid")]
            for q in QUANTS:
                lut = np.asarray(z[q.upper()][iL, :, :, si], dtype=float)
                d = np.abs(sp[q] - lut) / np.maximum(np.abs(lut), 1e-300)
                worst = max(worst, float(d[lut != 0].max()))
                assert np.array_equal(sp[q], lut) or float(d[lut != 0].max()) <= 1e-12, (kind, iL, si, q)
    print("격자점 재실행 최대 상대차 %.3g" % worst)


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
