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


# ---------------------------------------------------------------- [U5 2026-10-08] 계산 대기 metric 제약
# oracle (d) metrics CONTRACT 3.15 문장: '탐색 문맥(build_search_context)은 판정 제약 중 카탈로그에만 있는 이름을 constraint_notes 에
# unmeasured/metric_computation_pending 으로 남긴다' + (a) 이름은 설계 40 §3.8-8·41 §7.1 어휘, 회로 C 는 손 회로.
# ss_constraints 에 들어가면 측정 못 하는 행이 탐색 판정에 섞인다 -- 그래서 '들어가지 않는다'가 핵심 단정이다.
# [U8 2026-10-09] 잡음 4개는 레지스트리로 옮겨졌다(metrics CONTRACT 10절) -- 계산 대기 자리는 아직 대기인 이름(offset_sys_mv·icmr_v, 40 §3.8-8 표)으로 바꾼다.
# 잡음 제약 분류는 아래 U8 절 test 가 본다.
PENDING_CONS = (("offset_excess", "<=", 2 ** 0.5, None), ("offset_sys_mv", "<=", 2.0, None),
                ("swing_out_v", ">=", 0.5, None), ("icmr_v", ">=", 0.3, None))


def test_pending_metric_constraints_noted_not_searched(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=PENDING_CONS + (("gain_ss_db", ">=", 10.0, None),))
    s = case.sctx
    assert [c.metric for c in s.ss_constraints] == ["gain_ss_db"]
    assert not {m for m, *_ in PENDING_CONS} & {x[0] for x in s.judged_constraints}
    notes = _notes(s)
    for metric, *_ in PENDING_CONS:
        mine = [n for n in notes if metric in repr(n)]
        assert len(mine) == 1, (metric, notes)
        assert mine[0].get("verdict") == "unmeasured"
        assert mine[0].get("reason") == "metric_computation_pending"


def test_pending_metric_notes_do_not_touch_registry_rows(tmp_path, lut_sealed):
    """계산 대기 제약을 더해도 레지스트리 제약 분류(ss_constraints·judged_constraints)는 그대로다."""
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed, constraints=CONS).sctx
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed, constraints=CONS + PENDING_CONS).sctx
    assert [(c.metric, c.op, c.value) for c in a.ss_constraints] == [(c.metric, c.op, c.value) for c in b.ss_constraints]
    assert tuple(tuple(x) for x in a.judged_constraints) == tuple(tuple(x) for x in b.judged_constraints)
    extra = [n for n in _notes(b) if n not in _notes(a)]
    assert len(extra) == len(PENDING_CONS)
    assert all(n.get("reason") == "metric_computation_pending" for n in extra)



def test_ff_gm_ratio_constraint_noted_computation_pending(tmp_path, lut_sealed):
    """[U5 후속 2026-10-09] ff_gm_ratio(40 §3.8-8, 값 계산은 §11 J 추가 범위 U7) 는 카탈로그에만 있는 계산 대기 이름 --
    oracle (d) SPEC_CONTRACT 6절 끝 '탐색 문맥이 constraint_notes 에 unmeasured/metric_computation_pending 으로 남긴다'.
    ss_constraints·judged_constraints 에 들지 않는다(측정 못 하는 행이 탐색 판정에 섞이지 않음)."""
    cons = (("ff_gm_ratio", ">=", 1.0, None), ("gain_ss_db", ">=", 10.0, None))
    s = build_case(tmp_path, circuit_c(), lut_sealed, constraints=cons).sctx
    assert [c.metric for c in s.ss_constraints] == ["gain_ss_db"]
    assert "ff_gm_ratio" not in {x[0] for x in s.judged_constraints}
    mine = [n for n in _notes(s) if "ff_gm_ratio" in repr(n)]
    assert len(mine) == 1, _notes(s)
    assert mine[0].get("verdict") == "unmeasured"
    assert mine[0].get("reason") == "metric_computation_pending"


# ---------------------------------------------------------------- [U8 2026-10-09] 잡음 제약 -- 시작 때 잡음 LUT 필수 검사
# oracle (d) search CONTRACT 11절·설계 41 §7.2 '잡음 데이터가 없는데 잡음 제약이 선언되면 SchemaRejectedError(noise_lut_missing)',
# lut CONTRACT 9.5(detail kinds = 없는 kind 정렬 tuple). lut_sealed 는 잡음 r1 없이 만든 toy LUT 다(구성).

@pytest.mark.parametrize("metric, op, value", [("noise_excess_th", "<=", 2.0), ("noise_th_in_v2hz", "<=", 1e-15),
                                               ("noise_fc_in_hz", "<=", 1e5), ("noise_out_int_vrms", "<=", 3e-4)])
def test_noise_constraint_without_noise_lut_rejected(tmp_path, lut_sealed, metric, op, value):
    with pytest.raises(SchemaRejectedError) as ei:
        build_case(tmp_path, circuit_c(), lut_sealed, constraints=((metric, op, value, None), ("gain_ss_db", ">=", 10.0, None)))
    d = dict(ei.value.record.detail)
    assert d["reason"] == "noise_lut_missing"
    assert tuple(d["kinds"]) == ("nmos", "pmos")              # 회로 C 의 MOS kind 둘 다 잡음 표가 없다


def test_no_noise_constraint_no_noise_lut_needed(tmp_path, lut_sealed):
    """잡음 제약이 없으면 잡음 LUT 없이도 시작한다(거부는 값 있는 잡음 제약이 있을 때만)."""
    s = build_case(tmp_path, circuit_c(), lut_sealed, constraints=(("gain_ss_db", ">=", 10.0, None),)).sctx
    assert [c.metric for c in s.ss_constraints] == ["gain_ss_db"]


def test_noise_decl_without_s1v(tmp_path, lut_sealed):
    """search 11절: SearchContext.noise_decl = noise_decl(spec, s1v) -- 6인자 호출(s1v 없음)이면 입력 셀 없음, spec feedback 빈 list -> (),
    noise_testbench 없음 -> 샘플링 커패시터 (). oracle (d)."""
    from gmid_engine.metrics import NoiseDecl
    s = build_case(tmp_path, circuit_c(), lut_sealed).sctx
    assert s.noise_decl == NoiseDecl(feedback=(), sampling_caps=(), input_cells=())
