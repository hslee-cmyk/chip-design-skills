"""CONTRACT 3.9 [r2·r3·r4] `build_search_context` + I-11.

- 정의역 = domain_of(dc, settings, pdk), 제약 분류(목적 축 -> judged_constraints, 레지스트리 view 있는 판정 제약 ->
  ss_constraints + notes verdict unmeasured, view 없는 판정 제약 -> notes metric_not_in_registry_or_no_ss_view),
  counters 6키 0([xrun] interface card C1), eval_budget = settings, deadline None, archive None/S3Archive, spec_passive_values.
- I-11: θ 저항이 있고 상자 미선언 -> SchemaRejectedError(theta_resistance_bounds_undeclared), 커널(sizing 평가 블록) 호출 0.
"""
import ast
import re
from pathlib import Path

import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.search import S3Archive, SearchSettings, build_search_context, search_domain
from gmid_engine.sizing import dc_solve, dc_currents, dc_solve

from .conftest import domain_of  # [U17 ①-b] graph/kernel: search_domain 필드 읽기
from .conftest import CODE_FP, SRC, build_case, circuit_c, circuit_p, write_pdk
from .conftest import block_row, fresh_run  # [XRUN-F1 card B C0·C1]

# [xrun] interface card C1: SearchContext.counters 키 집합 = 이 6개(디스크 실패 적중 계수 삭제 -- 설계 40 v1.10 §2.4.3 '디스크 실패 기록 읽기')
COUNTERS = ("requests", "kernel_calls", "hits", "fail_hits", "outside_domain", "recompute_same_key")
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
    d = domain_of(case.dc, case.settings, case.pdk, (), 1e-9)
    assert s.domain == d and s.domain.area_budget_m2 == 1e-9
    assert re.fullmatch(r"[0-9a-f]{64}", s.code_fp)
    assert not hasattr(s, "spec_passive_values")        # [U17 ①] 설계 40 §2.4.7 SearchContext 칸 배정: 수동소자 값 사본 칸 없음


def test_spec_passive_value_is_s2_field(tmp_path, lut_sealed):
    """[U17 ①] 설계 40 v1.6 §2.4.7 'SearchContext 칸 배정' 표: `element_values`·`spec_passive_values` -> 수동소자 값 필드(S2).
    spec 선언 값 CL = 2e-12 는 SearchContext 의 칸이 아니라 평가 스냅샷의 `device.passive_value` 행이다(§2.4.8, 값 = spec 선언 그대로)."""
    from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
    from .conftest import CELLS_C, theta_r4c
    case = build_case(tmp_path, circuit_c(with_cap=True), lut_sealed, elements=(("CL", "capacitor", 2e-12),))
    assert not hasattr(case.sctx, "spec_passive_values")
    r = evaluate(case.sctx, tuple(sorted(theta_r4c().items())), CELLS_C)
    assert r.evaluation is not None
    assert dict(r.evaluation.snapshot.column("device", "passive_value")) == {"CL": 2e-12}


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
    # [xrun] 옛 단언 '디스크 실패 표가 비어 있다'는 지웠다 -- 그 칸이 없어졌다(설계 40 v1.10 §2.4.3 '디스크 실패 기록 읽기' 삭제).
    # S3Archive 공개 메서드(interface card C6): 쓰기 셋과 폴더 .dir 만, 읽기 API 는 없다.
    methods = {n for n in dir(S3Archive) if not n.startswith("_") and callable(getattr(S3Archive, n))}
    assert methods == {"append_eval", "append_run", "write_snapshot"}
    assert Path(case.sctx.archive.dir) == Path(short_root) / case.sctx.context_fp


def test_counters_key_set_exact(tmp_path, lut_sealed):
    """[xrun XR-7] interface card C1: SearchContext.counters 키 집합 = {requests, kernel_calls, hits, fail_hits, outside_domain,
    recompute_same_key} 정확히(양성 형식)."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    assert set(dict(case.sctx.counters)) == set(COUNTERS)
    assert len(COUNTERS) == 6


def test_s0_keyword_rejected(tmp_path, lut_sealed):
    """[xrun XR-7] interface card C1: build_search_context 는 s0 키워드를 받지 않는다(모르는 키워드 TypeError) -- S0 저장 폐지
    (설계 40 v1.10 §2.4.3 'S0 저장' 삭제). 대조군: 같은 인자에서 s0 만 빼면 만들어진다(TypeError 가 다른 인자 때문이 아님)."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(TypeError):
        build_search_context(case.dc, case.spec, case.settings, None, case.pdk, case.rule, code_fp=CODE_FP, s0=None)
    s = build_search_context(case.dc, case.spec, case.settings, None, case.pdk, case.rule, code_fp=CODE_FP)
    assert s.code_fp == CODE_FP


