"""`load_lut_set` -- CONTRACT 1.4: LutSet 구성·불변식·용량 기준 폭 w_ref_m·로드 거부 사유(1.3 전부 + 8종).

거부 test 는 toy 임시 사본을 고쳐 만든다(manifest sha256 은 고친 파일로 다시 잰다 -- sha 불일치는 test_provenance).
"""
import json

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import CapTable, DcSlice, LutSet, LutSpec

from .conftest import (TOY_L, TOY_SPEC, TOY_VDS, TOY_VGS, TOY_VS, curve_cap_arrays, curve_slice_arrays, detail_of,
                       rel_close,
                       standard_toy_slices, toy_cap_arrays, toy_slice_arrays)


def _reject(build, spec=TOY_SPEC):
    with pytest.raises(SchemaRejectedError) as ei:
        build.load(spec)
    return detail_of(ei.value)


# ---------------------------------------------------------------------------
# 구성
# ---------------------------------------------------------------------------

def test_toy_structure(toy):
    assert isinstance(toy, LutSet)
    assert toy.spec == TOY_SPEC
    assert set(toy.slice_map) == {("nmos", 100), ("nmos", 200)}
    with pytest.raises(TypeError):
        toy.slice_map[("nmos", 300)] = None
    assert set(toy.cap_map) == {"nmos"}
    sl = toy.slice_map[("nmos", 100)]
    assert isinstance(sl, DcSlice)
    assert (sl.kind, sl.w_key) == ("nmos", 100)
    assert rel_close(sl.w_m, 1e-6, 1e-15)
    assert sl.grids == (TOY_L, TOY_VGS, TOY_VDS, TOY_VS)
    assert all(isinstance(x, float) for g in sl.grids for x in g)
    a = toy_slice_arrays(1e-6)
    np.testing.assert_array_equal(np.asarray(sl.ID), a["ID"])
    np.testing.assert_array_equal(np.asarray(sl.VTH), a["VTH"])
    for name in ("ID", "VTH", "on_mask", "log_ID", "log_GM", "log_GDS"):
        arr = getattr(sl, name)
        with pytest.raises(ValueError):
            arr[0, 0, 0, 0] = arr[0, 0, 0, 0]
    np.testing.assert_array_equal(np.asarray(sl.log_ID), np.log(a["ID"]))
    np.testing.assert_array_equal(np.asarray(sl.log_GM), np.log(a["GM"]))
    np.testing.assert_array_equal(np.asarray(sl.log_GDS), np.log(a["GDS"]))
    assert np.asarray(sl.on_mask).all()


# ---------------------------------------------------------------------------
# [r5] Hermite 보조 필드 (CONTRACT 1.4): vds_slope_ok·fc_ok_vgs·fc_ok_vds·hermite_fc
# ---------------------------------------------------------------------------

def _check_hermite_fields(sl, z):
    from .conftest import RefSlice
    rs = RefSlice(z)
    nL, nG, nV, nS = (len(g) for g in rs.grids)
    assert np.asarray(sl.fc_ok_vgs).shape == (nL, nG - 1, nV, nS)
    assert np.asarray(sl.fc_ok_vds).shape == (nL, nG, nV - 1, nS)
    for name in ("vds_slope_ok", "fc_ok_vgs", "fc_ok_vds"):
        arr = getattr(sl, name)
        assert np.asarray(arr).dtype == np.bool_, name
        with pytest.raises(ValueError):
            arr[0, 0, 0, 0] = arr[0, 0, 0, 0]
    np.testing.assert_array_equal(np.asarray(sl.vds_slope_ok), rs.vds_ok)
    np.testing.assert_array_equal(np.asarray(sl.fc_ok_vgs), rs.fc_vgs)
    np.testing.assert_array_equal(np.asarray(sl.fc_ok_vds), rs.fc_vds)
    assert tuple(sl.hermite_fc) == rs.hermite_fc()
    return rs


