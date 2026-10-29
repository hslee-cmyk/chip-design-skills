"""`_helpers_columns` (column_source) -- CONTRACT 1.2·1.4·4.3 [r6], 공개 API 경유(`vdsat`·`gmb`·`tol_vdsat_table` 의 출처,
`DcSlice.columns`·`CapTable.columns`·`on_mask`·`sign_convention`·`l_source`, 로드 거부).

열 출처 규칙: (1) 슬라이스 (kind, w_key) 의 columns 에 열이 있으면 "slice" (2) 아니면 cap_map[kind].w_key == w_key 이고 기준 LUT
columns 에 있으면 "cap_table" (3) 아니면 required 면 `lut_column_unavailable`(detail column, kind, w_key, cap_w_key, slice_columns,
cap_columns -- 뒤 둘은 이름 정렬 tuple), 아니면 None. **다른 폭의 열로 대신하지 않는다.** 슬라이스 없음 -> KeyError.
파생 열 GMBS_PER_ID = GMBS/ID(ID > 0, 아니면 NaN). 기대값은 toy 배열(손으로 정한 식)과 npz 직접 읽기.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import (CAP_TABLE_COLUMNS, COLUMN_ORIGINS, DERIVED_COLUMNS, SLICE_OPTIONAL_COLUMNS, gmb, op_point,
                             tol_vdsat_table, vdsat)

from .conftest import (TOY_VGS, detail_of, new_memo, r6_toy_cap_arrays, rel_close, toy_cap_arrays, toy_id,
                       toy_slice_arrays)

PT = (1e-6, 0.25, 0.75, 0.25)              # (L 앵커, vgs, vds, vsb) -- VGS 칸 중앙


def _vdsat_arr(a, b):
    V = np.empty((3, 3, 2, 2))
    V[...] = (a + b * np.asarray(TOY_VGS))[None, :, None, None]
    return V


def _slices(w100_cols=None, w200_cols=None):
    a = toy_slice_arrays(1e-6, 1.0)
    b = toy_slice_arrays(2e-6, 2.0)
    a.update(w100_cols or {})
    b.update(w200_cols or {})
    return [("toy_w100.npz", "toyn", a), ("toy_w200.npz", "toyn", b)]


def _unavailable(fn, *args):
    with pytest.raises(SealViolationError) as ei:
        fn(*args)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_column_unavailable"
    return det


def test_constants():
    assert CAP_TABLE_COLUMNS == ("CDD", "CSS", "GDS", "GM", "GMBS", "ID", "SVG2_1HZ", "SVG2_HF", "VDSAT", "VTH")
    assert SLICE_OPTIONAL_COLUMNS == ("GMBS", "VDSAT")
    assert DERIVED_COLUMNS == ("GMBS_PER_ID",)
    assert set(COLUMN_ORIGINS) == {"slice", "cap_table"}


def test_cap_table_origin_only_for_cap_width(toy_build):
    """7.1 r6 마지막 행: 기준 LUT(w_key 100)에만 VDSAT·GMBS -> w_key 100 은 "cap_table", w_key 200 은 lut_column_unavailable
    (폭 100 의 열로 대신하지 않는다)."""
    lut = toy_build("capcol", cap=r6_toy_cap_arrays()).load()
    m = new_memo(lut)
    assert lut.cap_map["nmos"].w_key == 100
    assert rel_close(vdsat(m, "nmos", 100, *PT), 0.15, 1e-12)
    assert tol_vdsat_table(m, "nmos", 100).origin == "cap_table"
    det = _unavailable(vdsat, m, "nmos", 200, *PT)
    assert (det["column"], det["kind"], det["w_key"], det["cap_w_key"]) == ("VDSAT", "nmos", 200, 100)
    assert tuple(det["slice_columns"]) == ()
    assert tuple(det["cap_columns"]) == ("GMBS", "GMBS_PER_ID", "ID", "VDSAT")   # 파생 열 포함, 이름 정렬
    det = _unavailable(tol_vdsat_table, m, "nmos", 200)
    assert det["w_key"] == 200 and det["column"] == "VDSAT"


def test_slice_column_wins_over_cap_table(toy_build):
    """같은 폭에 둘 다 있으면 슬라이스 열(값으로 출처를 가린다: 슬라이스 0.3 + 0.1·VGS, 기준 LUT 0.1 + 0.2·VGS)."""
    lut = toy_build("both", slices=_slices(w100_cols={"VDSAT": _vdsat_arr(0.3, 0.1)}),
                    cap=r6_toy_cap_arrays()).load()
    m = new_memo(lut)
    assert rel_close(vdsat(m, "nmos", 100, *PT), 0.3 + 0.1 * 0.25, 1e-12)
    assert tol_vdsat_table(m, "nmos", 100).origin == "slice"


def test_slice_column_at_other_width_and_cap_fallback(toy_build):
    """폭 200 슬라이스에만 열, 기준 LUT(키 100)에도 열: w100 -> cap_table 값, w200 -> slice 값."""
    lut = toy_build("mix", slices=_slices(w200_cols={"VDSAT": _vdsat_arr(0.3, 0.1)}), cap=r6_toy_cap_arrays()).load()
    m = new_memo(lut)
    assert rel_close(vdsat(m, "nmos", 100, *PT), 0.15, 1e-12)
    assert rel_close(vdsat(m, "nmos", 200, *PT), 0.325, 1e-12)
    assert tol_vdsat_table(m, "nmos", 100).origin == "cap_table"
    assert tol_vdsat_table(m, "nmos", 200).origin == "slice"


def test_no_cross_width_from_other_slice(toy_build):
    """음성: 폭 100 슬라이스에만 VDSAT, 기준 LUT 에는 없음 -> 폭 200 조회는 거부(폭 100 열을 빌리지 않는다)."""
    lut = toy_build("cross", slices=_slices(w100_cols={"VDSAT": _vdsat_arr(0.3, 0.1)})).load()
    m = new_memo(lut)
    assert rel_close(vdsat(m, "nmos", 100, *PT), 0.325, 1e-12)
    det = _unavailable(vdsat, m, "nmos", 200, *PT)
    assert tuple(det["slice_columns"]) == () and tuple(det["cap_columns"]) == ()
    assert det["cap_w_key"] == 100


def test_cap_key_matching_no_slice_width(toy_build):
    """음성: 기준 LUT 폭 키 150(어느 슬라이스와도 다름)에 VDSAT -> 두 폭 모두 lut_column_unavailable, detail cap_w_key 150."""
    cap = r6_toy_cap_arrays()
    cap["w_ref_m"] = np.float64(1.5e-6)
    lut = toy_build("k150", cap=cap).load()
    m = new_memo(lut)
    for wk in (100, 200):
        det = _unavailable(vdsat, m, "nmos", wk, *PT)
        assert det["cap_w_key"] == 150 and det["w_key"] == wk


def test_missing_slice_is_keyerror(toy_build):
    m = new_memo(toy_build("ke", cap=r6_toy_cap_arrays()).load())
    with pytest.raises(KeyError):
        vdsat(m, "nmos", 150, *PT)


def test_gmb_column_not_required_falls_back(toy_build):
    """GMBS_PER_ID 는 required=False: w_key 100(cap_table 열) -> 0.25·ID(점), w_key 200(열 없음) -> r5 VS 할선(거부 아님)."""
    lut = toy_build("gmbfb", cap=r6_toy_cap_arrays()).load()
    m = new_memo(lut)
    L, vgs, vds, vsb = 1e-6, 0.25, 0.5, 0.0
    idp = op_point(m, "nmos", 100, L, vgs, vds, vsb).IDu * 1e-6 / L
    assert rel_close(gmb(m, "nmos", 100, L, vgs, vds, vsb), 0.25 * idp, 1e-12)
    id200 = op_point(m, "nmos", 200, L, vgs, vds, vsb).IDu * 2e-6 / L
    secant = -id200 * math.log(0.5) / 0.5                              # r5 toy VS 방향 ln ID 기울기 ln(0.5)/0.5
    assert rel_close(gmb(m, "nmos", 200, L, vgs, vds, vsb), secant, 1e-12)


# ---------------------------------------------------------------------------
# 열 로드 (1.2·1.4): DcSlice.columns·CapTable.columns·파생 열·on_mask·meta
# ---------------------------------------------------------------------------

# [r7 2026-10-09 단위 검사 복원(CONTRACT 1.4)] 슬라이스 GMBS 는 ln ID 의 VS 기울기와 맞아야 로드된다. r5 toy 의 ln ID VS 몫은
# ln(0.5)·vsb/0.5(CONTRACT 7.1 닫힌 식) -> −GMBS/ID = 2·ln 0.5, GMBS = 2·ln2·ID (oracle (a) 구성). 옛 값 0.4·ID 는 VS 칸 18 개 모두
# 현 −1.39 대 끝 기울기 −0.4 로 1.4 위반(로드 거부)이었다. 열 로드·파생 열 확인이 목적이라 값만 일관되게 바꾼다.
R5_GMBS_PER_ID = 2.0 * math.log(2.0)


def test_slice_columns_and_derived(toy_build):
    a_cols = {"GMBS": toy_id(1.0) * R5_GMBS_PER_ID, "VDSAT": _vdsat_arr(0.3, 0.1)}
    a_cols["GMBS"][0, 0, 0, 0] = 1e-9
    lut = toy_build("sc", slices=_slices(w100_cols=a_cols)).load()
    sl = lut.slice_map[("nmos", 100)]
    assert set(sl.columns) == {"GMBS", "VDSAT", "GMBS_PER_ID"}
    assert np.array_equal(np.asarray(sl.columns["VDSAT"]), a_cols["VDSAT"])
    exp = a_cols["GMBS"] / toy_id(1.0)
    np.testing.assert_array_equal(np.asarray(sl.columns["GMBS_PER_ID"]), exp)
    assert dict(lut.slice_map[("nmos", 200)].columns) == {}
    with pytest.raises(TypeError):                                    # 1.4: 읽기 전용 매핑
        sl.columns["X"] = np.zeros(1)
    with pytest.raises(TypeError):
        lut.cap_map["nmos"].columns["X"] = np.zeros(1)


def test_derived_gmbs_per_id_nan_where_id_not_positive(toy_build):
    ida = toy_slice_arrays(1e-6, 1.0)
    ida["ID"] = ida["ID"].copy()
    ida["ID"][0, 0, 0, 0] = 0.0
    ida["GMBS"] = toy_id(1.0) * R5_GMBS_PER_ID
    lut = toy_build("nan", slices=[("toy_w100.npz", "toyn", ida), ("toy_w200.npz", "toyn", toy_slice_arrays(2e-6, 2.0))]).load()
    r = np.asarray(lut.slice_map[("nmos", 100)].columns["GMBS_PER_ID"])
    assert math.isnan(r[0, 0, 0, 0])
    assert np.isfinite(np.delete(r.ravel(), 0)).all()


def test_cap_columns_derived_on_mask_and_meta(toy_build):
    cap = r6_toy_cap_arrays()
    cap["GM_n"] = cap["ID_n"] * 5.0
    cap["GM_n"][1, 1, 0, 0] = 0.0
    cap["CDD_n"] = np.full((3, 3, 2, 2), 3e-16)
    cap["meta_json"] = np.str_('{"sign_convention": "keep sign", "L_source": {"sha256": "ab", "kind": "json"}}')
    lut = toy_build("capmeta", cap=cap).load()
    ct = lut.cap_map["nmos"]
    assert set(ct.columns) == {"CDD", "GM", "GMBS", "ID", "VDSAT", "GMBS_PER_ID"}
    np.testing.assert_array_equal(np.asarray(ct.columns["GMBS_PER_ID"]), cap["GMBS_n"] / cap["ID_n"])
    exp_on = (cap["ID_n"] > 0) & (cap["GM_n"] > 0)
    assert np.array_equal(np.asarray(ct.on_mask), exp_on) and not exp_on.all()
    assert ct.sign_convention == "keep sign"
    assert tuple(ct.l_source) == (("kind", "json"), ("sha256", "ab"))


def test_cap_on_mask_none_without_gm(toy_build):
    ct = toy_build("nogm", cap=r6_toy_cap_arrays()).load().cap_map["nmos"]
    assert ct.on_mask is None
    assert ct.sign_convention is None and tuple(ct.l_source) == ()


def test_old_style_set_without_columns_loads(toy_build):
    lut = toy_build("plain").load()
    assert dict(lut.cap_map["nmos"].columns) == {}
    assert all(dict(sl.columns) == {} for sl in lut.slice_map.values())


@pytest.mark.parametrize("col", ["VDSAT_n", "GMBS_n", "CSS_n", "SVG2_HF_n"])
def test_reject_cap_column_shape_mismatch(toy_build, col):
    cap = toy_cap_arrays()
    cap[col] = np.zeros((3, 3, 2, 3))
    with pytest.raises(SchemaRejectedError) as ei:
        toy_build("shp", cap=cap).load()
    det = detail_of(ei.value)
    assert det["reason"] == "lut_cap_shape_mismatch" and det["column"] == col and "path" in det


@pytest.mark.parametrize("col", ["GMBS", "VDSAT"])
def test_reject_slice_optional_shape_mismatch(toy_build, col):
    with pytest.raises(SchemaRejectedError) as ei:
        toy_build("sshp", slices=_slices(w200_cols={col: np.zeros((3, 3, 2, 3))})).load()
    det = detail_of(ei.value)
    assert det["reason"] == "lut_slice_shape_mismatch" and det["array"] == col


# ---------------------------------------------------------------------------
# 실데이터: LUT v2(결정 B 재생성 슬라이스 -- 모든 폭 "slice"), 결정 B 이전 v2 슬라이스(w_key 1000 만 "cap_table"), 옛 12-L 세트
# ---------------------------------------------------------------------------

@pytest.mark.lut_realdata
def test_real_v2_all_widths_slice_origin(real_lut, raw_slice):
    for (kind, wk), sl in sorted(real_lut.slice_map.items()):
        assert set(sl.columns) == {"GMBS", "VDSAT", "GMBS_PER_ID"}, (kind, wk)
    m = new_memo(real_lut)
    for kind, wk in (("nmos", 72), ("nmos", 1000), ("pmos", 84), ("pmos", 1000)):
        assert tol_vdsat_table(m, kind, wk).origin == "slice"
        z = raw_slice(kind, wk)
        iL, iG, k, s = 11, 30, 30, 3
        got = vdsat(m, kind, wk, float(z["L"][iL]), float(z["VGS"][iG]), float(z["VDS"][k]), float(z["VS"][s]))
        assert got == float(z["VDSAT"][iL, iG, k, s])                 # 격자점은 슬라이스 저장값 그대로


@pytest.mark.lut_realdata
def test_real_cap_columns_loaded(real_lut, raw_cap):
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        ct = real_lut.cap_map[kind]
        assert set(ct.columns) == set(CAP_TABLE_COLUMNS) | {"GMBS_PER_ID"}
        for col in CAP_TABLE_COLUMNS:
            assert np.array_equal(np.asarray(ct.columns[col]), raw_cap[col + suf]), (kind, col)
        I, G = raw_cap["ID" + suf], raw_cap["GM" + suf]
        assert np.array_equal(np.asarray(ct.on_mask), (I > 0) & (G > 0))
        assert ct.sign_convention == __import__("json").loads(str(raw_cap["meta_json"]))["sign_convention"]
        assert dict(ct.l_source)["sha256"] == __import__("json").loads(str(raw_cap["meta_json"]))["L_source"]["sha256"]


@pytest.mark.lut_realdata
def test_real_nocol_v2_slices_cap_table_only_at_1000(nocol_lut, raw_cap):
    """결정 B 이전 v2 슬라이스(GMBS·VDSAT 없음): w_key 1000 만 "cap_table"(기준 LUT 폭 키 1000), 다른 폭은 lut_column_unavailable."""
    assert all(dict(sl.columns) == {} for sl in nocol_lut.slice_map.values())
    m = new_memo(nocol_lut)
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        assert tol_vdsat_table(m, kind, 1000).origin == "cap_table"
        Lg = raw_cap["L"]
        iL, iG, k, s = 11, 30, 30, 3
        got = vdsat(m, kind, 1000, float(Lg[iL]), float(raw_cap["VGS"][iG]), float(raw_cap["VDS"][k]),
                    float(raw_cap["VS"][s]))
        assert got == float(raw_cap["VDSAT" + suf][iL, iG, k, s])
        other = min(wk for (kd, wk) in nocol_lut.slice_map if kd == kind)
        det = _unavailable(vdsat, m, kind, other, float(Lg[iL]), 0.9, 0.9, 0.0)
        assert det["cap_w_key"] == 1000 and tuple(det["slice_columns"]) == ()
        assert "VDSAT" in tuple(det["cap_columns"])


