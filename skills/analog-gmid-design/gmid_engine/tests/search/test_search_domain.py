"""CONTRACT 3.7 [r2·r3·r10] `search_domain(dc_ctx, settings, pdk_decl, spec_bounds=()) -> SearchDomain`.

기대값: θ 스키마 성분 순(L 제외), ln_idu 포락선·전류 상자는 npz 배열 직접 계산(conftest `expect_ln_idu_bounds`·`expect_box`),
저항 상자 = 선언 ln, grid/w_min = toy PDK 선언 값, b_A = 둘의 곱.
"""
import math

import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.search import SearchDomain, SearchSettings, Variable, search_domain

from .conftest import (
    CODE_FP,
    GRID,
    R4_L,
    SRC,
    W_MIN,
    Z_ELEMENTS,
    build_case,
    circuit_c,
    circuit_p,
    circuit_z,
    expect_box,
    expect_ln_idu_bounds,
    mos,
    r4_arrays,
    topo,
    two,
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


# ---------------------------------------------------------------- [r6] DEC-92 수동소자 θ 상자 · 모르는 θ 종류 · [r5] current_box kind

def test_passive_theta_variables_use_declared_boxes(tmp_path, lut_sealed):
    """r6: capacitance -> (ln, capacitance_bounds_f), ss_resistance -> (ln, resistance_bounds_ohm)."""
    rb, cb = (1e2, 1e6), (1e-14, 1e-10)
    case = build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=rb, cbounds=cb)
    comps = case.dc.schema.components
    assert ("capacitance", "Cz") in comps and ("ss_resistance", "Rz") in comps      # 입력 확인(sizing r5)
    d = search_domain(case.dc, SearchSettings(600.0, 40, rb, SRC, cb), case.pdk)
    vs = {v.component: v for v in d.variables}
    assert [v.component for v in d.variables] == [c for c in comps if c[0] != "L"]
    c, r = vs[("capacitance", "Cz")], vs[("ss_resistance", "Rz")]
    assert c.log is True and (c.lo, c.hi) == (pytest.approx(math.log(cb[0]), rel=1e-15),
                                              pytest.approx(math.log(cb[1]), rel=1e-15))
    assert r.log is True and (r.lo, r.hi) == (pytest.approx(math.log(rb[0]), rel=1e-15),
                                              pytest.approx(math.log(rb[1]), rel=1e-15))


def test_capacitance_bounds_undeclared_rejected(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10))
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(case.dc, SearchSettings(600.0, 40, (1e2, 1e6), SRC), case.pdk)
    det = dict(e.value.record.detail)
    assert (det["gate"], det["reason"]) == ("search_domain", "theta_capacitance_bounds_undeclared")
    assert tuple(det["capacitors"]) == ("Cz",)


def test_ss_resistance_needs_resistor_bounds(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10))
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(case.dc, SearchSettings(600.0, 40, None, SRC, (1e-14, 1e-10)), case.pdk)
    det = dict(e.value.record.detail)
    assert det["reason"] == "theta_resistance_bounds_undeclared"
    assert "Rz" in tuple(det["resistors"])


@pytest.mark.parametrize("cb", [(1e-12, 1e-12), (2e-12, 1e-12)])
def test_empty_capacitance_box_value_error(tmp_path, lut_sealed, cb):
    case = build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10))
    with pytest.raises(ValueError):
        search_domain(case.dc, SearchSettings(600.0, 40, (1e2, 1e6), SRC, cb), case.pdk)


def test_unknown_theta_kind_value_error(tmp_path, lut_sealed):
    """r6: 모르는 θ 종류는 조용히 건너뛰지 않고 ValueError."""
    import dataclasses
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    sch = case.dc.schema
    bad = dataclasses.replace(sch, components=tuple(sorted(sch.components + (("bogus_kind", "X"),))))
    dc2 = dataclasses.replace(case.dc, schema=bad)
    with pytest.raises(ValueError):
        search_domain(dc2, _settings(), case.pdk)


def test_capacitance_bounds_default_none():
    assert SearchSettings(600.0, 40, None, SRC).capacitance_bounds_f is None