def test_theta_resistance_without_bounds_rejected_before_kernel(tmp_path, lut_sealed):
    """I-11: build_case 가 상자 없이 부르면 거부 -- sizing 평가 블록(커널) 호출 0([XRUN-F1 card B C1] 그 실행 계수에 평가 블록 행이 없다)."""
    run = fresh_run()
    # [FS-1 A-188·A-190 M-2b] 정본 경로(build_case = 단계 A -> 단계 B)에서는 같은 사유(탐색 정의역 게이트 theta_resistance_bounds_undeclared)를 단계 B 가 먼저 낸다:
    # build_case 가 '단계 B 불통과' 로 멈추고 그 정지 사유에 같은 사유가 들어 있다. 커널 컨텍스트는 만들어지지 않는다(커널 호출 0).
    with pytest.raises(AssertionError) as e:
        build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=None, run=run)
    assert "단계 B 불통과" in str(e.value) and "theta_resistance_bounds_undeclared" in str(e.value)
    assert [block_row(run["counters"], b.name)[0] for b in (dc_currents, dc_solve, dc_solve)] == [0, 0, 0]


def test_settings_type_checked(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(TypeError):
        build_search_context(case.dc, case.spec, (600.0, 40, None, SRC), None, case.pdk, case.rule, code_fp=CODE_FP)
    with pytest.raises(TypeError):
        build_search_context(case.dc, case.spec, SearchSettings(600.0, 40, None, SRC), None, None, case.rule, code_fp=CODE_FP)


def test_code_fp_is_required_keyword(tmp_path, lut_sealed):
    # [U17 ①-a] 설계 40 §2.4.3 (iii): 코드 지문은 단계 A 가 실행마다 한 번 잰 엔진 코드 지문(StageAResult.code_fp)을 받는다 --
    # 없거나 빈 값이면 거부(옛 6개 패키지 자체 계산 경로 없음).
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(TypeError):
        build_search_context(case.dc, case.spec, case.settings, None, case.pdk, case.rule)
    for bad in (None, "", 7):
        with pytest.raises(TypeError):
            build_search_context(case.dc, case.spec, case.settings, None, case.pdk, case.rule, code_fp=bad)


def test_code_fp_is_the_given_value(tmp_path, lut_sealed):
    # 넘긴 값을 그대로 쓴다(다시 재지 않는다) -- S3 기록의 code_fp 가 단계 A·S0 스냅샷 키의 엔진 코드 지문과 같은 값.
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    given = "ab" * 32
    s = build_search_context(case.dc, case.spec, case.settings, None, case.pdk, case.rule, code_fp=given)
    assert s.code_fp == given


def test_search_context_dc_carries_run_pair(tmp_path, lut_sealed):
    """B-T16(XRUN-F1 card B C6): build_search_context 는 서명 그대로이고 dc_ctx 의 두 칸을 쓴다 -- sctx.dc 의 donors·counters 는 그 커널
    컨텍스트에 넘긴 두 객체 그대로(is)."""
    run = fresh_run()
    case = build_case(tmp_path, circuit_c(), lut_sealed, run=run)
    assert case.dc.donors is run["donors"] and case.dc.counters is run["counters"]
    assert case.sctx.dc.donors is run["donors"] and case.sctx.dc.counters is run["counters"]


def test_pdk_missing_quantity(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    with pytest.raises(SchemaRejectedError) as e:
        build_search_context(case.dc, case.spec, case.settings, None, write_pdk(tmp_path / "p2", with_minw=False), case.rule,
                             code_fp=CODE_FP)
    assert dict(e.value.record.detail)["reason"] == "pdk_quantity_undeclared"


def test_theta_capacitance_without_bounds_rejected_before_kernel(tmp_path, lut_sealed):
    """r6: θ capacitance 가 있고 capacitance_bounds_f 미선언 -> theta_capacitance_bounds_undeclared, 커널 호출 0."""
    from .conftest import Z_ELEMENTS, circuit_z
    run = fresh_run()
    with pytest.raises(AssertionError) as e:      # [FS-1 A-190 M-2b] 단계 B 가 같은 사유로 먼저 거부 (위 test 와 같은 설명)
        build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=None, run=run)
    assert "단계 B 불통과" in str(e.value) and "theta_capacitance_bounds_undeclared" in str(e.value) and "Cz" in str(e.value)
    assert [block_row(run["counters"], b.name)[0] for b in (dc_currents, dc_solve, dc_solve)] == [0, 0, 0]


def test_junction_built_once_per_context(tmp_path, lut_sealed):
    """r6 [JC-1]: build_search_context 가 S0 당 1회 JunctionSource.from_decls(lut_rule, lut) -- 같은 선언이면 같은 묶음."""
    from gmid_engine.metrics import JunctionSource
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    j = case.sctx.junction
    assert isinstance(j, JunctionSource)
    assert j == JunctionSource.from_decls(case.rule, case.dc.lut.memo.lut)


# ---------------------------------------------------------------- [U7+U8 통합 2026-10-09] 계산 대기 표가 빈 표인 문맥
# 옛 [U5] 두 test(`test_pending_metric_constraints_noted_not_searched`·`test_pending_metric_notes_do_not_touch_registry_rows`)는 계산 대기
# 이름(PENDING_CONS)이 빈 tuple 이 되어 반복할 대상이 없는 헐거운 test 였다 -- 삭제하고 아래 test 로 대체한다.
# 현재 계약: metrics CONTRACT 10.0·11절(`PENDING_METRIC_ROWS` 빈 tuple, 카탈로그 = 레지스트리), search CONTRACT 3.9 분류
# (목적 축 -> judged_constraints, view 있는 판정 제약 -> ss_constraints, 나머지 -> notes metric_not_in_registry_or_no_ss_view).
# 그래서 카탈로그의 어떤 이름으로 제약을 걸어도 metric_computation_pending 노트가 생기지 않고, 각 제약은 세 곳 중 정확히 한 곳에 간다.
# oracle (d) 계약 문장. 잡음 4개는 잡음 LUT 없는 toy LUT 에서 noise_lut_missing 거부(U8 절 test)라 이 sweep 에서 뺀다 -- 구성(a).
# view_kind cm_loop(회로 C 는 차동 출력이 없어 기본 뷰 없음)·ratio({num, den} 명시 필수)는 로더가 view_required 로 거부하므로
# 뷰 없는 이 sweep 에서 뺀다(SPEC_CONTRACT 2절, authoring test 가 본다) -- 구성(a).
# 값 1.0 은 합성 입력(a), 사용자 값 아님. 미지 이름 거부(metric_unknown, 로더)는 authoring/test_spec_constraints.py 가 본다.
NOISE_NAMES = ("noise_th_in_v2hz", "noise_fc_in_hz", "noise_excess_th", "noise_out_int_vrms")
# [U13 후속 2026-10-09] offset 2개(offset_in_sigma_mv·offset_excess)는 mismatch r1 없는 toy LUT 에서 mismatch_lut_missing 거부(search CONTRACT 11절,
# 아래 U13 후속 절 test)라 잡음과 같은 이유로 이 sweep 에서 뺀다 -- 구성(a). 두 metric 의 분류(ss_constraints)는 mismatch r1 을 실은 실경로 test 가 본다.
OFFSET_NAMES = ("offset_in_sigma_mv", "offset_excess")
VIEW_REQUIRED_KINDS = ("cm_loop", "ratio")


def test_every_catalog_constraint_classified_once_never_pending(tmp_path, lut_sealed):
    from gmid_engine.metrics import metric_catalog
    cat = metric_catalog()
    assert set(OFFSET_NAMES) <= set(cat)                     # 입력 확인: 빼는 이름이 카탈로그에 있다
    names = sorted(n for n in cat if n not in NOISE_NAMES + OFFSET_NAMES and cat[n].view_kind not in VIEW_REQUIRED_KINDS)
    assert len(names) == 23 - len(NOISE_NAMES) - len(OFFSET_NAMES) - 2          # pm_cm_ss_deg(cm_loop)·ratio_ss_db(ratio)
    cons = tuple((n, "<=", 1.0, None) for n in names)
    s = build_case(tmp_path, circuit_c(), lut_sealed, constraints=cons).sctx
    notes = _notes(s)
    assert not any(n.get("reason") == "metric_computation_pending" for n in notes)
    ss = [c.metric for c in s.ss_constraints]
    judged = [x[0] for x in s.judged_constraints]
    for n in names:
        noted = [x for x in notes if x.get("reason") == "metric_not_in_registry_or_no_ss_view" and repr(n) in repr(x)]
        assert ss.count(n) + judged.count(n) + len(noted) == 1, (n, ss, judged, notes)


# ---------------------------------------------------------------- [U7 2026-10-09] 계산이 들어온 offset·스윙·FF 비 제약
# oracle (d) metrics CONTRACT 10.7: '`ctx.ss_constraints` 에 `AUX_TYPES` metric(뷰 없는 swing·mirror 포함)이 들어가 `ss_constraint_rows` 가
# 판정한다'. 설계 40 §3.8-8 판정 위치 '다른 metric 과 같이 외층 전회로 계산 한 곳(DEC-74)' -- 계산 대기 노트(metric_computation_pending)로
# 남으면 판정이 조용히 빠진다. 옛 기대(계산 대기 노트)는 U7 이 계산을 넣어 대체된 동작이다.
# [U13 후속 2026-10-09] offset_excess 는 mismatch r1 없는 toy LUT(lut_sealed)에서 시작 거부(mismatch_lut_missing)라 여기서 뺐다 -- 같은 단언
# (ss_constraints 에 들고 판정 축·노트에 없다)은 mismatch r1 을 실은 실경로 test_offset_constraints_with_mismatch_lut_enter_ss_constraints 가 본다.
AUX_CONS = (("swing_out_v", ">=", 0.5, None), ("mirror_ratio_sigma_pct", "<=", 1.0, None), ("ff_gm_ratio", ">=", 1.0, None))


def test_aux_metric_constraints_enter_ss_constraints(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=AUX_CONS + (("gain_ss_db", ">=", 10.0, None),))
    s = case.sctx
    assert sorted(c.metric for c in s.ss_constraints) == sorted([m for m, *_ in AUX_CONS] + ["gain_ss_db"])
    assert not {m for m, *_ in AUX_CONS} & {x[0] for x in s.judged_constraints}
    assert not any(n.get("reason") == "metric_computation_pending" for n in _notes(s))
    assert not any(n.get("reason") == "metric_not_in_registry_or_no_ss_view" and any(m in repr(n) for m, *_ in AUX_CONS)
                   for n in _notes(s))


def test_ff_gm_ratio_constraint_judged_not_pending(tmp_path, lut_sealed):
    """[U7] ff_gm_ratio(40 §3.8-8, 계산 = §11 J 추가 범위 U7 행) 는 이제 레지스트리 metric -- ss_constraints 에 들고 노트가 없다."""
    cons = (("ff_gm_ratio", ">=", 1.0, None), ("gain_ss_db", ">=", 10.0, None))
    s = build_case(tmp_path, circuit_c(), lut_sealed, constraints=cons).sctx
    assert [c.metric for c in s.ss_constraints] == ["ff_gm_ratio", "gain_ss_db"]
    assert "ff_gm_ratio" not in {x[0] for x in s.judged_constraints}
    assert [n for n in _notes(s) if "ff_gm_ratio" in repr(n)] == []



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


# [FS-1 A-190 M-2d 삭제] test_noise_decl_without_s1v·test_u7_context_inputs_default -- 'S1v 없는 S1 수준 컨텍스트' 전제의 legacy (정본 경로 build_case 는 단계 A·B 를 거쳐
# S1v 필드가 항상 있다: 실측 input_cells=(('M1',),), structure 있음). tests/RETIRED_TESTS_fs1.md.


# ---------------------------------------------------------------- [U13 후속 2026-10-09] offset 제약 -- 시작 때 mismatch LUT 필수 검사(fail-closed)
# oracle (d) search CONTRACT 11절 '값이 있는 offset_in_sigma_mv 또는 offset_excess 판정 제약이 있고 MOS kind 의 mismatch 감도 r1 데이터
# (LutSet.mismatch)가 없으면 SchemaRejectedError(mismatch_lut_missing)', lut CONTRACT 9.5(detail kinds = 없는 kind 정렬 tuple).
# lut_sealed 는 mismatch r1 없이 만든 toy LUT 다(구성 (a)). 제약 값 3.3·sqrt(2) 는 합성 입력(사용자 값 아님, 판정 기대 아님).

@pytest.mark.parametrize("metric, op, value", [("offset_in_sigma_mv", "<=", 3.3), ("offset_excess", "<=", 2 ** 0.5)])
def test_offset_constraint_without_mismatch_lut_rejected(tmp_path, lut_sealed, metric, op, value):
    with pytest.raises(SchemaRejectedError) as ei:
        build_case(tmp_path, circuit_c(), lut_sealed, constraints=((metric, op, value, None), ("gain_ss_db", ">=", 10.0, None)))
    d = dict(ei.value.record.detail)
    assert d["reason"] == "mismatch_lut_missing"
    assert tuple(d["kinds"]) == ("nmos", "pmos")              # 회로 C 의 MOS kind 둘 다 mismatch 표가 없다


def test_offset_sys_constraint_needs_no_mismatch_lut(tmp_path, lut_sealed):
    """oracle (d) search CONTRACT 11절: 검사 대상은 offset_in_sigma_mv·offset_excess 둘뿐 -- 계통 offset(offset_sys_mv)은 mismatch 감도와 무관해
    mismatch r1 없이도 시작한다(거부 범위가 넓어지지 않는다)."""
    s = build_case(tmp_path, circuit_c(), lut_sealed, constraints=(("offset_sys_mv", "<=", 1.0, None),
                                                                   ("gain_ss_db", ">=", 10.0, None))).sctx
    noted = [x for x in _notes(s) if x.get("reason") == "metric_not_in_registry_or_no_ss_view" and "offset_sys_mv" in repr(x)]
    ss = [c.metric for c in s.ss_constraints]
    judged = [x[0] for x in s.judged_constraints]
    assert ss.count("offset_sys_mv") + judged.count("offset_sys_mv") + len(noted) == 1     # 위 sweep 과 같은 '정확히 한 곳'


def test_offset_constraints_with_mismatch_lut_enter_ss_constraints():
    """mismatch r1 을 실은 실 LUT(u13_real: lut CONTRACT 1.8 정본 호출 `mismatch_npz=loc.mismatch_path`)면 같은 두 제약으로 거부되지 않고 시작하며,
    두 metric 은 ss_constraints 에 정확히 한 번씩 들고 판정 축·계산 대기/뷰 없음 노트에 없다(위 U7 절 oracle (d) metrics CONTRACT 10.7 과 같은 단언).
    입력: library two_stage_ota(spec 이 offset_excess <= sqrt(2) 를 선언) + 추가 offset_in_sigma_mv <= 3.3(test_iv_matching_l 과 같은 test 입력)."""
    from .u13_real import real_case, real_env
    assert real_env().lut.mismatch                              # 전제: mismatch r1 이 실렸다
    s = real_case("two_stage_ota", (("offset_in_sigma_mv", "<=", 3.3),)).sctx
    ss = [c.metric for c in s.ss_constraints]
    judged = {x[0] for x in s.judged_constraints}
    for m in OFFSET_NAMES:
        assert ss.count(m) == 1, (m, ss)
        assert m not in judged
    assert not any(n.get("reason") in ("metric_computation_pending", "metric_not_in_registry_or_no_ss_view")
                   and any(m in repr(n) for m in OFFSET_NAMES) for n in _notes(s))


# [U17 ①-b] 설계 40 v1.9 §2.4.7 'SearchContext 칸 배정' 표 중 S0 수준 필드로 가는 칸(§2.4.8 graph/kernel·graph/s1v·graph/ach·graph/start 행):
# `domain` -> graph/kernel search_domain, `judged_constraints`·`ss_constraints`·`constraint_notes` -> graph/kernel constraint_classes,
# `junction`·`mismatch` -> junction_source·mismatch_source, `area_decl` -> passive_area_decl, `model_error` -> model_error,
# `structure` -> graph/s1v metric_structure, `noise_decl` -> graph/s1v noise_input_cells, `s1v`·`ach`·`start` -> graph/s1v·ach·start 필드.
# SearchContext 는 이 값을 칸으로 들지 않는다(나머지 칸 정리 -- 참조·S3 색인·실행 계수만 -- 는 단계 ② G-7).
S0_SLOTS_REMOVED = ("domain", "judged_constraints", "ss_constraints", "constraint_notes", "junction", "mismatch", "area_decl",
                    "model_error", "structure", "noise_decl", "s1v", "ach", "start")


def _stored_attrs(tree):
    """모듈 안에서 속성으로 **대입**되는 이름(`x.a = ...`, `x.a += ...`), 클래스 본문의 주석·대입 이름, `__slots__` 문자열."""
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Store):
            out.add(n.attr)
        elif isinstance(n, ast.ClassDef):
            for st in n.body:
                if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
                    out.add(st.target.id)
                elif isinstance(st, ast.Assign):
                    for t in st.targets:
                        if isinstance(t, ast.Name) and t.id == "__slots__":
                            out.update(c.value for c in ast.walk(st.value) if isinstance(c, ast.Constant) and isinstance(c.value, str))
                        elif isinstance(t, ast.Name):
                            out.add(t.id)
    return out


