"""`load_lut_set` -- CONTRACT 1.4: LutSet 구성·불변식·용량 기준 폭 w_ref_m·로드 거부 사유(1.3 전부 + 8종).

거부 test 는 toy 임시 사본을 고쳐 만든다(manifest sha256 은 고친 파일로 다시 잰다 -- sha 불일치는 test_provenance).
"""
import json
import math

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import CapTable, DcSlice, LutSet, LutSpec, MidpointTable, widths

from .conftest import (BIN_ANCHOR_BIN_LO, BIN_BLOCKS, BIN_MODEL_REL, SKILL_DIR, T_MID_L, TOY_L, TOY_SPEC, TOY_VDS, TOY_VGS, TOY_VS,
                       build_t, curve_cap_arrays, curve_slice_arrays, detail_of, mid_file, mid_meta, sha256_file,
                       rel_close, t_spec,
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
    # [r7] VS 축 보조 필드(CONTRACT 1.4 [r7]): vs_slope_ok = GMBS/ID 유한·양수, fc_ok_vs 모양 [nL, nVGS, nVDS, nVS − 1]
    assert np.asarray(sl.fc_ok_vs).shape == (nL, nG, nV, nS - 1)
    np.testing.assert_array_equal(np.asarray(sl.vs_slope_ok), rs.vs_ok)
    np.testing.assert_array_equal(np.asarray(sl.fc_ok_vs), rs.fc_vs)
    assert tuple(sl.hermite_fc) == rs.hermite_fc()
    return rs


@pytest.mark.parametrize("w_key,W,scale", [(100, 1e-6, 1.0), (200, 2e-6, 2.0)])
def test_r5_toy_hermite_fields(toy, w_key, W, scale):
    """CONTRACT 7.1: hermite_fc = (("VDS", 18, 0), ("VGS", 24, 0)) [r7: + ("VS", 0, 0) -- toy 슬라이스는 GMBS 열이 없어 VS Hermite 칸 0]."""
    sl = toy.slice_map[("nmos", w_key)]
    _check_hermite_fields(sl, toy_slice_arrays(W, scale))
    assert tuple(sl.hermite_fc) == (("VDS", 18, 0), ("VGS", 24, 0), ("VS", 0, 0))
    assert np.asarray(sl.fc_ok_vgs).all() and np.asarray(sl.fc_ok_vds).all()


def test_r4_toy_hermite_fields_load_not_rejected(r4toy):
    """CONTRACT 7.2: hermite_fc = (("VDS", 18, 18), ("VGS", 24, 12)) [r7: + ("VS", 0, 0)] -- 위반이 있어도 로드는 거부하지 않는다."""
    from .conftest import r4_toy_slice_arrays
    sl = r4toy.slice_map[("nmos", 100)]
    _check_hermite_fields(sl, r4_toy_slice_arrays(1e-6))
    assert tuple(sl.hermite_fc) == (("VDS", 18, 18), ("VGS", 24, 12), ("VS", 0, 0))
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
    assert rs.hermite_fc() == (("VDS", 16, 0), ("VGS", 23, 0), ("VS", 0, 0))


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
    base = np.asarray((2.0 ** -24, 2.0 ** -20, 2.0 ** -17))
    # [r7] gm/ID 는 ln ID 현(ln16/0.5 = 5.55, ln8/0.5 = 4.16)이 두 끝 사이가 되게(lut CONTRACT 1.4 단위 검사 일관 -- 이 test 의 대상은 폭 동률)
    gmid = (6.0, 5.0, 4.0)
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
def test_real_hermite_fields_all_slices(real_lut, real_slice_files, raw_slice):
    """[r5] 모든 실 슬라이스의 vds_slope_ok·fc_ok_vgs·fc_ok_vds·hermite_fc = npz 독립 FC 계산.
    [r6] LUT v2(18 L·VS 10)의 칸 수는 독립 계산이 정한다(옛 12-L 실측 276360·276480 은 old_lut test)."""
    seen = set()
    for kind, _, _, wk, _ in real_slice_files:
        sl = real_lut.slice_map[(kind, wk)]
        _check_hermite_fields(sl, raw_slice(kind, wk))
        seen.add(tuple(sl.hermite_fc))
    print("LUT v2 hermite_fc 종류: %r" % (sorted(seen),))


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
# [LM-1e §2·§3] 중점 파일(DC 슬라이스 npz 꼴) 적재: MidpointTable 필드, 관문 G5~G7b(`load_lut_set`), D7 적재 거부(`bin_missing_external`)
# oracle (d): interface §2 관문 표·§3 T 표 (사용자 승인 계획 N6.40 LM-1e). 거부 순서 = 위에서 아래로 첫 맞는 행.
# ---------------------------------------------------------------------------

MID_LS = (3.25e-6, 3.5e-6, 7.5e-6)


def _mid(**kw):
    return mid_file(1e-6, 1.0, MID_LS, **kw)


def _mid_reject(mid_toy_build, sub, mid, **kw):
    mt = mid_toy_build(sub, mid={0: mid}, **kw)
    with pytest.raises(SchemaRejectedError) as ei:
        mt.load()
    return detail_of(ei.value), mt


def test_lm1e_midpoint_table_fields(mid_toy_build):
    m = _mid()
    m["ID"] = m["ID"].copy()
    m["ID"][0, 0, 0, 0] = 0.0                                       # ID 0 점 -> log_ID·gm_id NaN, on_mask 거짓
    mt = mid_toy_build("mf", mid={0: m})
    lut = mt.load()
    assert set(lut.midpoints) == {("nmos", 100)}                    # 키 = (kind, w_key) -- 폭마다 하나
    t = lut.midpoints[("nmos", 100)]
    assert isinstance(t, MidpointTable)
    assert (t.kind, t.sha256, t.w_m, t.w_key) == ("nmos", sha256_file(mt.mid_path), 1e-6, 100)     # sha256 = 그 파일 raw
    assert tuple(t.L_points) == MID_LS
    assert tuple(tuple(g) for g in t.grids) == (tuple(m["VGS"]), tuple(m["VDS"]), tuple(m["VS"]))
    I, G = m["ID"], m["GM"]
    pos = I > 0
    lg = np.asarray(t.log_ID)
    assert np.isnan(lg[0, 0, 0, 0]) and np.array_equal(lg[pos], np.log(I[pos]))
    gi = np.asarray(t.gm_id)
    assert np.isnan(gi[0, 0, 0, 0]) and np.array_equal(gi[pos], G[pos] / I[pos])
    assert np.array_equal(np.asarray(t.on_mask), (I > 0) & (G > 0))
    assert np.array_equal(np.asarray(t.VDSAT), m["VDSAT"])
    t2 = mid_toy_build("mf2", mid={0: mid_file(1e-6, 1.0, MID_LS, vdsat=False)}).load().midpoints[("nmos", 100)]
    assert t2.VDSAT is None


def test_lm1e_two_midpoint_files_two_tables(mid_toy_build):
    mt = mid_toy_build("two", mid={0: MID_LS, 1: MID_LS})
    lut = mt.load()
    assert set(lut.midpoints) == {("nmos", 100), ("nmos", 200)}
    assert [lut.midpoints[k].w_m for k in (("nmos", 100), ("nmos", 200))] == [1e-6, 2e-6]
    assert lut.provenance.midpoints_sha256 == tuple(sorted(sha256_file(p) for p in mt.mid_paths))


def test_contract_toy_r6_table(toy):
    """7.1 r6 표 첫 세 행(선택 열·중점 파일 없는 r5 toy)."""
    ct = toy.cap_map["nmos"]
    assert (ct.w_key, dict(ct.columns), ct.on_mask, ct.sign_convention, tuple(ct.l_source)) == (100, {}, None, None, ())
    assert dict(toy.slice_map[("nmos", 100)].columns) == {}
    assert dict(toy.midpoints) == {} and toy.provenance.midpoints_sha256 is None


def test_no_midpoints_empty_mapping(mid_toy_build, toy):
    assert dict(toy.midpoints) == {}
    assert dict(mid_toy_build("nm").load().midpoints) == {}


@pytest.mark.parametrize("field,val,key", [("corner", np.str_("ff"), "corner"), ("temp_c", np.float64(85.0), "temp_c")])
def test_lm1e_g5_conditions_mismatch(mid_toy_build, field, val, key):
    """G5: corner·temp_c ≠ 짝 슬라이스 -> lut_conditions_mismatch, key."""
    m = _mid()
    m[field] = val
    det, _ = _mid_reject(mid_toy_build, "cond", m)
    assert det["reason"] == "lut_conditions_mismatch" and det["key"] == key


@pytest.mark.parametrize("axis", ["VGS", "VDS", "VS"])
def test_lm1e_g6_axes_mismatch(mid_toy_build, axis):
    m = _mid()
    a = np.asarray(m[axis], dtype=float).copy()
    a[-1] = np.nextafter(a[-1], 10.0)                               # 1 ulp 도 다르면 거부(float 단위 같음)
    m[axis] = a
    det, _ = _mid_reject(mid_toy_build, "ax", m)
    assert det["reason"] == "lut_midpoints_axes_mismatch"


@pytest.mark.parametrize("drop", ["ID", "GM"])
def test_lm1e_g7_column_missing(mid_toy_build, drop):
    m = _mid()
    del m[drop]
    det, _ = _mid_reject(mid_toy_build, "cm", m)
    assert det["reason"] == "lut_midpoints_column_missing"
    assert det["kind"] == "nmos" and det["column"] == drop


def test_lm1e_g7b_shape_mismatch(mid_toy_build):
    m = _mid()
    m["GM"] = m["GM"][:, :, :, :1]
    det, _ = _mid_reject(mid_toy_build, "sm", m)
    assert det["reason"] == "lut_midpoints_shape_mismatch" and det["column"] == "GM"


def test_lm1e_old_l_source_reasons_never_raised(mid_toy_build):
    """옛 L_source 사유(unrecorded·mismatch)는 없다: meta 에 L_source 가 있어도(기준 LUT 와 다른 sha 라도) 읽지 않고 적재된다."""
    m = _mid()
    m["meta_json"] = np.str_(json.dumps(dict(json.loads(str(m["meta_json"])), L_source={"kind": "cli", "sha256": "b" * 64})))
    lut = mid_toy_build("ls", mid={0: m}, cap_meta={"L_source": {"kind": "json", "sha256": "c" * 64}}).load()
    assert ("nmos", 100) in lut.midpoints


@pytest.mark.parametrize("bad,first", [
    # (고친 것들, 먼저 나와야 할 사유) -- 관문 표 위에서 아래로 첫 맞는 행: G1 -> G4 -> G5 -> G6 -> G7 -> G7b
    ({"drop_w": True, "corner": "ff"}, "lut_midpoints_width_missing"),
    ({"gen": "1" * 64, "corner": "ff"}, "lut_conditions_mismatch"),       # G4 가 G5 보다 먼저(key 로 구분)
    ({"corner": "ff", "axis": "VGS"}, "lut_conditions_mismatch"),         # G5 가 G6 보다 먼저
    ({"axis": "VDS", "drop": "GM"}, "lut_midpoints_axes_mismatch"),       # G6 가 G7 보다 먼저
    ({"drop": "ID", "shape": "GM"}, "lut_midpoints_column_missing"),      # G7 이 G7b 보다 먼저
])
def test_lm1e_gate_order(mid_toy_build, bad, first):
    kw = dict(bad)
    m = mid_file(1e-6, 1.0, MID_LS, mid_meta(**({"generator_sha256": kw["gen"]} if "gen" in kw else {})))
    if kw.get("drop_w"):
        del m["W"]
    if "corner" in kw:
        m["corner"] = np.str_(kw["corner"])
    if "axis" in kw:
        a = np.asarray(m[kw["axis"]], dtype=float).copy()
        a[0] = a[0] - 1e-3
        m[kw["axis"]] = a
    if "drop" in kw:
        del m[kw["drop"]]
    if "shape" in kw:
        m[kw["shape"]] = m[kw["shape"]][:, :, :, :1]
    det, _ = _mid_reject(mid_toy_build, "ord", m)
    assert det["reason"] == first
    if "gen" in kw:
        assert det["key"] == "generator_sha256"
    elif "corner" in kw and not kw.get("drop_w"):
        assert det["key"] == "corner"


@pytest.mark.lut_realdata
def test_real_midpoints_loaded(real_lut, raw_mid):
    """[LM-1e] 적재된 중점 표 = (kind, w_key) 마다 하나, 그 값은 중점 npz 를 numpy 로 직접 읽은 L·W·VDSAT·on_mask 와 같다.
    oracle: (a) 파일 직접 읽기. (어느 (kind, w_key)에 있어야 하는가는 R-1 (i)가 `widths` 로 따로 단언한다.)"""
    assert real_lut.midpoints
    for (kind, wk), t in real_lut.midpoints.items():
        z = raw_mid(kind, wk)
        assert (t.kind, t.w_key) == (kind, wk) and t.w_m == float(z["W"])
        assert tuple(t.L_points) == tuple(float(x) for x in z["L"])
        assert np.array_equal(np.asarray(t.on_mask), (z["ID"] > 0) & (z["GM"] > 0))
        if "VDSAT" in z:
            assert np.array_equal(np.asarray(t.VDSAT), z["VDSAT"])


# ---------------------------------------------------------------------------
# [LM-1e §3 toy T] D7 적재 거부: 슬라이스 앵커 2개 bin 마다 그 슬라이스의 중점 L 가운데 두 앵커 사이인 것이 하나 이상
# (`widths(lut, kind)` 의 키만, 키 오름차순 첫 실패에서 SchemaRejectedError `bin_missing_external`).
# toy T: nmos 슬라이스 0.6·0.8 µm(키 60·80), 앵커 2개 bin = model.1(앵커 3·4 µm)·model.3(앵커 7·8 µm), 중점 L = 3.5 µm(model.1 안)·
# 7.5 µm(model.3 안). oracle (d): interface §3 T 표.
# ---------------------------------------------------------------------------

def _t_reject(mid_toy_build, sub, mids, w_min):
    mt = build_t(mid_toy_build, sub, mids)
    with pytest.raises(SchemaRejectedError) as ei:
        mt.load(t_spec(w_min))
    return detail_of(ei.value)


M1, M3 = "toyn__model.1", "toyn__model.3"


def test_bin_missing_t1_loads(mid_toy_build):
    """T-1 입력은 적재된다(값은 tests/lut/test_tolerance.py)."""
    lut = build_t(mid_toy_build, "t1", {0: T_MID_L, 1: T_MID_L}).load(t_spec(0.6e-6))
    assert set(lut.midpoints) == {("nmos", 60), ("nmos", 80)}


def test_bin_missing_t2_key80_missing(mid_toy_build):
    det = _t_reject(mid_toy_build, "t2", {0: T_MID_L}, 0.6e-6)
    assert det["reason"] == "bin_missing_external"
    assert (det["kind"], det["w_key"], tuple(det["models"])) == ("nmos", 80, (M1, M3))


def test_bin_missing_t3_widths_exclude_key60(mid_toy_build):
    """W_min 0.7 µm 면 키 60 은 `widths` 밖 -- 그래도 키 80 은 중점이 없어 거부(w_key 80)."""
    det = _t_reject(mid_toy_build, "t3", {0: T_MID_L}, 0.7e-6)
    assert det["reason"] == "bin_missing_external" and det["w_key"] == 80


def test_bin_missing_t4_key60_outside_widths_passes(mid_toy_build):
    lut = build_t(mid_toy_build, "t4", {1: T_MID_L}).load(t_spec(0.7e-6))
    assert set(lut.midpoints) == {("nmos", 80)}


def test_bin_missing_t5_partial_key60(mid_toy_build):
    """키 60 에 3.5 µm 만 있고 키 80 은 둘 다: 키 60 의 model.3 에 두 앵커 사이 중점이 없다 -> w_key 60, models (model.3,)."""
    det = _t_reject(mid_toy_build, "t5", {0: (3.5e-6,), 1: T_MID_L}, 0.6e-6)
    assert det["reason"] == "bin_missing_external"
    assert (det["w_key"], tuple(det["models"])) == (60, (M3,))


def test_bin_missing_t6_none(mid_toy_build):
    det = _t_reject(mid_toy_build, "t6", {}, 0.6e-6)
    assert det["reason"] == "bin_missing_external"
    assert (det["w_key"], tuple(det["models"])) == (60, (M1, M3))


def test_bin_missing_t7_toy_spec_passes_without_midpoints(mid_toy_build):
    """T-7: TOY_SPEC(최소 폭 1.5 µm) -- 슬라이스 0.6·0.8 µm 둘 다 `widths` 밖이라 중점 없이 통과."""
    lut = build_t(mid_toy_build, "t7", {}).load(TOY_SPEC)
    assert dict(lut.midpoints) == {}
    assert widths(lut, "nmos") == ()


def test_bin_missing_t9_l_off_grid_rejected_at_load(mid_toy_build):
    """T-9: 키 60 중점 L = (3.505e-6, 7.5e-6) -- 3.505e-6 / 1e-8 = 350.5 비정수 -> G1c lut_midpoints_l_off_grid(detail L_m)."""
    mt = build_t(mid_toy_build, "t9", {0: (3.505e-6, 7.5e-6), 1: T_MID_L})
    with pytest.raises(SchemaRejectedError) as ei:
        mt.load(t_spec(0.6e-6))
    det = detail_of(ei.value)
    assert det["reason"] == "lut_midpoints_l_off_grid" and det["L_m"] == 3.505e-6


def test_bin_missing_only_widths_keys_are_checked(mid_toy_build):
    """`widths` 밖 키(여기서 60)는 앵커 2개 bin 이 비어 있어도 거부하지 않는다 -- 표 셀 구성도 안 바뀐다(키 60 의 midpoints 항 없음)."""
    lut = build_t(mid_toy_build, "t4b", {1: T_MID_L}).load(t_spec(0.7e-6))
    assert widths(lut, "nmos") == (80,) and ("nmos", 60) not in lut.midpoints


# ---------------------------------------------------------------------------


# [r7] VS 축 FC 기록·기울기 열 단위 검사 (계획 DEC-87·N3.7, 설계 41 §4.1 '단위 불일치 -> 로드 거부(SchemaRejectedError)')
# ---------------------------------------------------------------------------

from .conftest import RefSlice, vs_toy_slices  # noqa: E402


def test_vs_hermite_fc_recorded_toy(toy_build):
    """(a) vs toy: VS Hermite 칸 = 3 L × 3 VGS × 2 VDS × 1 VS 칸 = 18, 위반 0(정확한 기울기). GMBS 가 없는 r5 toy 는 ("VS", 0, 0)."""
    lut = toy_build("vs", slices=vs_toy_slices()).load()
    assert lut.slice_map[("nmos", 100)].hermite_fc[2] == ("VS", 18, 0)
    lut0 = toy_build("plain").load()
    assert lut0.slice_map[("nmos", 100)].hermite_fc[2] == ("VS", 0, 0)


def test_vs_fc_violations_counted_toy(toy_build):
    """(a) VS FC 위반 판 vs toy(conftest vs_fc=True, 기울기 자료 일관) -> 18 칸 모두 위반(test__helpers_interp 의 손계산) -- 로드는
    거부하지 않는다(CONTRACT 1.4 '위반이 있어도'). [r7] 옛 입력(GMBS 1000 배)은 단위 검사로 거부된다(아래 test)."""
    lut = toy_build("vsfc", slices=vs_toy_slices(vs_fc=True)).load()
    assert lut.slice_map[("nmos", 100)].hermite_fc[2] == ("VS", 18, 18)


@pytest.mark.parametrize("col", ["GM", "GDS"])
def test_unit_mismatch_rejected_gm_gds(toy_build, col):
    """설계 41 §4.1: 기울기 열이 ln ID 격자 차분과 단위가 다르면(여기서 ×1000, A/V -> mA/V 류 SI 접두 오류) 로드 거부."""
    def bad(W, scale):
        from .conftest import toy_slice_arrays
        a = toy_slice_arrays(W, scale)
        a[col] = a[col] * 1000.0
        return a
    b = toy_build("unit_" + col, slices=[("a.npz", "toyn", bad(1e-6, 1.0)), ("b.npz", "toyn", bad(2e-6, 2.0))])
    with pytest.raises(SchemaRejectedError) as ei:
        b.load()
    d = detail_of(ei.value)
    assert d["reason"] == "lut_unit_mismatch" and d["column"] == col


def test_unit_mismatch_rejected_gmbs(toy_build):
    """[RED 예상 -- 기준 약화 보고] GMBS 는 r7 부터 VS 축 Hermite 의 기울기 열(DEC-87)이라 설계 41 §4.1 '단위 불일치 -> 로드 거부'의 대상이다.
    계약 r7(1.4)은 'toy 슬라이스 호환'을 이유로 GMBS/ID 를 검사에서 뺐다 -- 그 결과 GMBS 가 1000 배(단위 오류)인 슬라이스가 로드되고,
    VS 칸이 모두 FC 위반으로 선형 폴백되며 `gmb` 는 1000 배 값을 조용히 낸다. 기준을 빼는 것은 사용자 승인 사항이라 설계대로 고정한다."""
    b = toy_build("unit_gmbs", slices=vs_toy_slices(gmbs_mult=1000.0))
    with pytest.raises(SchemaRejectedError) as ei:
        b.load()
    d = detail_of(ei.value)
    assert d["reason"] == "lut_unit_mismatch" and d["column"] in ("GMBS", "GMBS_PER_ID")


@pytest.mark.lut_realdata
def test_real_vs_hermite_fc_counts_independent(real_lut, real_slice_files, raw_slice):
    """(b) 실데이터 32 슬라이스: `hermite_fc` 세 항(VDS·VGS·VS) = conftest 독립 FC 판정(RefSlice -- VS 기울기 −GMBS/ID).
    VS 위반은 nmos 72·78 과 pmos 여러 폭의 L 0.15 µm 행에만 있다(독립 계산: nmos 합 353, pmos 합 3,934)."""
    tot = {"nmos": 0, "pmos": 0}
    for kind, _, _, wk, _ in real_slice_files:
        rs = RefSlice(raw_slice(kind, wk))
        assert real_lut.slice_map[(kind, wk)].hermite_fc == rs.hermite_fc(), (kind, wk)
        tot[kind] += rs.hermite_fc()[2][2]
        assert int((~rs.fc_vs[1:]).sum()) == 0, (kind, wk)          # L 0.15 µm 외 행은 위반 없음
    assert tot == {"nmos": 353, "pmos": 3934}



# ---------------------------------------------------------------------------
# [JC-1 §5] LUT 축 키 관문: 적재가 읽는 npz 에 축 키(L·VGS·VDS·VS)가 없으면 분류된 정지 -- 그 자리 기존 축 사유 + detail {path, axis}.
# oracle (d): interface card 20261106-jc1 §5 X-0~X-7 (계획 N6.42 완료 (8) '분류된 정지'). 키를 빼는 것 말고 입력은 같다(X-0: 빼지 않으면 적재 통과).
# **범위 표지(원래 취지와 다름, 위임 A-158 rm2)**: X-7 (중점 파일 `L` 키 결손)은 LM-1e 관문(G1c 'L 제조 격자' 등)이 `L` 을 직접 읽는 자리가 `lut_provenance` 쪽이면 JC-1 이
# W12 파일 칸(`lut_set.py` 중점 자리) 밖을 고치게 만든다 -- 그 경우 이 test 의 통과 조건이 JC-1 범위 확장이다(판정자 확인 항목).
# ---------------------------------------------------------------------------
import os as _os  # noqa: E402

from .conftest import MismatchToy, NoiseToy, TOY_NOISE_SPEC, TOY_SHAPE, mid_file, toy_grid_mesh  # noqa: E402


def _same_path(got, want):
    return _os.path.abspath(str(got)) == _os.path.abspath(str(want))


def _axes_reject(build, reason, path, axis, spec=TOY_SPEC):
    with pytest.raises(SchemaRejectedError) as ei:
        build.load(spec)
    det = detail_of(ei.value)
    assert det["reason"] == reason, det
    assert _same_path(det["path"], path), (det["path"], path)
    assert det["axis"] == axis, det


def _mm_dv():
    L, v, d, s = toy_grid_mesh()
    return {"vth0": np.full(TOY_SHAPE, 1e-3), "toxe": 2e-3 * (1 + v), "voff": 2e-3 + 0 * v}


def _noise_ab():
    L, v, d, s = toy_grid_mesh()
    return 1e-12 * np.exp(v), 1e-16 * np.exp(0.5 * v)


def _x_toy(kind, tmp_path, toy_build, mid_toy_build, drop=None):
    """자리마다 그 자리 앞 관문을 모두 통과하는 기존 toy 에서 npz 의 `drop` 키 하나를 뺀 입력. 반환 (load 가능한 build, 그 npz 경로)."""
    if kind == "cap":
        cap = toy_cap_arrays()
        if drop:
            del cap[drop]
        b = toy_build("x_cap", cap=cap)
        return b, b.cap
    if kind in ("slice1", "slice0"):
        sl = standard_toy_slices()
        i = 0 if kind == "slice0" else 1
        if drop:
            del sl[i][2][drop]
        b = toy_build("x_" + kind, slices=sl)
        return b, b.root / sl[i][0]
    if kind == "mid":
        m = mid_file(1e-6, 1.0, MID_LS)
        if drop:
            del m[drop]
        mt = mid_toy_build("x_mid", mid={0: m})
        return mt, mt.mid_path
    if kind == "mismatch":
        t = MismatchToy(tmp_path / "x_mm", _mm_dv(), mm_mutate=(lambda a: a.pop(drop)) if drop else None)
        return t, t.path
    A, B = _noise_ab()
    t = NoiseToy(tmp_path / "x_noise", A, B, noise_mutate=(lambda a: a.pop(drop)) if drop else None)
    return t, t.path


X_CASES = [
    ("X-1", "cap", "lut_cap_axes_mismatch", TOY_SPEC),
    ("X-2", "slice1", "lut_slice_axes_mismatch", TOY_SPEC),
    ("X-3", "slice0", "lut_slice_axes_mismatch", TOY_SPEC),
    ("X-4", "mid", "lut_midpoints_axes_mismatch", TOY_SPEC),
    ("X-5", "mismatch", "lut_mismatch_axes_mismatch", TOY_SPEC),
    ("X-6", "noise", "lut_noise_axes_mismatch", TOY_NOISE_SPEC),
]


@pytest.mark.parametrize("label,kind,reason,spec", X_CASES, ids=[c[0] for c in X_CASES])
def test_axis_key_missing_vgs_is_classified_stop(tmp_path, toy_build, mid_toy_build, label, kind, reason, spec):
    """X-1~X-6: 자리마다 npz 의 `VGS` 키만 뺀다 -> SchemaRejectedError, reason = 그 자리 기존 축 사유, path = 그 npz, axis "VGS". base 는 분류되지 않은 KeyError.
    X-0 전제(먼저): 같은 toy 에서 키를 빼지 않으면 적재 통과."""
    ok, _ = _x_toy(kind, tmp_path / "ok", toy_build, mid_toy_build)
    ok.load(spec)                                                           # X-0: 앞 관문 통과 입력이다(통과 안 하면 이 test 는 설정 오류)
    bad, path = _x_toy(kind, tmp_path / "bad", toy_build, mid_toy_build, drop="VGS")
    _axes_reject(bad, reason, path, "VGS", spec)


def test_axis_key_missing_first_listed_axis_wins(tmp_path, toy_build, mid_toy_build):
    """axis = 없는 키 가운데 L → VGS → VDS → VS 순서 첫 것(결정성): 기준 폭 표에서 VGS 와 VS 를 함께 빼면 "VGS"."""
    cap = toy_cap_arrays()
    del cap["VGS"], cap["VS"]
    b = toy_build("x_two", cap=cap)
    _axes_reject(b, "lut_cap_axes_mismatch", b.cap, "VGS")


def test_axis_key_x7_midpoint_L_missing_uses_axes_gate_first(mid_toy_build):
    """X-7: 중점 파일의 `L` 키만 뺀다 -> lut_midpoints_axes_mismatch, path = 그 중점 파일, axis "L" (중점 파일 축 키는 `npz_grids` 하나가 처음 읽는다 --
    LM-1e 관문이 `L` 을 직접 읽는 자리가 있어도 그 앞에서 판정). X-0: L 을 빼지 않으면 적재 통과."""
    ok = mid_toy_build("x7_ok", mid={0: mid_file(1e-6, 1.0, MID_LS)})
    ok.load()
    m = mid_file(1e-6, 1.0, MID_LS)
    del m["L"]
    mt = mid_toy_build("x7", mid={0: m})
    _axes_reject(mt, "lut_midpoints_axes_mismatch", mt.mid_path, "L")


# ---------------------------------------------------------------------------
# [FS-1 C-1·C-1'] 후보 0 거부 `wf_candidates_empty` (interface card 20261107-fs1 §2)
# oracle (손): 합성 슬라이스 폭 {1e-6, 2e-6} (격자 1e-8 -> 키 100·200). `widths` = 키·격자 >= min_finger 인 것 -> 최소 폭이 2e-6 를 넘으면 후보 0.
# ---------------------------------------------------------------------------
def _fs1_reload(tmp_path, nmos_min, pmos_min):
    import dataclasses
    from gmid_engine.lut import load_lut_set
    from sizing.conftest import TOY_SPEC as R4_SPEC          # nmos+pmos 두 kind 합성 spec (lut 쪽 TOY_SPEC 은 nmos 하나)
    from sizing.wb1_toy import write_r4_bins_lut
    lut, root, tb = write_r4_bins_lut(tmp_path, widths=(1e-6, 2e-6))
    spec = dataclasses.replace(R4_SPEC,min_finger_w_m=(("nmos", nmos_min), ("pmos", pmos_min)))
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), spec, bin_rule=tb.bin_rule)


def test_wf_candidates_empty_c1_prime_loads_with_two_candidates(tmp_path):
    """C-1' (전제): 최소 폭 1e-6 이면 적재 통과, 후보 (100, 200)."""
    lut = _fs1_reload(tmp_path, 1e-6, 1e-6)
    assert widths(lut, "nmos") == (100, 200)


@pytest.mark.parametrize("nmos_min,pmos_min,kind", [(3e-6, 1e-6, "nmos"), (1e-6, 3e-6, "pmos"), (3e-6, 3e-6, "nmos")])
def test_wf_candidates_empty_rejected(tmp_path, nmos_min, pmos_min, kind):
    """C-1: 최소 finger 폭 > 가장 넓은 슬라이스 -> SchemaRejectedError reason wf_candidates_empty, kind = 그 kind (둘 다면 오름차순 첫 것)."""
    assert widths(_fs1_reload(tmp_path / "ok", 1e-6, 1e-6), "nmos") == (100, 200)      # 양성 대조
    with pytest.raises(SchemaRejectedError) as ei:
        _fs1_reload(tmp_path / "bad", nmos_min, pmos_min)
    d = detail_of(ei.value)
    assert d["reason"] == "wf_candidates_empty" and d["kind"] == kind