def test_current_box_kinds_are_circuit_mos_kinds(tmp_path, lut_sealed):
    """r5: current_box 의 kind = 회로 S1 의 MOS kind 집합(이름순) -- 회로 P 는 pmos 만."""
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=(1e3, 1e6))
    d = search_domain(case.dc, _settings((1e3, 1e6)), case.pdk)
    assert [k for k, _ in d.current_box] == ["pmos"]
    arr = r4_arrays("pmos")
    assert tuple(d.current_box[0][1]) == pytest.approx(expect_box(arr, [arr]), rel=1e-12)


# ---------------------------------------------------------------- [r10] 원소별 θ 수동소자 상자 (사용자 결정 8·10)
# 우선순위(CONTRACT r10): SearchSettings 재정의(그 종류 모든 원소) > spec `search.theta_bounds.<원소>` > 거부(상자 없는 원소만, θ 순).
# 기대값 = 이 test 가 spec 에 적은 상자 값의 ln(구성으로 정해진 합성 입력, oracle (a)) -- 피검 함수 출력으로 만들지 않는다.

TB_SRC = {"kind": "user_spec", "record": "search test theta box", "decided": "2026-10-08"}


def circuit_rr():
    """회로 RR: M1 pmos (out, in, vdd) + R1 (out, x) + R2 (x, gnd) -- 둘 다 DC 경로 engine 저항 -> θ `resistance` 두 개(sizing 4.4)."""
    return topo("hand_prr", [mos("M1", "pmos", "out", "in", "vdd")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                passives=[two("R1", "resistor", "out", "x"), two("R2", "resistor", "x", "gnd")])


def circuit_cc():
    """회로 CC: 회로 C + C1 (out, gnd) + C2 (out, gnd) -- 둘 다 engine 커패시터 -> θ `capacitance` 두 개(sizing 4.4 r5)."""
    d = circuit_c()
    d["passive_elements"] = [two("C1", "capacitor", "out", "gnd"), two("C2", "capacitor", "out", "gnd")]
    return d


RR_ELEMENTS = (("R1", "resistor", None), ("R2", "resistor", None))
CC_ELEMENTS = (("C1", "capacitor", None), ("C2", "capacitor", None))


def _dc_with_boxes(tmp, topo_doc, lut, elements, boxes):
    """spec JSON(metrics conftest `spec_json`)의 search 에 theta_bounds = boxes {원소: (min, max)} 를 적어 authoring 로더로 읽고
    KernelContext 를 만든다. -> (spec, dc, pdk, rule, spec_bounds)."""
    import json
    from pathlib import Path

    from gmid_engine.authoring import THETA_BOUNDS, load_sizing_spec, load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.metrics import metric_catalog
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    from metrics.conftest import spec_json

    from .conftest import SUPPLIES, new_access, write_decls

    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    tp = tmp / (topo_doc["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo_doc, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    doc = spec_json(td, SUPPLIES, list(elements), (), ())
    if boxes is not None:
        doc["human"]["search"]["theta_bounds"] = {n: {"min": lo, "max": hi, "source": dict(TB_SRC)}
                                                  for n, (lo, hi) in boxes.items()}
    sp = tmp / (topo_doc["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    inputs = dc_inputs_from_spec(spec)
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v)), inputs, new_access(lut))
    pdk, rule = write_decls(tmp / "pdk")
    found = [s.value for s in spec.search if s.field == THETA_BOUNDS]
    return spec, dc, pdk, rule, (found[0] if found else ())


def _bounds(domain):
    return {v.component: (v.log, v.lo, v.hi) for v in domain.variables
            if v.component[0] in ("resistance", "ss_resistance", "capacitance")}


def _ln(lo, hi):
    return (True, pytest.approx(math.log(lo), rel=1e-15), pytest.approx(math.log(hi), rel=1e-15))


def test_spec_boxes_apply_per_element(tmp_path, lut_sealed):
    """재정의 없음 -> 원소마다 spec 상자(R1·R2 서로 다른 상자). build_search_context 도 spec 상자를 넘긴다(r10 2)."""
    from gmid_engine.search import build_search_context
    boxes = {"R1": (1e3, 1e6), "R2": (1e4, 1e7)}
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path, circuit_rr(), lut_sealed, RR_ELEMENTS, boxes)
    comps = dc.schema.components
    assert ("resistance", "R1") in comps and ("resistance", "R2") in comps        # 입력 확인(sizing 4.4)
    assert [(t.element, t.kind, t.lo, t.hi) for t in sb] == [("R1", "resistor", 1e3, 1e6), ("R2", "resistor", 1e4, 1e7)]
    want = {("resistance", "R1"): _ln(1e3, 1e6), ("resistance", "R2"): _ln(1e4, 1e7)}
    assert _bounds(search_domain(dc, _settings(None), pdk, sb)) == want
    sctx = build_search_context(dc, spec, _settings(None), None, pdk, rule, code_fp=CODE_FP)
    assert _bounds(sctx.domain) == want


def test_settings_override_applies_to_all_elements_of_kind(tmp_path, lut_sealed):
    """SearchSettings.resistance_bounds_ohm 이 None 아님 -> 그 run 의 모든 저항 원소에 그 상자(spec 상자 무시, r10 1)."""
    from gmid_engine.search import build_search_context
    boxes = {"R1": (1e3, 1e6), "R2": (1e4, 1e7)}
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path, circuit_rr(), lut_sealed, RR_ELEMENTS, boxes)
    want = {("resistance", "R1"): _ln(50.0, 5e5), ("resistance", "R2"): _ln(50.0, 5e5)}
    assert _bounds(search_domain(dc, _settings((50.0, 5e5)), pdk, sb)) == want
    sctx = build_search_context(dc, spec, _settings((50.0, 5e5)), None, pdk, rule, code_fp=CODE_FP)
    assert _bounds(sctx.domain) == want