def test_search_context_has_no_s0_value_slots():
    import gmid_engine.search as search_pkg
    path = Path(search_pkg.__file__).resolve().parent / "search_context.py"      # 파일 = design §2.4.7 표의 E/search/search_context.py
    stored = _stored_attrs(ast.parse(path.read_text(encoding="utf-8")))
    assert not stored & set(S0_SLOTS_REMOVED), sorted(stored & set(S0_SLOTS_REMOVED))


def test_stored_attrs_scanner():
    src = ("class C:\n    __slots__ = ('a', 'b')\n    c: int\n    d = 1\n    def f(self):\n        self.e = 0\n        self.g.h = 1\n"
           "ctx.i = 2\nctx.j += 1\nx = ctx.k\n")
    assert _stored_attrs(ast.parse(src)) == {"a", "b", "c", "d", "e", "h", "i", "j"}


# =====================================================================================================================
# [XRUN-F1 card A] 첫 평가 버림 제거 -- interface card xrunf1a C3(계수 상태 memo)·C4(build_search_context 안 커널 평가 0, 탐색 memo =
# LutMemo.counting(호출자 lut, n_θ, table_cache=호출자 memo 의 table_cache))·C5(evaluate 의 첫 커널 평가가 창). 옛 test_sweep_memo_wiring.py 의
# 성질(탐색 memo ≠ 호출자 memo, 상한 = (n_θ + 1)·U, 값 비트 동일, 호출자 상한 상수 무영향)을 여기로 옮겼다(원본 없는 test 파일 삭제, 규칙 H).
# 관찰 지점(J-3): 모듈 속성 `gmid_engine.search.kernel.size_and_seal`(커널 평가 1회 = 호출 1회), 클래스 속성 `LutMemo.lookup`(모든 조회가 거친다).
# oracle:
# - (독립) 커널 호출 수·창 안 서로 다른 키 수 U_r 는 이 파일이 감싼 함수로 따로 센다(엔진 계수·stats 의 hits/misses 를 쓰지 않는다).
#   '서로 다름'의 동치 = C3 문장(0.0 과 −0.0 은 다른 키, NaN 은 같은 내용이면 같은 키, 1·1.0·True 는 서로 다른 키)을 이 파일의 `_canon` 이 따로 구현.
# - (식) 상한 = (n_θ + 1)·U_r, n_θ = len(centre_start(sctx)[0])(C4 정의 -- 첫 점의 변수 수를 읽을 뿐 상한 계산은 쓰지 않는다).
# - (비교) 같은 입력 두 실행의 front·평가 결과 비트 비교(memo 는 값을 바꾸지 않는다, C3 '값').
# 엔진 소스는 열람하지 않았다(interface card 만).
# =====================================================================================================================