@pytest.mark.parametrize("w_key,W,scale", [(100, 1e-6, 1.0), (200, 2e-6, 2.0)])
def test_r5_toy_hermite_fields(toy, w_key, W, scale):
    """CONTRACT 7.1: hermite_fc = (("VDS", 18, 0), ("VGS", 24, 0))."""
    sl = toy.slice_map[("nmos", w_key)]
    _check_hermite_fields(sl, toy_slice_arrays(W, scale))
    assert tuple(sl.hermite_fc) == (("VDS", 18, 0), ("VGS", 24, 0))
    assert np.asarray(sl.fc_ok_vgs).all() and np.asarray(sl.fc_ok_vds).all()


def test_r4_toy_hermite_fields_load_not_rejected(r4toy):
    """CONTRACT 7.2: hermite_fc = (("VDS", 18, 18), ("VGS", 24, 12)) -- 위반이 있어도 로드는 거부하지 않는다."""
    from .conftest import r4_toy_slice_arrays
    sl = r4toy.slice_map[("nmos", 100)]
    _check_hermite_fields(sl, r4_toy_slice_arrays(1e-6))
    assert tuple(sl.hermite_fc) == (("VDS", 18, 18), ("VGS", 24, 12))
    fv = np.asarray(sl.fc_ok_vgs)
    assert not fv[:, 0].any() and fv[:, 1].all()                    # VGS 칸 0 위반, 칸 1 단조
    assert not np.asarray(sl.fc_ok_vds).any()


def test_non_hermite_cells_are_true(toy_build):
    """Hermite 칸이 아닌 칸(한 끝 기울기 정의 안 됨)은 참. GDS 0 점 -> vds_slope_ok 거짓, 그 VDS 칸은 Hermite 칸 아님."""
    sl_ = standard_toy_slices()
    a = sl_[0][2]
    a["GDS"][0, 1, 0, 0] = 0.0
    a["ID"][2, 2, 1, 1] = 0.0
    lut = toy_build(slices=sl_).load()
    sl = lut.slice_map[("nmos", 100)]
    rs = _check_hermite_fields(sl, a)
    assert not bool(np.asarray(sl.vds_slope_ok)[0, 1, 0, 0])
    assert bool(np.asarray(sl.fc_ok_vds)[0, 1, 0, 0])
    assert bool(np.asarray(sl.fc_ok_vgs)[2, 1, 1, 1])
    # 손계산: VDS 칸 18 − (GDS 0 점의 칸 1) − (ID 0 점의 칸 1) = 16, VGS 칸 24 − (ID 0 점 = VGS 끝 마디, 칸 1) = 23
    assert rs.hermite_fc() == (("VDS", 16, 0), ("VGS", 23, 0))


def test_log_floor_is_min_positive_and_on_mask(toy_build):
    sl = standard_toy_slices()
    a = sl[0][2]
    a["ID"][0, 0, 0, 0] = 0.0
    a["ID"][1, 0, 1, 1] = -1e-12
    a["GM"][2, 1, 0, 0] = 0.0
    lut = toy_build(slices=sl).load()
    s = lut.slice_map[("nmos", 100)]
    id_floor = float(a["ID"][a["ID"] > 0].min())
    gm_floor = float(a["GM"][a["GM"] > 0].min())
    np.testing.assert_array_equal(np.asarray(s.log_ID), np.log(np.clip(a["ID"], id_floor, None)))
    np.testing.assert_array_equal(np.asarray(s.log_GM), np.log(np.clip(a["GM"], gm_floor, None)))
    assert np.asarray(s.log_ID)[0, 0, 0, 0] == np.log(id_floor)          # 상수 바닥 없음
    expect_mask = (a["ID"] > 0) & (a["GM"] > 0)
    np.testing.assert_array_equal(np.asarray(s.on_mask), expect_mask)
    assert int((~np.asarray(s.on_mask)).sum()) == 3
    floors = dict(s.floors)
    nonpos = dict(s.nonpositive)
    assert floors["ID"] == id_floor and floors["GM"] == gm_floor
    assert nonpos["ID"] == 2 and nonpos["GM"] == 1 and nonpos["GDS"] == 0     # GDS 는 ID 수정 전 값


def test_cap_recorded_w_ref(toy):
    cap = toy.cap_map["nmos"]
    assert isinstance(cap, CapTable)
    assert cap.w_ref_m == 1e-6
    assert cap.basis == (("method", "recorded_w_ref_m"),)
    assert cap.grids == (TOY_L, TOY_VGS, TOY_VDS, TOY_VS)