def test_override_also_covers_unboxed_elements(tmp_path, lut_sealed):
    """재정의는 spec 상자가 없는 원소에도 적용된다 -- R1 만 상자, 재정의 있으면 거부 없이 R1·R2 모두 재정의 상자."""
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path, circuit_rr(), lut_sealed, RR_ELEMENTS, {"R1": (1e3, 1e6)})
    got = _bounds(search_domain(dc, _settings((2e2, 2e5)), pdk, sb))
    assert got == {("resistance", "R1"): _ln(2e2, 2e5), ("resistance", "R2"): _ln(2e2, 2e5)}


def test_unboxed_resistor_rejected_listing_only_unboxed(tmp_path, lut_sealed):
    """재정의 없음·R1 만 상자 -> SchemaRejectedError(gate search_domain, theta_resistance_bounds_undeclared, resistors = (R2,))."""
    from gmid_engine.search import build_search_context
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path, circuit_rr(), lut_sealed, RR_ELEMENTS, {"R1": (1e3, 1e6)})
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(dc, _settings(None), pdk, sb)
    det = dict(e.value.record.detail)
    assert (det["gate"], det["reason"]) == ("search_domain", "theta_resistance_bounds_undeclared")
    assert tuple(det["resistors"]) == ("R2",)
    with pytest.raises(SchemaRejectedError) as e2:                       # build_search_context 경로도 같은 거부
        build_search_context(dc, spec, _settings(None), None, pdk, rule, code_fp=CODE_FP)
    assert tuple(dict(e2.value.record.detail)["resistors"]) == ("R2",)


def test_no_spec_boxes_reject_lists_all_in_theta_order(tmp_path, lut_sealed):
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path, circuit_rr(), lut_sealed, RR_ELEMENTS, None)
    assert sb == ()
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(dc, _settings(None), pdk, sb)
    assert tuple(dict(e.value.record.detail)["resistors"]) == ("R1", "R2")