import dataclasses
import importlib
import math

from gmid_engine.lut import LutMemo
from gmid_engine.search import cone_rows, find_front
from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
from gmid_engine.search.layer0_center import centre_start

from .conftest import front_signature, schema_of, theta_r4c

SWEEP = ("point", "curve", "root")
_KERNEL = importlib.import_module("gmid_engine.search.kernel")


def _canon(v):
    """C3 키 동치의 독립 구현: 형 태그 + 값(float 은 hex, NaN 은 하나로). tuple·frozenset 은 재귀."""
    if isinstance(v, bool):
        return ("bool", v)
    if isinstance(v, int):
        return ("int", v)
    if isinstance(v, float):
        return ("float", "nan" if math.isnan(v) else v.hex())
    if isinstance(v, (str, bytes)):
        return (type(v).__name__, v)
    if isinstance(v, tuple):
        return ("tuple", tuple(_canon(x) for x in v))
    if isinstance(v, frozenset):
        return ("frozenset", tuple(sorted(repr(_canon(x)) for x in v)))
    if v is None:
        return ("none",)
    return ("obj", type(v).__module__, type(v).__qualname__, repr(v))


def _caps(memo):
    return {r: s.capacity for r, s in memo.stats() if r in SWEEP}


def _count_kernel(monkeypatch):
    calls = []
    real = _KERNEL.size_and_seal

    def counted(*a, **k):
        calls.append(1)
        return real(*a, **k)
    monkeypatch.setattr(_KERNEL, "size_and_seal", counted)
    return calls