def test_cap_vs_axis_may_differ(toy_build):
    cap = toy_cap_arrays()
    cap["VS"] = np.asarray((0.0, 0.25, 0.75))
    shp = (3, 3, 2, 3)
    cap["CGG_n"], cap["CGD_n"] = np.full(shp, 1e-15), np.full(shp, 2e-16)
    lut = toy_build(cap=cap).load()
    assert lut.cap_map["nmos"].grids[3] == (0.0, 0.25, 0.75)


def test_cap_width_by_slice_id_match(toy_build):
    cap = toy_cap_arrays()
    del cap["w_ref_m"]
    cap["ID_n"] = toy_slice_arrays(1e-6)["ID"].copy()
    lut = toy_build(cap=cap).load()
    c = lut.cap_map["nmos"]
    assert rel_close(c.w_ref_m, 1e-6, 1e-12)
    b = dict(c.basis)
    assert [k for k, _ in c.basis] == ["max_rel_diff", "method", "nearest_other_rel_diff", "w_key"]
    assert b["method"] == "slice_id_match" and b["w_key"] == 100
    assert b["max_rel_diff"] == 0.0
    assert rel_close(b["nearest_other_rel_diff"], 1.0, 1e-12)


# ---------------------------------------------------------------------------
# 거부 사유 (1.4 고유)
# ---------------------------------------------------------------------------

def test_reject_conditions_mismatch_between_slices(toy_build):
    sl = standard_toy_slices()
    sl[1][2]["corner"] = np.str_("ff")
    assert _reject(toy_build(slices=sl))["reason"] == "lut_conditions_mismatch"


def test_reject_conditions_mismatch_temp(toy_build):
    sl = standard_toy_slices()
    sl[1][2]["temp_c"] = np.float64(85.0)
    assert _reject(toy_build(slices=sl))["reason"] == "lut_conditions_mismatch"


def test_reject_conditions_mismatch_cap(toy_build):
    cap = toy_cap_arrays()
    cap["temp_c"] = np.float64(-40.0)
    assert _reject(toy_build(cap=cap))["reason"] == "lut_conditions_mismatch"


@pytest.mark.parametrize("axis,new", [
    ("L", (1e-6, 2e-6, 3.5e-6)),
    ("VGS", (0.0, 0.4, 1.0)),
    ("VDS", (0.5, 1.1)),
    ("VS", (0.0, 0.25)),
])
def test_reject_slice_axes_mismatch(toy_build, axis, new):
    sl = standard_toy_slices()
    sl[1][2][axis] = np.asarray(new)
    assert _reject(toy_build(slices=sl))["reason"] == "lut_slice_axes_mismatch"


def test_reject_slice_axes_one_ulp(toy_build):
    sl = standard_toy_slices()
    vgs = np.asarray(TOY_VGS)
    vgs[1] = np.nextafter(vgs[1], 1.0)                # float 단위로 같아야 한다
    sl[1][2]["VGS"] = vgs
    assert _reject(toy_build(slices=sl))["reason"] == "lut_slice_axes_mismatch"


@pytest.mark.parametrize("name", ["ID", "GM", "GDS", "VTH"])
def test_reject_slice_shape_mismatch(toy_build, name):
    sl = standard_toy_slices()
    sl[0][2][name] = sl[0][2][name][:, :2]
    assert _reject(toy_build(slices=sl))["reason"] == "lut_slice_shape_mismatch"


@pytest.mark.parametrize("name", ["ID", "GM", "GDS"])
def test_reject_array_no_positive(toy_build, name):
    sl = standard_toy_slices()
    sl[0][2][name] = np.zeros_like(sl[0][2][name])
    assert _reject(toy_build(slices=sl))["reason"] == "lut_array_no_positive"


@pytest.mark.parametrize("axis,new", [
    ("L", (1e-6, 2e-6, 4e-6)),
    ("VGS", (0.0, 0.5, 1.1)),
    ("VDS", (0.4, 1.0)),
])
def test_reject_cap_axes_mismatch(toy_build, axis, new):
    cap = toy_cap_arrays()
    cap[axis] = np.asarray(new)
    assert _reject(toy_build(cap=cap))["reason"] == "lut_cap_axes_mismatch"


