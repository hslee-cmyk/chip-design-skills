"""CONTRACT 3.9 [r2·r3·r4] `build_search_context` + I-11.

- 정의역 = search_domain(dc, settings, pdk), 제약 분류(목적 축 -> judged_constraints, 레지스트리 view 있는 판정 제약 ->
  ss_constraints + notes verdict unmeasured, view 없는 판정 제약 -> notes metric_not_in_registry_or_no_ss_view),
  counters 7키 0, eval_budget = settings, deadline None, archive None/S3Archive, spec_passive_values.
- I-11: θ 저항이 있고 상자 미선언 -> SchemaRejectedError(theta_resistance_bounds_undeclared), 커널(sizing 평가 블록) 호출 0.
"""
import re

import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.search import S3Archive, SearchSettings, build_search_context, search_domain
from gmid_engine.sizing import dc_columns, dc_currents, dc_widths

from .conftest import SRC, build_case, circuit_c, circuit_p, write_pdk

COUNTERS = ("requests", "kernel_calls", "hits", "fail_hits", "disk_hits", "outside_domain", "recompute_same_key")
CONS = (("power_dc_w", "<=", 1e-3, None), ("gain_ss_db", ">=", 10.0, None), ("supply_current_dc", "<=", 1e-3, None),
        ("area_search_m2", "<=", 1e-9, None))


def _notes(sctx):
    return [dict(n) for n in sctx.constraint_notes]


def test_classification_and_initial_state(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=CONS)
    s = case.sctx
    assert tuple(tuple(x) for x in s.judged_constraints) == (("power_dc_w", "<=", 1e-3), ("area_search_m2", "<=", 1e-9))
    assert [(c.metric, c.op, c.value) for c in s.ss_constraints] == [("gain_ss_db", ">=", 10.0)]
    notes = _notes(s)
    # r4 3.9 덮어쓰기는 ss 제약을 ss_constraints 로만 적는다(r2 의 notes verdict unmeasured 문장은 r4 에서 빠짐 -- 보고한 모호점).
    assert any(n.get("reason") == "metric_not_in_registry_or_no_ss_view" and "supply_current_dc" in repr(n)
               for n in notes)
    assert not any("power_dc_w" in repr(n) or "area_search_m2" in repr(n) for n in notes)
    assert dict(s.counters) == {k: 0 for k in COUNTERS}
    assert s.eval_budget == 40
    assert s.deadline is None
    assert s.archive is None
    # [결정 11] 3.14: CONS 의 판정 제약 area_search_m2 <= 1e-9 가 면적 예산 -> 정의역 = search_domain(..., area_budget_m2=1e-9)
    # (옛 기대 search_domain(dc, settings, pdk) 는 예산 없는 정의역 -- 계약 3.14 r11 로 기대 변경).
    d = search_domain(case.dc, case.settings, case.pdk, (), 1e-9)
    assert s.domain == d and s.domain.area_budget_m2 == 1e-9
    assert re.fullmatch(r"[0-9a-f]{64}", s.code_fp)
    assert tuple(s.spec_passive_values) == ()


def test_spec_passive_values(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(with_cap=True), lut_sealed, elements=(("CL", "capacitor", 2e-12),))
    assert tuple(tuple(x) for x in case.sctx.spec_passive_values) == (("CL", 2e-12),)


def test_fingerprints_deterministic_and_input_sensitive(tmp_path, lut_sealed, lut_pending):
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed).sctx
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed).sctx
    c = build_case(tmp_path / "c", circuit_c(), lut_pending).sctx
    assert (a.context_fp, a.schema_fp, a.code_fp) == (b.context_fp, b.schema_fp, b.code_fp)
    assert c.context_fp != a.context_fp            # LUT 가 context_fp 에 든다
    assert c.schema_fp == a.schema_fp              # 스키마는 LUT 와 무관


def test_archive_created(tmp_path, lut_sealed, short_root):
    case = build_case(tmp_path, circuit_c(), lut_sealed, archive_root=short_root)
    assert isinstance(case.sctx.archive, S3Archive)
    assert dict(case.sctx.disk_failures) == {}


def test_theta_resistance_without_bounds_rejected_before_kernel(tmp_path, lut_sealed):
    """I-11: build_case 가 상자 없이 부르면 거부 -- sizing 평가 블록(커널) 호출 0."""
    before = [b.stats().calls for b in (dc_currents, dc_columns, dc_widths)]
    with pytest.raises(SchemaRejectedError) as e:
        build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=None)
    assert dict(e.value.record.detail)["reason"] == "theta_resistance_bounds_undeclared"
    assert [b.stats().calls for b in (dc_currents, dc_columns, dc_widths)] == before


def test_settings_type_checked(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(TypeError):
        build_search_context(case.dc, case.spec, (600.0, 40, None, SRC), None, case.pdk, case.rule)
    with pytest.raises(TypeError):
        build_search_context(case.dc, case.spec, SearchSettings(600.0, 40, None, SRC), None, None, case.rule)


def test_pdk_missing_quantity(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(SchemaRejectedError) as e:
        build_search_context(case.dc, case.spec, case.settings, None, write_pdk(tmp_path / "p2", with_minw=False), case.rule)
    assert dict(e.value.record.detail)["reason"] == "pdk_quantity_undeclared"


def test_theta_capacitance_without_bounds_rejected_before_kernel(tmp_path, lut_sealed):
    """r6: θ capacitance 가 있고 capacitance_bounds_f 미선언 -> theta_capacitance_bounds_undeclared, 커널 호출 0."""
    from .conftest import Z_ELEMENTS, circuit_z
    before = [b.stats().calls for b in (dc_currents, dc_columns, dc_widths)]
    with pytest.raises(SchemaRejectedError) as e:
        build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=None)
    det = dict(e.value.record.detail)
    assert det["reason"] == "theta_capacitance_bounds_undeclared" and tuple(det["capacitors"]) == ("Cz",)
    assert [b.stats().calls for b in (dc_currents, dc_columns, dc_widths)] == before


def test_junction_built_once_per_context(tmp_path, lut_sealed):
    """r6: build_search_context 가 S0 당 1회 JunctionSource.from_decls(pdk, lut_rule, lut) -- 같은 선언이면 같은 묶음."""
    from gmid_engine.metrics import JunctionSource
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    j = case.sctx.junction
    assert isinstance(j, JunctionSource)
    assert j == JunctionSource.from_decls(case.pdk, case.rule, case.dc.lut.memo.lut)