def _centre_in_cone(sctx):
    """전제: 상자 중심(centre_start 의 θ)이 원뿔 안 -- as-built 가 컨텍스트 생성 안에서 이 점을 커널로 평가했을 조건."""
    _v, theta, _cells, _u = centre_start(sctx)
    return all(row.c > 0 for row in cone_rows(schema_of(sctx.dc), tuple(sorted(dict(theta).items()))))


def test_build_search_context_runs_no_kernel(tmp_path, lut_sealed, monkeypatch):
    """A-T9: build_search_context 동안 kernel.size_and_seal 호출 0(임시 컨텍스트·버리는 평가 없음). 반환 뒤 kernel_calls 0·seq 0·cache 빔."""
    calls = _count_kernel(monkeypatch)
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    n_build = len(calls)
    s = case.sctx
    assert _centre_in_cone(s)                                       # 전제(공허 방지)
    assert n_build == 0, n_build
    assert dict(s.counters)["kernel_calls"] == 0 and s.seq == 0 and len(s.cache) == 0
    # 감싼 계수가 실제로 센다(대조군): 첫 커널 평가 한 번 -> 1
    _v, theta, cells, _u = centre_start(s)
    evaluate(s, theta, cells)
    assert len(calls) == 1 and dict(s.counters)["kernel_calls"] == 1


