"""`load_lut_set` -- CONTRACT 1.4: LutSet 구성·불변식·용량 기준 폭 w_ref_m·로드 거부 사유(1.3 전부 + 8종).

거부 test 는 toy 임시 사본을 고쳐 만든다(manifest sha256 은 고친 파일로 다시 잰다 -- sha 불일치는 test_provenance).
"""
import json
import math

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import CapTable, DcSlice, LutSet, LutSpec, MidpointTable

from .conftest import (BIN_ANCHOR_BIN_LO, BIN_BLOCKS, BIN_MODEL_REL, MID_L_SOURCE, SKILL_DIR, TOY_L, TOY_SPEC, TOY_VDS, TOY_VGS, TOY_VS,
                       curve_cap_arrays, curve_slice_arrays, detail_of, mid_point_arrays, sha256_file,
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
    """[r6] LUT v2: 슬라이스 32개, 축 18 L·VS 10(0~1.8), 기준 LUT 에 w_ref_m(5e-06) 기록 -> basis (("method", "recorded_w_ref_m"),).
    기록값은 슬라이스 ID 대조로도 같은 폭(키 1000)을 고른다(데이터 정합 확인 -- 독립 계산)."""
    assert len(real_lut.slice_map) == len(real_slice_files) == 32
    assert set(real_lut.slice_map) == {(k, wk) for k, _, _, wk, _ in real_slice_files}
    for sl in real_lut.slice_map.values():
        assert len(sl.grids[0]) == 18 and len(sl.grids[3]) == 10
        assert sl.grids[3][0] == 0.0 and sl.grids[3][-1] == 1.8
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        cap = real_lut.cap_map[kind]
        assert tuple(cap.basis) == (("method", "recorded_w_ref_m"),)
        assert cap.w_ref_m == float(raw_cap["w_ref_m"]) == 5e-06
        keys = [(k, wk) for (k, wk) in real_lut.slice_map if k == kind]
        best, dw, near, second = _independent_width_choice(raw_cap, raw_slice, keys, suf)
        assert best == 1000 and dw < near / 2


@pytest.mark.lut_realdata
def test_old_set_load_slice_id_match(old_lut, old_slice_files, old_raw_cap, old_raw_slice):
    """옛 12-L 세트(w_ref_m 기록 없음 -- 1.4 (2) slice_id_match): 계약 1.4 실측 nmos·pmos 모두 w_key 1000, 이웃 차 0.88·1.25."""
    assert len(old_lut.slice_map) == len(old_slice_files) == 32
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        keys = [(k, wk) for (k, wk) in old_lut.slice_map if k == kind]
        best, dw, near, second = _independent_width_choice(old_raw_cap, old_raw_slice, keys, suf)
        assert best == 1000
        cap = old_lut.cap_map[kind]
        b = dict(cap.basis)
        assert b["method"] == "slice_id_match" and b["w_key"] == best
        assert rel_close(b["max_rel_diff"], dw, 1e-9)
        assert dw < 1e-6
        # [r2] sep = min over s ≠ w of max |ID_s − ID_w| / |ID_w| (분모 = 고른 슬라이스). 계약 실측 0.88(nmos)·1.25(pmos)
        assert rel_close(b["nearest_other_rel_diff"], near, 1e-12), (kind, b, near, second)
        assert rel_close(near, {"nmos": 0.8845524, "pmos": 1.2508113}[kind], 1e-6)
        assert dw < b["nearest_other_rel_diff"] / 2
        assert rel_close(cap.w_ref_m, old_lut.slice_map[(kind, best)].w_m, 1e-12)
        assert cap.w_key == 1000                                            # [r6] 폭 키
        assert cap.l_bins == old_lut.slice_map[(kind, 1000)].l_bins


@pytest.mark.lut_realdata
def test_real_hermite_fields_all_slices(real_lut, real_slice_files, raw_slice):
    """[r5] 모든 실 슬라이스의 vds_slope_ok·fc_ok_vgs·fc_ok_vds·hermite_fc = npz 독립 FC 계산.
    [r6] LUT v2(18 L·VS 10)의 칸 수는 독립 계산이 정한다(옛 12-L 실측 276360·276480 은 old_lut test)."""
    seen = set()
    for kind, _, _, wk, _ in real_slice_files:
        sl = real_lut.slice_map[(kind, wk)]
        _check_hermite_fields(sl, raw_slice(kind, wk))
        seen.add(tuple(sl.hermite_fc))
    print("LUT v2 hermite_fc 종류: %r" % (sorted(seen),))


@pytest.mark.lut_realdata
def test_old_set_hermite_fields(old_lut, old_slice_files, old_raw_slice):
    """옛 12-L 세트: 계약 1.4 [r5 실측] 모든 슬라이스 hermite_fc = (("VDS", 276360, 0), ("VGS", 276480, 0))."""
    for kind, _, _, wk, _ in old_slice_files[:3]:
        _check_hermite_fields(old_lut.slice_map[(kind, wk)], old_raw_slice(kind, wk))
    assert {tuple(sl.hermite_fc) for sl in old_lut.slice_map.values()} == {(("VDS", 276360, 0), ("VGS", 276480, 0))}


# ---------------------------------------------------------------------------
# [r4] L bin 지도 로드 거부 (1.4) -- bin toy 임시 사본의 모델 파일을 고쳐 만든다(meta sha256 은 고친 파일로 다시 잰다)
# ---------------------------------------------------------------------------

def _blocks_set(name, idx, value, blocks=BIN_BLOCKS):
    return tuple(b[:idx] + (value,) + b[idx + 1:] if b[0] == name else b for b in blocks)


def test_reject_model_bin_incomplete(bin_toy_build):
    det = _reject(bin_toy_build(extra=".model toyn__half nmos\n+ lmin = 1e-06 lmax = 2e-06"))
    assert det["reason"] == "lut_model_bin_incomplete"
    assert det["model"] == "toyn__half" and "path" in det and "keys" in det


def test_reject_model_bins_no_width(bin_toy_build):
    # 아래 W 범위 wmax 를 0.9 µm, 위 범위 wmin 을 1.1 µm 로: 폭 1e-6 슬라이스가 어느 W 범위에도 없다
    blocks = tuple(b[:4] + (0.9e-6,) if b[4] == 1e-6 else (b[:3] + (1.1e-6,) + b[4:]) for b in BIN_BLOCKS)
    det = _reject(bin_toy_build(blocks=blocks))
    assert det["reason"] == "lut_model_bins_no_width"
    assert det["w_m"] == 1e-6 and "path" in det


def test_reject_model_bins_overlap(bin_toy_build):
    det = _reject(bin_toy_build(blocks=_blocks_set("toyn__model.1", 1, 1.9e-6)))     # B = [1.9, 4] 가 A = [1, 2] 와 겹침
    assert det["reason"] == "lut_model_bins_overlap"
    assert det["w_m"] == 1e-6 and set(det["models"]) == {"toyn__model.0", "toyn__model.1"}


def test_adjacent_within_one_ulp_is_not_overlap(bin_toy_build):
    lo_b = 2e-6 - math.ulp(2e-6)                      # B 의 lmin 이 A 의 lmax 보다 1 ulp 아래 -> 겹침 아님
    lut = bin_toy_build(blocks=_blocks_set("toyn__model.1", 1, lo_b)).load()
    assert lut.slice_map[("nmos", 100)].l_bins.anchor_bin == BIN_ANCHOR_BIN_LO


def test_reject_anchor_outside_model_bins(bin_toy_build):
    det = _reject(bin_toy_build(blocks=tuple(b for b in BIN_BLOCKS if b[0] != "toyn__model.4")))   # 9 µm 앵커의 bin 없음
    assert det["reason"] == "lut_l_anchor_outside_model_bins"
    assert det["L"] == 9e-6 and det["w_m"] == 1e-6 and "path" in det


def test_no_bin_blocks_gives_empty_map(bin_toy_build):
    """모델 파일에 bin 블록이 하나도 없으면 거부가 아니라 빈 지도(1.4 의 2.)."""
    lut = bin_toy_build(blocks=()).load()
    for sl in lut.slice_map.values():
        assert sl.l_bins.bins == () and sl.l_bins.w_bin is None and sl.l_bins.anchor_bin == ()


# ---------------------------------------------------------------------------
# [r6] 1.7 검증 중점 파일 로드: MidpointTable 필드, 거부 순서 (1)~(7)
# ---------------------------------------------------------------------------

MID_LS = (3.25e-6, 3.5e-6, 7.5e-6)


def _mid(**kw):
    kw.setdefault("l_source", MID_L_SOURCE)
    return mid_point_arrays(MID_LS, **kw)


def _mid_reject(mid_toy_build, sub, mid, **kw):
    mt = mid_toy_build(sub, mid=mid, **kw)
    with pytest.raises(SchemaRejectedError) as ei:
        mt.load()
    return detail_of(ei.value), mt


def test_midpoint_table_fields(mid_toy_build):
    m = _mid()
    m["ID_n"] = m["ID_n"].copy()
    m["ID_n"][0, 0, 0, 0] = 0.0                                     # ID 0 점 -> log_ID·gm_id NaN, on_mask 거짓
    mt = mid_toy_build("mf", mid=m)
    lut = mt.load()
    assert set(lut.midpoints) == {"nmos"}
    t = lut.midpoints["nmos"]
    assert isinstance(t, MidpointTable)
    assert (t.kind, t.sha256, t.w_m, t.w_key) == ("nmos", sha256_file(mt.mid_path), 1e-6, 100)
    assert tuple(t.L_points) == MID_LS
    assert tuple(tuple(g) for g in t.grids) == (tuple(m["VGS"]), tuple(m["VDS"]), tuple(m["VS"]))
    I, G = m["ID_n"], m["GM_n"]
    pos = I > 0
    lg = np.asarray(t.log_ID)
    assert np.isnan(lg[0, 0, 0, 0]) and np.array_equal(lg[pos], np.log(I[pos]))
    gi = np.asarray(t.gm_id)
    assert np.isnan(gi[0, 0, 0, 0]) and np.array_equal(gi[pos], G[pos] / I[pos])
    assert np.array_equal(np.asarray(t.on_mask), (I > 0) & (G > 0))
    assert np.array_equal(np.asarray(t.VDSAT), m["VDSAT_n"])
    t2 = mid_toy_build("mf2", mid=_mid(vdsat=False)).load().midpoints["nmos"]
    assert t2.VDSAT is None


def test_contract_toy_r6_table(toy):
    """7.1 r6 표 첫 세 행(선택 열·중점 파일 없는 r5 toy)."""
    ct = toy.cap_map["nmos"]
    assert (ct.w_key, dict(ct.columns), ct.on_mask, ct.sign_convention, tuple(ct.l_source)) == (100, {}, None, None, ())
    assert dict(toy.slice_map[("nmos", 100)].columns) == {}
    assert dict(toy.midpoints) == {} and toy.provenance.midpoints_sha256 is None


def test_no_midpoints_empty_mapping(mid_toy_build, toy):
    assert dict(toy.midpoints) == {}
    assert dict(mid_toy_build("nm").load().midpoints) == {}


@pytest.mark.parametrize("ls", [None, {"kind": "cli"}, {"kind": "cli", "value": "0.165,6.0,14.0"}])
def test_reject_l_source_unrecorded(mid_toy_build, ls):
    """(1) meta L_source 에 sha256 없음(없음·`--l-um` cli -- 생성기 sky130_lut_sweep.py read_l_list 의 모양
    {"kind": "cli", "value": <쉼표 문자열>}) -> lut_midpoints_l_source_unrecorded."""
    m = mid_point_arrays(MID_LS, l_source=ls)
    det, _ = _mid_reject(mid_toy_build, "lsu", m)
    assert det["reason"] == "lut_midpoints_l_source_unrecorded" and "path" in det and "l_source" in det


def test_l_source_matching_cap_accepted_mismatch_rejected(mid_toy_build):
    """(2) 기준 LUT L_source sha256 이 있고 중점 sha256 과 다름 -> lut_midpoints_l_source_mismatch(detail path, kind, cap, midpoints).
    같으면 로드."""
    ok = mid_toy_build("lsok", mid=_mid(), cap_meta={"L_source": dict(MID_L_SOURCE)}).load()
    assert dict(ok.cap_map["nmos"].l_source)["sha256"] == MID_L_SOURCE["sha256"]
    det, _ = _mid_reject(mid_toy_build, "lsbad", _mid(), cap_meta={"L_source": {"kind": "json", "sha256": "b" * 64}})
    assert det["reason"] == "lut_midpoints_l_source_mismatch"
    assert (det["kind"], det["cap"], det["midpoints"]) == ("nmos", "b" * 64, MID_L_SOURCE["sha256"])


@pytest.mark.parametrize("field,val", [("corner", "ff"), ("temp_c", 85.0)])
def test_reject_conditions_mismatch(mid_toy_build, field, val):
    det, _ = _mid_reject(mid_toy_build, "cond", _mid(**{field: val}))
    assert det["reason"] == "lut_conditions_mismatch"
    assert det["key"] == field and det["midpoints"] == val


@pytest.mark.parametrize("axis", ["VGS", "VDS", "VS"])
def test_reject_axes_mismatch(mid_toy_build, axis):
    m = _mid()
    a = np.asarray(m[axis], dtype=float).copy()
    a[-1] = np.nextafter(a[-1], 10.0)                               # 1 ulp 도 다르면 거부(float 단위 같음)
    m[axis] = a
    det, _ = _mid_reject(mid_toy_build, "ax", m)
    assert det["reason"] == "lut_midpoints_axes_mismatch"


def test_reject_width_missing_and_off_grid(mid_toy_build):
    det, _ = _mid_reject(mid_toy_build, "wm", _mid(w_ref_m=None))
    assert det["reason"] == "lut_midpoints_width_missing"
    m = _mid()
    m["w_ref_m"] = np.float64(1.005e-6)                             # 100.5 격자 -> 격자 밖
    det, _ = _mid_reject(mid_toy_build, "wo", m)
    assert det["reason"] == "lut_width_off_grid"


@pytest.mark.parametrize("drop", ["ID_n", "GM_n"])
def test_reject_column_missing(mid_toy_build, drop):
    det, _ = _mid_reject(mid_toy_build, "cm", _mid(drop=(drop,)))
    assert det["reason"] == "lut_midpoints_column_missing"
    # [해석] detail column 이 접미사 없는 이름("ID")인지 열 이름("ID_n")인지는 계약에 없다 -- 둘 다 허용
    assert det["kind"] == "nmos" and det["column"] in (drop.split("_")[0], drop)


def test_reject_shape_mismatch(mid_toy_build):
    m = _mid()
    m["GM_n"] = m["GM_n"][:, :, :, :1]
    det, _ = _mid_reject(mid_toy_build, "sm", m)
    assert det["reason"] == "lut_midpoints_shape_mismatch"


@pytest.mark.parametrize("bad,first", [
    # (고친 것들, 먼저 나와야 할 사유) -- 1.7 검사 순서 (1) l_source -> (3) 조건 -> (4) 축 -> (5) 폭 -> (7) 열
    ({"l_source": None, "corner": "ff"}, "lut_midpoints_l_source_unrecorded"),
    ({"corner": "ff", "axis": "VGS"}, "lut_conditions_mismatch"),
    ({"axis": "VDS", "w_ref_m": None}, "lut_midpoints_axes_mismatch"),
    ({"w_ref_m": None, "drop": ("GM_n",)}, "lut_midpoints_width_missing"),
])
def test_reject_order(mid_toy_build, bad, first):
    kw = dict(bad)
    axis = kw.pop("axis", None)
    kw.setdefault("l_source", MID_L_SOURCE)
    m = mid_point_arrays(MID_LS, **kw)
    if axis:
        a = np.asarray(m[axis], dtype=float).copy()
        a[0] = a[0] - 1e-3
        m[axis] = a
    det, _ = _mid_reject(mid_toy_build, "ord", m)
    assert det["reason"] == first


@pytest.mark.lut_realdata
def test_real_midpoints_loaded(real_lut, raw_mid):
    """[r6, 2026-10-08 중점 변경] 1.7: L = 승인 L 파일 `verification_midpoints_um` (0.165·0.85·1.75·3.25 µm -- CONTRACT 8절,
    user_decisions 2026-10-08 '7번'), w_ref_m 5e-06 -> 폭 키 1000, nmos·pmos 표.
    oracle: (d) 사용자 결정으로 선언된 승인 L 파일 값(파일을 직접 읽음) + 중점 npz 를 numpy 로 직접 읽은 L 축."""
    assert set(real_lut.midpoints) == {"nmos", "pmos"}
    declared = json.loads((SKILL_DIR / "assets" / "sky130_lut_L_grid.json").read_text(encoding="utf-8"))
    declared_um = declared["verification_midpoints_um"]
    assert declared_um == [0.165, 0.85, 1.75, 3.25]                    # (d) 사용자 결정 2026-10-08 '7번' 의 목록
    file_L = tuple(float(x) for x in raw_mid["L"])
    assert len(file_L) == len(declared_um)
    for got, um_ in zip(file_L, declared_um):                         # µm -> m 곱의 반올림(1 ulp) 안
        assert abs(got - um_ * 1e-6) <= math.ulp(um_ * 1e-6), (got, um_)
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        t = real_lut.midpoints[kind]
        assert t.w_key == 1000 and t.w_m == float(raw_mid["w_ref_m"]) == 5e-06
        assert tuple(t.L_points) == file_L
        assert np.array_equal(np.asarray(t.VDSAT), raw_mid["VDSAT" + suf])
        I, G = raw_mid["ID" + suf], raw_mid["GM" + suf]
        assert np.array_equal(np.asarray(t.on_mask), (I > 0) & (G > 0))