def test_capacitors_spec_box_override_and_reject(tmp_path, lut_sealed):
    """커패시터도 같은 우선순위: spec 원소별 / capacitance_bounds_f 재정의(모두) / 없는 원소만 거부(capacitors).
    [r12] 회로 CC 의 C1·C2 는 연결이 같은 자기동형 궤도(sizing 3.0b)라 기본은 한 변수로 묶인다(3.24) -- 원소별로 다른 spec 상자는
    `untie`(spec untie_orbits)로 풀어야 받고, 풀지 않으면 tied_orbit_bounds_differ. 재정의는 두 원소에 같은 상자라 묶인 채 대표 하나."""
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path / "a", circuit_cc(), lut_sealed, CC_ELEMENTS,
                                             {"C1": (1e-13, 1e-11), "C2": (2e-13, 5e-12)})
    comps = dc.schema.components
    assert ("capacitance", "C1") in comps and ("capacitance", "C2") in comps
    assert _bounds(search_domain(dc, _settings(None), pdk, sb, untie=("C1",))) == {
        ("capacitance", "C1"): _ln(1e-13, 1e-11), ("capacitance", "C2"): _ln(2e-13, 5e-12)}
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(dc, _settings(None), pdk, sb)
    assert dict(e.value.record.detail)["reason"] == "tied_orbit_bounds_differ"
    ov = SearchSettings(600.0, 40, None, SRC, (1e-14, 1e-10))
    assert _bounds(search_domain(dc, ov, pdk, sb, untie=("C2",))) == {
        ("capacitance", "C1"): _ln(1e-14, 1e-10), ("capacitance", "C2"): _ln(1e-14, 1e-10)}
    tied = search_domain(dc, ov, pdk, sb)
    got = _bounds(tied)
    assert len(got) == 1 and list(got.values()) == [_ln(1e-14, 1e-10)]
    assert {frozenset((r,) + tuple(m)) for r, m in tied.ties if r[0] == "capacitance"} == {
        frozenset({("capacitance", "C1"), ("capacitance", "C2")})}
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path / "b", circuit_cc(), lut_sealed, CC_ELEMENTS, {"C2": (1e-13, 1e-11)})
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(dc, _settings(None), pdk, sb)
    det = dict(e.value.record.detail)
    assert (det["gate"], det["reason"]) == ("search_domain", "theta_capacitance_bounds_undeclared")
    assert tuple(det["capacitors"]) == ("C1",)


def test_mixed_override_resistor_spec_capacitor(tmp_path, lut_sealed):
    """회로 Z: ss_resistance Rz 는 resistor 상자 규칙(r6). 저항 재정의만 있으면 Rz = 재정의, Cz = spec 상자."""
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path, circuit_z(), lut_sealed, Z_ELEMENTS,
                                             {"Rz": (1e3, 1e5), "Cz": (1e-13, 1e-11)})
    assert ("ss_resistance", "Rz") in dc.schema.components
    assert _bounds(search_domain(dc, _settings(None), pdk, sb)) == {
        ("ss_resistance", "Rz"): _ln(1e3, 1e5), ("capacitance", "Cz"): _ln(1e-13, 1e-11)}
    assert _bounds(search_domain(dc, _settings((1e2, 1e6)), pdk, sb)) == {
        ("ss_resistance", "Rz"): _ln(1e2, 1e6), ("capacitance", "Cz"): _ln(1e-13, 1e-11)}


def test_override_one_kind_still_rejects_other_unboxed_kind(tmp_path, lut_sealed):
    """저항 재정의만 있고 Cz 상자가 없으면 커패시터 쪽은 거부(capacitors = (Cz,))."""
    spec, dc, pdk, rule, sb = _dc_with_boxes(tmp_path, circuit_z(), lut_sealed, Z_ELEMENTS, {"Rz": (1e3, 1e5)})
    with pytest.raises(SchemaRejectedError) as e:
        search_domain(dc, _settings((1e2, 1e6)), pdk, sb)
    det = dict(e.value.record.detail)
    assert det["reason"] == "theta_capacitance_bounds_undeclared" and tuple(det["capacitors"]) == ("Cz",)


def test_spec_box_change_keeps_context_fp(tmp_path, lut_sealed):
    """r10: 상자는 변수 bounds 로만 작용 -- SearchContext 지문(context_fp·schema_fp)은 상자와 무관, spec_fp 는 바뀐다(search_fp)."""
    from gmid_engine.search import build_search_context
    a = _dc_with_boxes(tmp_path / "a", circuit_rr(), lut_sealed, RR_ELEMENTS, {"R1": (1e3, 1e6), "R2": (1e4, 1e7)})
    b = _dc_with_boxes(tmp_path / "b", circuit_rr(), lut_sealed, RR_ELEMENTS, {"R1": (2e3, 1e6), "R2": (1e4, 1e7)})
    sa = build_search_context(a[1], a[0], _settings(None), None, a[2], a[3], code_fp=CODE_FP)
    sb_ = build_search_context(b[1], b[0], _settings(None), None, b[2], b[3], code_fp=CODE_FP)
    assert a[0].spec_fp != b[0].spec_fp
    assert dict(a[0].section_fps)["search_fp"] != dict(b[0].section_fps)["search_fp"]
    assert sa.context_fp == sb_.context_fp and sa.schema_fp == sb_.schema_fp
    assert _bounds(sa.domain)[("resistance", "R1")] != _bounds(sb_.domain)[("resistance", "R1")]