def _lookups_during(monkeypatch, memo, fn):
    """fn() 이 도는 동안 memo(그 객체)의 영역 point·curve·root 조회 중 정상 반환한 것을 (영역, _canon((lut.fp, fn_name) + tuple(key)))로
    기록한다(LutMemo.lookup 클래스 수준 감쌈, 원래 것을 부름). compute 예외로 끝난 조회는 기록하지 않는다(C3)."""
    seen = []
    real = LutMemo.lookup

    def wrapped(self, region, fn_name, key, compute):
        out = real(self, region, fn_name, key, compute)
        if self is memo and region in SWEEP:
            seen.append((region, _canon((self.lut.fp, fn_name) + tuple(key))))
        return out
    monkeypatch.setattr(LutMemo, "lookup", wrapped)
    try:
        fn()
    finally:
        monkeypatch.setattr(LutMemo, "lookup", real)
    return seen


def test_first_kernel_eval_fixes_capacity_from_independent_count(tmp_path, lut_sealed, monkeypatch):
    """A-T10: build 뒤 첫 커널 평가(상자 중심 θ·cells) 한 번의 호출 구간에서 탐색 memo 조회를 따로 세어 U_r -> stats capacity = (n_θ + 1)·U_r
    (영역 point·curve·root). n_θ = len(centre_start(sctx)[0])."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    s = case.sctx
    memo = s.dc.lut.memo
    variables, theta, cells, _u = centre_start(s)                   # 창 밖(첫 커널 평가 전) -- 이 조회는 U 에 세지 않는다
    n_theta = len(variables)
    assert dict(s.counters)["kernel_calls"] == 0                    # 전제: 아직 커널 평가 없음 -> 다음 evaluate 가 첫 커널 평가
    seen = _lookups_during(monkeypatch, memo, lambda: evaluate(s, theta, cells))
    assert dict(s.counters)["kernel_calls"] == 1                    # 전제: 정말 커널 평가였다(원뿔 밖·캐시 적중 아님)
    assert seen                                                     # 공허 방지: 창 안 조회가 있다
    u = {r: len({k for rr, k in seen if rr == r}) for r in SWEEP}
    assert _caps(s.dc.lut.memo) == {r: (n_theta + 1) * u[r] for r in SWEEP}   # (식)


def test_search_memo_rejects_second_window_after_first_kernel_eval(tmp_path, lut_sealed):
    """A-T11: 첫 커널 평가 뒤 탐색 memo 는 고정(bound_state "fixed") -- open_count()·fix_bound() 각각 ValueError(C3 한 방향 전이)."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    s = case.sctx
    _v, theta, cells, _u = centre_start(s)
    evaluate(s, theta, cells)
    assert dict(s.counters)["kernel_calls"] == 1
    memo = s.dc.lut.memo
    assert memo.bound_state == "fixed"
    with pytest.raises(ValueError):
        memo.open_count()
    with pytest.raises(ValueError):
        memo.fix_bound()
    assert memo.bound_state == "fixed"


