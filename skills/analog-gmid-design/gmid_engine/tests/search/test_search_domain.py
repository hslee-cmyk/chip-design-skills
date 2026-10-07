"""CONTRACT 3.7 [r2·r3] `search_domain(dc_ctx, settings, pdk_decl) -> SearchDomain`.

기대값: θ 스키마 성분 순(L 제외), ln_idu 포락선·전류 상자는 npz 배열 직접 계산(conftest `expect_ln_idu_bounds`·`expect_box`),
저항 상자 = 선언 ln, grid/w_min = toy PDK 선언 값, b_A = 둘의 곱.
"""
import math

import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.search import SearchDomain, SearchSettings, Variable, search_domain

from .conftest import (
    GRID,
    R4_L,
    SRC,
    W_MIN,
    build_case,
    circuit_c,
    circuit_p,
    expect_box,
    expect_ln_idu_bounds,
    r4_arrays,
    write_pdk,
)

KIND = {"M1": "nmos", "M2": "pmos"}


def _settings(rb=None, eb=40):
    return SearchSettings(600.0, eb, rb, SRC)


def test_circuit_c_domain(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    d = search_domain(case.dc, _settings(), case.pdk)
    assert isinstance(d, SearchDomain)
    comps = [c for c in case.dc.schema.components if c[0] != "L"]
    assert [v.component for v in d.variables] == comps
    arr = {k: r4_arrays(k) for k in ("nmos", "pmos")}
    for v in d.variables:
        assert isinstance(v, Variable)
        t, key = v.component
        if t == "ln_idu":
            lo, hi = expect_ln_idu_bounds(arr[KIND[key]])
            assert (v.log, v.lo, v.hi) == (False, pytest.approx(lo, rel=1e-12), pytest.approx(hi, rel=1e-12))
        elif t == "y":
            assert (v.log, v.lo, v.hi) == (False, 0.0, 1.0)
        elif t == "current":                     # 기저 원소 M2 = MOS -> pmos 상자
            i_off, i_max = expect_box(arr["pmos"], [arr["pmos"]])
            assert v.log is True
            assert v.lo == pytest.approx(math.log(i_off), rel=1e-12)
            assert v.hi == pytest.approx(math.log(i_max), rel=1e-12)
        else:
            raise AssertionError(v)
    assert d.l_cells == (("M1", tuple((a, a) for a in R4_L)), ("M2", tuple((a, a) for a in R4_L)))
    assert d.grid_m == pytest.approx(GRID, rel=1e-12)
    assert d.w_min_m == pytest.approx(W_MIN, rel=1e-12)
    assert d.area_resolution_m2 == pytest.approx(GRID * W_MIN, rel=1e-12)
    assert [k for k, _ in d.current_box] == ["nmos", "pmos"]
    for k, box in d.current_box:
        assert tuple(box) == pytest.approx(expect_box(arr[k], [arr[k]]), rel=1e-12)


def test_resistor_variable_and_non_mos_current(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=(1e3, 1e6))
    d = search_domain(case.dc, _settings((1e3, 1e6)), case.pdk)
    vs = {v.component: v for v in d.variables}
    r = vs[("resistance", "R1")]
    assert r.log is True
    assert (r.lo, r.hi) == (pytest.approx(math.log(1e3), rel=1e-15), pytest.approx(math.log(1e6), rel=1e-15))
    cur = [v for c, v in vs.items() if c[0] == "current"]
    assert len(cur) == 1
    # 기저 원소가 M1(MOS) 이든 R1(원뿔 행에 R1 항을 갖는 MOS = M1) 이든 pmos 상자.
    arr = r4_arrays("pmos")
    i_off, i_max = expect_box(arr, [arr])
    assert (cur[0].lo, cur[0].hi) == (pytest.approx(math.log(i_off), rel=1e-12), pytest.approx(math.log(i_max), rel=1e-12))


def test_resistor_bounds_undeclared_rejected(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=(1e3, 1e6))
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(case.dc, _settings(None), case.pdk)
    det = dict(e.value.record.detail)
    assert det["gate"] == "search_domain"
    assert det["reason"] == "theta_resistance_bounds_undeclared"
    assert tuple(det["resistors"]) == ("R1",)


@pytest.mark.parametrize("rb", [(1e5, 1e5), (2e5, 1e5)])
def test_empty_box_value_error(tmp_path, lut_sealed, rb):
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=(1e3, 1e6))
    with pytest.raises(ValueError):
        search_domain(case.dc, _settings(rb), case.pdk)


def test_type_errors(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(TypeError):
        search_domain(case.dc, (600.0, 40, None, ()), case.pdk)
    with pytest.raises(TypeError):
        search_domain(case.dc, _settings(), {"manufacturing_grid_m": 1e-8})


def test_pdk_without_min_finger_rejected(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    pdk = write_pdk(tmp_path / "pdk2", with_minw=False)
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(case.dc, _settings(), pdk)
    assert dict(e.value.record.detail)["reason"] == "pdk_quantity_undeclared"


def test_pdk_values_follow_declaration(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    pdk = write_pdk(tmp_path / "pdk3", grid_um="0.005", minw_um="0.42")
    d = search_domain(case.dc, _settings(), pdk)
    assert d.grid_m == pytest.approx(5e-9, rel=1e-12)
    assert d.w_min_m == pytest.approx(4.2e-7, rel=1e-12)
    assert d.area_resolution_m2 == pytest.approx(5e-9 * 4.2e-7, rel=1e-12)