# ---------------------------------------------------------------- [r11, 사용자 결정 11] 면적 예산 -> S-3b 전류 상한 (3.14·3.7)
# oracle (a)·(b): 소자 하나의 W·L ≤ A 이고 L ≥ L_lo 이므로 W ≤ A/L_lo, ID = IDu·W/L ≤ IDu_max·A/L_lo² (IDu = ID·L/w_slice 정의 그대로 --
# 물리 부등식). IDu_max = npz 배열 on_mask 점의 ln(ID·L/w_m) 최대를 exp(conftest `expect_ln_idu_bounds`, 피검 함수 아님),
# L_lo = toy LUT 의 최소 L 앵커(R4_L 직접). I_off 는 예산과 무관(3.19 그대로, conftest `expect_box`).

def _budget_box(kind, A):
    arr = r4_arrays(kind)
    i_off, _ = expect_box(arr, [arr])
    _, hi = expect_ln_idu_bounds(arr)
    return i_off, math.exp(hi) * A / min(R4_L) ** 2


@pytest.mark.parametrize("A", [1e-9, 1e-11])
def test_area_budget_sets_current_upper_bound(tmp_path, lut_sealed, A):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    d = search_domain(case.dc, _settings(), case.pdk, (), A)
    assert d.area_budget_m2 == A
    assert [k for k, _ in d.current_box] == ["nmos", "pmos"]
    for k, box in d.current_box:
        assert tuple(box) == pytest.approx(_budget_box(k, A), rel=1e-12), k
    (cur,) = [v for v in d.variables if v.component[0] == "current"]      # 기저 M2 = pmos 상자
    i_off, i_max = _budget_box("pmos", A)
    assert cur.log is True
    assert (cur.lo, cur.hi) == (pytest.approx(math.log(i_off), rel=1e-12), pytest.approx(math.log(i_max), rel=1e-12))


def test_area_budget_scales_upper_bound_linearly(tmp_path, lut_sealed):
    """I_max ∝ A (같은 IDu_max·L_lo): 예산 두 배 -> I_max 두 배, I_off 불변."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    a = dict(search_domain(case.dc, _settings(), case.pdk, (), 1e-10).current_box)
    b = dict(search_domain(case.dc, _settings(), case.pdk, (), 2e-10).current_box)
    for k in a:
        assert b[k][0] == a[k][0]
        assert b[k][1] == pytest.approx(2 * a[k][1], rel=1e-12)


def test_no_budget_keeps_provisional_box(tmp_path, lut_sealed):
    """예산 없음(None, 기본) -> area_budget_m2 None, current_box 는 종전 단일 finger 슬라이스 값(3.19) -- 예산 인자 없이 부른 것과 같다."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    d0 = search_domain(case.dc, _settings(), case.pdk)
    d1 = search_domain(case.dc, _settings(), case.pdk, (), None)
    assert d0 == d1 and d0.area_budget_m2 is None
    for k, box in d0.current_box:
        arr = r4_arrays(k)
        assert tuple(box) == pytest.approx(expect_box(arr, [arr]), rel=1e-12)


def test_context_budget_from_spec_area_constraint(tmp_path, lut_sealed):
    """build_search_context: area_budget_m2 = spec 판정 제약 area_search_m2 <= v 의 v(같은 (metric, op) 두 개는 spec 로더가
    constraint_duplicate 로 거부하므로 '최솟값' 은 한 개의 값), 정의역은 그 예산으로 만든 것과 같다."""
    cons = (("area_search_m2", "<=", 2e-10, None), ("power_dc_w", "<=", 1e-3, None))
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=cons)
    assert case.sctx.domain.area_budget_m2 == 2e-10
    assert case.sctx.domain == search_domain(case.dc, case.settings, case.pdk, (), 2e-10)
    for k, box in case.sctx.domain.current_box:
        assert tuple(box) == pytest.approx(_budget_box(k, 2e-10), rel=1e-12)


def test_context_without_area_constraint_has_no_budget(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=(("power_dc_w", "<=", 1e-3, None),))
    assert case.sctx.domain.area_budget_m2 is None
    assert case.sctx.domain == search_domain(case.dc, case.settings, case.pdk)