def _eval_table(sctx):
    """sctx.cache 의 평가 결과 -> {키 repr: 비트 비교용 repr}. float repr 은 왕복 정확(비트 동일 ⇔ repr 동일)."""
    out = {}
    for k, r in sctx.cache.items():
        fail = None if r.failure is None else repr(r.failure)
        out[repr(k)] = repr((r.theta, r.status, r.objectives, r.constraints, r.cone, r.unmeasured, r.warnings, r.seq, fail))
    return out


def _build_with_caller_cap(tmp, lut, cap, **kw):
    """search conftest `build_case` 와 같은 입력, 호출자 memo 상한만 `cap`(영역 셋 모두)."""
    from gmid_engine.graph import build_s1
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec, LutAccess
    from .conftest import load_spec, write_decls
    tmp = Path(tmp)
    acc = LutAccess(LutMemo(lut, point=cap, curve=cap, root=cap))
    td, spec = load_spec(tmp / "case", circuit_c())
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()                      # [XRUN-F1 card B C0·C6] 이 build 하나 = 실행 하나
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, acc, **run)
    pdk, rule = write_decls(tmp / "pdk")
    settings = SearchSettings(600.0, kw.get("eval_budget", 30), None, tuple(SRC), None)
    return acc, build_search_context(dc, spec, settings, None, pdk, rule, code_fp=CODE_FP)