def test_reject_cap_kind_undeclared(toy_build):
    # 슬라이스 kind(nmos)의 기준 LUT 열 접미사가 선언되지 않음
    spec = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), ())
    det = _reject(toy_build(), spec)
    assert det["reason"] == "lut_cap_kind_undeclared" and det["kind"] == "nmos"


@pytest.mark.parametrize("cap_cols", [False, True])
def test_reject_cap_kind_without_slices(toy_build, cap_cols):
    # [r2] 용량 kind 집합 = 슬라이스 kind ∪ 접미사 선언 kind (fail-closed): 선언됐지만 슬라이스 없는 kind -> 거부
    # (열 유무와 무관: 검사 순서가 접미사 -> 슬라이스 -> 열)
    cap = toy_cap_arrays()
    if cap_cols:
        cap["CGG_q"], cap["CGD_q"] = cap["CGG_n"].copy(), cap["CGD_n"].copy()
    spec = LutSpec(1e-8, (("nmos", 1.5e-6), ("qmos", 1e-6)), (("toyn", "nmos"), ("toyq", "qmos")),
                   (("nmos", "_n"), ("qmos", "_q")))
    det = _reject(toy_build(cap=cap), spec)
    assert det["reason"] == "lut_cap_kind_without_slices" and det["kind"] == "qmos"


def test_cap_map_keys_are_cap_kind_set(toy):
    assert set(toy.cap_map) == {"nmos"} == {k for k, _ in toy.slice_map}


@pytest.mark.parametrize("drop", ["CGG_n", "CGD_n"])
def test_reject_cap_column_missing(toy_build, drop):
    cap = toy_cap_arrays()
    del cap[drop]
    assert _reject(toy_build(cap=cap))["reason"] == "lut_cap_column_missing"


def _cap_no_wref(id_ref=None, vs=None):
    cap = toy_cap_arrays()
    del cap["w_ref_m"]
    if vs is not None:
        cap["VS"] = np.asarray(vs)
    if id_ref is not None:
        cap["ID_n"] = id_ref
    return cap


def test_reject_width_unresolved_no_wref_no_id(toy_build):
    assert _reject(toy_build(cap=_cap_no_wref()))["reason"] == "lut_cap_width_unresolved"


def test_reject_width_unresolved_single_slice(toy_build):
    sl = standard_toy_slices()[:1]
    cap = _cap_no_wref(toy_slice_arrays(1e-6)["ID"].copy())
    assert _reject(toy_build(slices=sl, cap=cap))["reason"] == "lut_cap_width_unresolved"


def test_reject_width_unresolved_tie(toy_build):
    # 2 의 거듭제곱 값: |I − 2I| / 2I = |3I − 2I| / 2I = 0.5 정확히 같음(동률)
    vgs = (0.0, 0.5, 1.0)
    base = np.asarray((2.0 ** -24, 2.0 ** -20, 2.0 ** -16))
    gmid = (20.0, 10.0, 4.0)
    a = curve_slice_arrays(1e-6, vgs, base, gmid)
    b = curve_slice_arrays(2e-6, vgs, 3.0 * base, gmid)
    ref = curve_slice_arrays(1e-6, vgs, 2.0 * base, gmid)["ID"]
    d_a = np.max(np.abs(a["ID"] - ref) / ref)
    d_b = np.max(np.abs(b["ID"] - ref) / ref)
    assert d_a == d_b == 0.5                                   # 전제: 정확한 동률
    cap = curve_cap_arrays(vgs)
    del cap["w_ref_m"]
    cap["ID_n"] = ref.copy()
    built = toy_build(slices=[("a.npz", "toyn", a), ("b.npz", "toyn", b)], cap=cap)
    assert _reject(built)["reason"] == "lut_cap_width_unresolved"


def test_reject_width_unresolved_separation(toy_build):
    # 슬라이스 ID 배수 1(키 100)·1.1(키 110), 기준 0.8: d_100 = 0.25 가 최소지만 이웃 차(0.1 수준)의 절반보다 크다
    sl = [("a.npz", "toyn", toy_slice_arrays(1e-6, 1.0)),
          ("b.npz", "toyn", toy_slice_arrays(1.1e-6, 1.1))]
    cap = _cap_no_wref(toy_slice_arrays(1e-6, 0.8)["ID"].copy())
    assert _reject(toy_build(slices=sl, cap=cap))["reason"] == "lut_cap_width_unresolved"