def test_search_memo_is_not_callers_and_caller_untouched(tmp_path, lut_sealed):
    """A-T12 (옮겨 온 성질 1): 탐색 memo ≠ 호출자 memo, 호출자가 넘긴 커널 컨텍스트의 memo 는 그대로."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    assert case.sctx.dc.lut.memo is not case.acc.memo
    assert case.dc.lut.memo is case.acc.memo


def test_eval_results_identical_search_memo_vs_caller_memo(tmp_path, lut_sealed):
    """A-T12 (옮겨 온 성질 2): 같은 입력의 탐색을 (A) 탐색 memo(배선 그대로), (B) 호출자 memo(상한 4096 생성자 memo)로 돌린다 ->
    front·모든 평가 결과·run_id 비트 동일."""
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed, eval_budget=30)
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed, eval_budget=30)
    assert b.dc.lut.memo is b.acc.memo
    # (B) 탐색이 호출자 memo 를 쓴다. 커널 컨텍스트 `base` 는 S0 수준 스냅샷이라 LUT 손잡이만 호출자 것으로 바꾼다.
    b.sctx.dc = dataclasses.replace(b.sctx.dc, lut=b.dc.lut)
    fa = find_front(a.sctx, [theta_r4c()])
    fb = find_front(b.sctx, [theta_r4c()])
    assert a.sctx.dc.lut.memo is not a.acc.memo and b.sctx.dc.lut.memo is b.acc.memo
    assert dict(fa.perf)["stops_wall_budget"] == 0 and dict(fb.perf)["stops_wall_budget"] == 0
    assert front_signature(fa) == front_signature(fb)
    assert fa.front or fa.pending_front or fa.unmeasured_front        # 공허한 비교 방지
    ta, tb = _eval_table(a.sctx), _eval_table(b.sctx)
    assert len(ta) > 1
    assert ta == tb
    assert fa.run_id == fb.run_id


def test_caller_capacity_constant_does_not_influence_search(tmp_path, lut_sealed):
    """A-T12 (옮겨 온 성질 3): 호출자 memo 상한 1 과 4096 -> 탐색 memo 상한(탐색 뒤)·정의역·front·평가 결과 모두 같다, 탐색 memo 상한은
    호출자 상수가 아니다."""
    acc1, s1 = _build_with_caller_cap(tmp_path / "c1", lut_sealed, 1)
    acc2, s2 = _build_with_caller_cap(tmp_path / "c4096", lut_sealed, 4096)
    assert s1.dc.lut.memo is not acc1.memo and s2.dc.lut.memo is not acc2.memo
    assert s1.domain == s2.domain
    f1 = find_front(s1, [theta_r4c()])
    f2 = find_front(s2, [theta_r4c()])
    assert dict(f1.perf)["stops_wall_budget"] == 0 and dict(f2.perf)["stops_wall_budget"] == 0
    assert dict(f1.perf)["kernel_calls"] > 0                          # 전제: 커널 평가가 있었다(상한이 정해진 뒤 비교)
    assert _caps(s1.dc.lut.memo) == _caps(s2.dc.lut.memo)
    assert all(v != 1 and v != 4096 for v in _caps(s1.dc.lut.memo).values())
    assert front_signature(f1) == front_signature(f2)
    assert _eval_table(s1) == _eval_table(s2)