def test_reject_width_unresolved_vs_not_on_axis(toy_build):
    shp = (3, 3, 2, 2)
    cap = _cap_no_wref(np.full(shp, 1e-6), vs=(0.25, 0.75))
    assert _reject(toy_build(cap=cap))["reason"] == "lut_cap_width_unresolved"


# ---------------------------------------------------------------------------
# 1.3 사유는 load_lut_set 에서도 (대표 2개 -- 전부는 test_provenance)
# ---------------------------------------------------------------------------

def test_provenance_reasons_propagate(toy_build, tmp_path):
    b = toy_build()
    (b.root / "toy_w200.npz").unlink()
    assert _reject(b)["reason"] == "lut_slice_missing"
    b2 = toy_build("x")
    b2.cap.unlink()
    assert _reject(b2)["reason"] == "lut_cap_missing"


# ---------------------------------------------------------------------------
# 실데이터: 슬라이스 32 개, 용량 기준 폭 = 5 µm (독립 계산과 대조)
# ---------------------------------------------------------------------------

def _independent_width_choice(raw_cap, raw_slice, keys, suffix):
    VSr = [float(v) for v in raw_cap["VS"]]
    IR = raw_cap["ID" + suffix]
    d, ids = {}, {}
    for kind, wk in keys:
        z = raw_slice(kind, wk)
        VSs = [float(v) for v in z["VS"]]
        cols = [VSs.index(v) for v in VSr]
        I = z["ID"][..., cols]
        mask = IR > 0
        ids[wk] = (I, mask)
        d[wk] = float(np.max(np.abs(I[mask] - IR[mask]) / np.abs(IR[mask])))
    best = min(d, key=d.get)
    Ib, mask = ids[best]
    m2 = mask & (Ib > 0)                     # [r2] 비교 점: 기준 ID > 0 이고 ID_w > 0, 분모 ID_w
    near = min(float(np.max(np.abs(ids[w][0][m2] - Ib[m2]) / np.abs(Ib[m2]))) for w in d if w != best)
    second = sorted(d.values())[1]
    return best, d[best], near, second


@pytest.mark.lut_realdata
def test_real_load(real_lut, real_slice_files, raw_cap, raw_slice):
    assert len(real_lut.slice_map) == len(real_slice_files) == 32
    assert set(real_lut.slice_map) == {(k, wk) for k, _, _, wk, _ in real_slice_files}
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        keys = [(k, wk) for (k, wk) in real_lut.slice_map if k == kind]
        best, dw, near, second = _independent_width_choice(raw_cap, raw_slice, keys, suf)
        assert best == 1000
        cap = real_lut.cap_map[kind]
        b = dict(cap.basis)
        assert b["method"] == "slice_id_match" and b["w_key"] == best
        assert rel_close(b["max_rel_diff"], dw, 1e-9)
        assert dw < 1e-6
        # [r2] sep = min over s ≠ w of max |ID_s − ID_w| / |ID_w| (분모 = 고른 슬라이스). 계약 실측 0.88(nmos)·1.25(pmos)
        assert rel_close(b["nearest_other_rel_diff"], near, 1e-12), (kind, b, near, second)
        assert rel_close(near, {"nmos": 0.8845524, "pmos": 1.2508113}[kind], 1e-6)
        assert dw < b["nearest_other_rel_diff"] / 2
        assert rel_close(cap.w_ref_m, real_lut.slice_map[(kind, best)].w_m, 1e-12)


@pytest.mark.lut_realdata
def test_real_hermite_fields_all_slices(real_lut, real_slice_files, raw_slice):
    """[r5] 모든 실 슬라이스의 vds_slope_ok·fc_ok_vgs·fc_ok_vds·hermite_fc = npz 독립 FC 계산(계약 1.4 실측과 대조 기록)."""
    seen = set()
    for kind, _, _, wk, _ in real_slice_files:
        sl = real_lut.slice_map[(kind, wk)]
        _check_hermite_fields(sl, raw_slice(kind, wk))
        seen.add(tuple(sl.hermite_fc))
    assert seen == {(("VDS", 276360, 0), ("VGS", 276480, 0))}
