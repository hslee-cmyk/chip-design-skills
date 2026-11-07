"""CONTRACT 3.10 [r4] `evaluate(sctx, theta, cells, parent=None, origin=())` -- 순서·계수·캐시·실패·S3 줄 + I-1·I-2·I-3·I-5·I-12.

기대값: 계수는 계약 1~7 단계 문장 그대로, 목적·제약은 결과 스냅샷 입력 열로 conftest(`expected_objectives`·`expected_rows`)
가 계산, ss 행은 metrics `ss_evaluate` 가 낸 값(상류 패키지 결과)을 3.20 식으로 정규화.
"""
import json
import re
from pathlib import Path

import pytest

from gmid_engine.metrics import ss_evaluate
from gmid_engine.search import (
    STATUS_FAILED,
    STATUS_OUTSIDE_DOMAIN,
    STATUS_PENDING_SEAL7,
    STATUS_SEALED,
    STATUS_UNDEFINED,
    EvalResult,
)

from .conftest import (
    evaluate,           # [FS-1 서명 맞춤] 손 wf 를 끼운 공개 evaluate 래퍼 (conftest `evaluate`)
    hand_wf_of,
    CODE_FP,
    CELLS_C,
    CELLS_P,
    PENDING,
    GRID,
    W_MIN,
    build_case,
    circuit_c,
    circuit_n,
    expected_objectives,
    expected_rows,
    snap_of,
    theta_n,
    theta_r4c,
)
from .conftest import block_row, row_delta  # [XRUN-F1 card B C1] 실행 계수 행

AXIS_CONS = (("power_dc_w", "<=", 1e-3, None), ("area_search_m2", "<=", 1e-9, None))
SS_CONS = (("gain_ss_db", ">=", 10.0, None),)


def th_sorted(th):
    return tuple(sorted(th.items()))


def counters(s):
    return dict(s.counters)


def read_evals(root, ctx_fp):
    p = Path(root) / ctx_fp / "evals.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


@pytest.fixture
def case_c(tmp_path, lut_sealed, short_root):
    return build_case(tmp_path, circuit_c(), lut_sealed, constraints=AXIS_CONS + SS_CONS, archive_root=short_root), \
        short_root


def test_sealed_point_objectives_and_constraint_rows(case_c):
    case, root = case_c
    s = case.sctx
    th = theta_r4c()
    r = evaluate(s, th_sorted(th), CELLS_C)
    assert isinstance(r, EvalResult)
    assert r.status == STATUS_SEALED and r.seq == 1 and r.failure is None
    # [xrun] 계수 6키(interface card C1 -- 디스크 실패 적중 계수 삭제, 설계 40 v1.10 §2.4.3 '디스크 실패 기록 읽기' 삭제)
    assert counters(s) == {"requests": 1, "kernel_calls": 1, "hits": 0, "fail_hits": 0,
                           "outside_domain": 0, "recompute_same_key": 0}
    snap = snap_of(r)
    e = expected_objectives(snap)
    o = r.objectives
    assert o.power_w == pytest.approx(e["power"], rel=1e-12)
    assert o.area_m2 == pytest.approx(e["gate_area"], rel=1e-12)
    assert o.power_resolution_w == pytest.approx(e["bp"], rel=1e-12)
    # 제약 = constraint_rows 행 + 목적 축 spec 행 + ss 행 (그 순서)
    base_rows, undef = expected_rows(snap, W_MIN, GRID)
    assert undef == []
    names = [x.name for x in r.constraints]
    n0 = len(base_rows)
    assert names[:n0] == [n for n, _ in base_rows]
    for row, (_, c) in zip(r.constraints[:n0], base_rows):
        assert row.c == pytest.approx(c, rel=1e-9)
    spec_rows = {x.name: x for x in r.constraints[n0:n0 + 2]}
    assert set(spec_rows) == {"spec:power_dc_w<=", "spec:area_search_m2<="}
    assert spec_rows["spec:power_dc_w<="].c == pytest.approx((1e-3 - e["power"]) / e["bp"], rel=1e-9)
    assert spec_rows["spec:area_search_m2<="].c == pytest.approx((1e-9 - e["gate_area"]) / (GRID * W_MIN), rel=1e-9)
    ss_rows = r.constraints[n0 + 2:]
    # r6: 봉인 점 ss = ss_evaluate(sealed, dc, θ, ss_constraints, (), junction=sctx.junction), 분모 = MetricResult.resolution
    ref = ss_evaluate(r.evaluation.sealed, case.dc, th, s.ss_constraints, (), junction=s.junction)
    (res,) = [res for req, res in ref.ss.entries if req.metric == "gain_ss_db"]
    assert res.value is not None and res.resolution is not None and res.resolution > 0
    assert len(ss_rows) == 1 and ss_rows[0].name == "ss:0:gain_ss_db>="
    assert ss_rows[0].c == pytest.approx((res.value - 10.0) / res.resolution, rel=1e-9)
    assert ss_rows[0].active == (ss_rows[0].c <= 1)
    assert tuple(r.unmeasured) == ()
    # 원뿔 행: 회로 C 의 두 MOS 행은 기저 M2 하나 -> c = 1.
    assert [(x.name, x.c) for x in r.cone] == [("current_cone:M1", 1.0), ("current_cone:M2", 1.0)]


def test_cache_hit_returns_same_object_no_kernel_no_s3(case_c):
    case, root = case_c
    s = case.sctx
    th = th_sorted(theta_r4c())
    r1 = evaluate(s, th, CELLS_C)
    n_lines = len(read_evals(root, s.context_fp))
    r2 = evaluate(s, th, CELLS_C, origin=("other",))
    assert r2 is r1
    c = counters(s)
    assert (c["requests"], c["kernel_calls"], c["hits"], c["recompute_same_key"]) == (2, 1, 1, 0)
    assert len(read_evals(root, s.context_fp)) == n_lines == c["kernel_calls"]        # I-2


def test_outside_domain_no_kernel_no_s3_cached(case_c):
    case, root = case_c
    s = case.sctx
    th = th_sorted(theta_r4c(i2=-1e-5))
    r = evaluate(s, th, CELLS_C)
    assert r.status == STATUS_OUTSIDE_DOMAIN and r.seq == -1
    c = counters(s)
    assert (c["kernel_calls"], c["outside_domain"]) == (0, 1)
    assert read_evals(root, s.context_fp) == []
    assert evaluate(s, th, CELLS_C) is r
    assert counters(s)["hits"] == 1 and counters(s)["outside_domain"] == 1


def test_candidate_failure_recorded_and_cached(case_c):
    """봉인 7 위반(VDS < VDsat + tol: y 작게·M1 vgs 크게) -> SealViolationError -> STATUS_FAILED + record, fail_hits."""
    case, root = case_c
    s = case.sctx
    th = th_sorted(theta_r4c(y=0.1, v1=1.5))
    r = evaluate(s, th, CELLS_C)
    assert r.status == STATUS_FAILED and r.failure is not None and r.seq == 1
    assert counters(s)["kernel_calls"] == 1
    lines = read_evals(root, s.context_fp)
    assert len(lines) == 1 and lines[0]["ok"] is False and "fail" in lines[0] and lines[0]["status"] == STATUS_FAILED
    r2 = evaluate(s, th, CELLS_C)
    assert r2 is r
    c = counters(s)
    assert (c["hits"], c["fail_hits"], c["kernel_calls"]) == (1, 1, 1)


def _as_failure_line(line):
    """엔진이 쓴 성공 evals 줄(같은 schema·code·cells·θ hex)을 ok 아닌 줄로 손으로 바꾼다 -- 옛 '디스크 실패 적중'이 받던 입력 형식
    (옛 tests/search/test_layer0_center.py 디스크 주입 helper 가 쓰던 구성, 0538dec). 이 줄을 엔진이 읽지 않아야 한다(C5)."""
    d = {k: v for k, v in line.items() if k not in ("objectives", "power_resolution_w", "snapshot_fp")}
    d.update(ok=False, status=STATUS_FAILED, constraints=[], unmeasured=[],
             fail={"class": "SEAL_VIOLATION", "devices": [], "margin": None,
                   "detail": {"reason": "empty_window", "node": "out", "lo": 1.8, "hi": 0.0, "item": 7, "constraints": 3}})
    return d


def test_hand_written_failure_line_is_not_read_by_new_context(tmp_path, lut_sealed, short_root):
    """[xrun XR-3] interface card C5 '두 번째 실행의 탐색은 첫 실행(또는 누가 써 넣은) 실패 줄을 실패로 받지 않는다'(설계 40 v1.10 §2.4.3
    'S3' 행: 엔진은 S3 evals·runs 를 실행 사이에 읽지 않는다). oracle (a) 구성: 같은 θ 를 같은 입력으로 새 컨텍스트에서 평가하면 결과 상태는
    첫 평가와 같아야 하고(S3 폴더 내용과 무관), 커널을 한 번 부르고, S3 에는 계속 쓴다(evals 줄 1개 추가)."""
    th = th_sorted(theta_r4c())
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed, archive_root=short_root)
    ra = evaluate(a.sctx, th, CELLS_C)
    assert ra.status == STATUS_SEALED                                    # 전제: 성공 평가
    p = Path(short_root) / a.sctx.context_fp / "evals.jsonl"
    (ok_line,) = read_evals(short_root, a.sctx.context_fp)
    with open(p, "a", encoding="utf-8") as fh:                           # 같은 θ 의 실패 줄을 손으로 붙인다
        fh.write(json.dumps(_as_failure_line(ok_line)) + "\n")
    n_before = len(read_evals(short_root, a.sctx.context_fp))
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed, archive_root=short_root)
    assert b.sctx.context_fp == a.sctx.context_fp                        # 전제: 같은 S3 실행 폴더
    rb = evaluate(b.sctx, th, CELLS_C)
    assert rb.status == ra.status and rb.failure is None
    assert counters(b.sctx)["kernel_calls"] == 1
    after = read_evals(short_root, a.sctx.context_fp)
    assert len(after) == n_before + 1 and after[-1]["ok"] is True       # S3 는 출력으로 계속 쓴다(C5)


def test_kernel_value_error_propagates(case_c):
    """I-5: check_theta 의 ValueError(y 범위 밖, 원뿔은 안) 는 evaluate 밖으로 -- kernel_calls 는 증가한 채."""
    case, _ = case_c
    s = case.sctx
    with pytest.raises(ValueError):
        evaluate(s, th_sorted(theta_r4c(y=1.5)), CELLS_C)
    assert counters(s)["kernel_calls"] == 1


def test_pending_point_ss_all_unmeasured(tmp_path, lut_pending):
    """I-12: 봉인 7 대기 점 -> ss 제약 행 0, 전부 (metric, op, ss_requires_sealed_snapshot)."""
    case = build_case(tmp_path, circuit_c(), lut_pending, constraints=AXIS_CONS + SS_CONS)
    r = evaluate(case.sctx, th_sorted(theta_r4c()), CELLS_C)
    assert r.status == STATUS_PENDING_SEAL7
    assert not any(x.name.startswith("ss:") for x in r.constraints)
    assert [tuple(u) for u in r.unmeasured] == [("gain_ss_db", ">=", "ss_requires_sealed_snapshot")]
    assert any(x.name.startswith("spec:power_dc_w") for x in r.constraints)       # 목적·제약은 정의됨(4절)
    assert r.objectives is not None and r.objectives.power_resolution_w is not None


def test_sealed_point_with_undeclared_passive_is_unmeasured(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(with_cap=True), lut_sealed, constraints=SS_CONS,
                      elements=(("CL", "capacitor", PENDING),))
    r = evaluate(case.sctx, th_sorted(theta_r4c()), CELLS_C)
    assert r.status == STATUS_SEALED
    un = [tuple(u) for u in r.unmeasured]
    assert len(un) == 1 and un[0][:2] == ("gain_ss_db", ">=") and "passive_value_undeclared" in un[0][2]
    assert not any(x.name.startswith("ss:") for x in r.constraints)


def test_power_resolution_none_is_undefined(tmp_path, lut_sealed):
    """3.10 6: b_P None -> STATUS_UNDEFINED (회로 N: 레일 채널은 0 V gnd 뿐)."""
    case = build_case(tmp_path, circuit_n(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=(1e3, 1e6))
    r = evaluate(case.sctx, th_sorted(theta_n(case.dc)), CELLS_P)
    assert r.status == STATUS_UNDEFINED


def test_evals_record_fields(case_c):
    case, root = case_c
    s = case.sctx
    th = theta_r4c()
    r = evaluate(s, th_sorted(th), CELLS_C, origin=(("stage", "start"),))
    (rec,) = read_evals(root, s.context_fp)
    for k in ("seq", "schema_fp", "cells", "w_fixed_fp", "theta_hex", "theta", "status", "ok", "origin", "objectives",
              "power_resolution_w", "constraints", "unmeasured", "snapshot_fp", "code_fp", "wf_keys"):
        assert k in rec, k
    assert rec["wf_keys"] == list(hand_wf_of(s).keys)                                  # [FS-1 E-5] S3 줄 wf_keys == list(wf.keys)
    assert rec["seq"] == r.seq == 1 and rec["ok"] is True and rec["status"] == STATUS_SEALED
    assert rec["schema_fp"] == s.schema_fp and rec["code_fp"] == s.code_fp
    assert rec["theta_hex"] == [float(v).hex() for _, v in th_sorted(th)]
    assert rec["objectives"]["power_dc_w"] == r.objectives.power_w
    assert rec["objectives"]["area_search_m2"] == r.objectives.area_m2
    assert [c["name"] for c in rec["constraints"]] == [x.name for x in r.constraints]


# [XRUN-F1 card C] 삭제: test_eval_budget_derived_once_after_n_plus_one -- evaluate 가 n_θ+1 번째 평가에서 E_B 를 유도한다는 옛 계약이다.
# 계약 C6 은 evaluate 가 eval_times 만 기록한다고 정한다. 대체: test_evaluate_does_not_derive_or_change_eval_budget(이 파일, 불변 단언),
# 유도 자체는 test_search_ceiling.py 가 본다.


def test_parent_reuses_lineage(case_c):
    """parent = 앞 결과 -> sizing 은 그 lineage 에서 이어 계산(current 성분만 다르면 dc_currents·dc_solve 각 1회 -- [WB-1] 노드 풀이 블록이 W 블록과 합쳐졌다, I-4 와 같은 근거)."""
    from gmid_engine.sizing import dc_solve, dc_currents
    case, _ = case_c
    s = case.sctx
    base = evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    # [XRUN-F1 card B C1·C6] 계수 = 그 탐색 컨텍스트 실행(sctx.dc.counters)의 행 computes(인덱스 4)
    c0, u0 = block_row(s.dc.counters, dc_solve.name)[4], block_row(s.dc.counters, dc_currents.name)[4]
    r = evaluate(s, th_sorted(theta_r4c(i2=1.1e-5)), CELLS_C, parent=base)
    assert r.status == STATUS_SEALED
    assert block_row(s.dc.counters, dc_solve.name)[4] == c0 + 1
    assert block_row(s.dc.counters, dc_currents.name)[4] == u0 + 1


def test_repeated_requests_kernel_equals_unique_keys(tmp_path, lut_sealed):
    """I-1: 같은 θ 를 섞어 여러 번 요청 -> kernel_calls == 고유 키 수, recompute_same_key 0, 같은 키 = 같은 객체."""
    import random
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    s = case.sctx
    pool = [th_sorted(theta_r4c(i2=1e-5 * (1 + 0.05 * k), y=0.45 + 0.01 * k)) for k in range(5)]
    pool.append(th_sorted(theta_r4c(i2=-1e-5)))                       # 정의역 밖도 캐시
    rng = random.Random(7)
    seen = {}
    for _ in range(40):
        th = rng.choice(pool)
        r = evaluate(s, th, CELLS_C)
        if th in seen:
            assert r is seen[th]
        seen[th] = r
    c = counters(s)
    assert c["requests"] == 40
    assert c["kernel_calls"] == len([t for t in seen if seen[t].status != STATUS_OUTSIDE_DOMAIN])
    assert c["recompute_same_key"] == 0
    assert c["hits"] == 40 - len(seen)


def test_pending_point_passive_values_include_passive_theta(tmp_path, lut_pending):
    """r6: 봉인 아닌 점의 metrics_dc 수동 값 = spec 값 ∪ θ resistance·capacitance·ss_resistance -> 값 미정 목록에 없음,
    단위 면적 선언이 없어 passive_area_undeclared 에 든다."""
    from .conftest import Z_ELEMENTS, circuit_z, theta_z
    case = build_case(tmp_path, circuit_z(), lut_pending, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10),
                      constraints=SS_CONS)
    r = evaluate(case.sctx, th_sorted(theta_z(case.dc)), CELLS_C)
    assert r.status == STATUS_PENDING_SEAL7
    assert tuple(r.objectives.passive_value_undetermined) == ()
    assert tuple(r.objectives.passive_area_undeclared) == ("Cz", "Rz")
    assert [tuple(u) for u in r.unmeasured] == [("gain_ss_db", ">=", "ss_requires_sealed_snapshot")]


def test_sealed_point_with_passive_theta_has_ss_row(tmp_path, lut_sealed):
    """DEC-92: θ capacitance·ss_resistance 가 ss 계에 들어가 봉인 점의 ss 제약이 측정된다(S-20 해소)."""
    from .conftest import Z_ELEMENTS, circuit_z, theta_z
    case = build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10),
                      constraints=SS_CONS)
    s = case.sctx
    th = theta_z(case.dc)
    r = evaluate(s, th_sorted(th), CELLS_C)
    assert r.status == STATUS_SEALED and tuple(r.unmeasured) == ()
    ref = ss_evaluate(r.evaluation.sealed, case.dc, th, s.ss_constraints, (), junction=s.junction)
    (res,) = [x for q, x in ref.ss.entries if q.metric == "gain_ss_db"]
    (row,) = [c for c in r.constraints if c.name.startswith("ss:")]
    assert row.c == pytest.approx((res.value - 10.0) / res.resolution, rel=1e-9)

# ---------------------------------------------------------------- [U7 2026-10-09] 구조 입력 -> S3 evals 의 블록 잔차 기록
# oracle (d) 설계 41 §2.2 '평가마다 다음을 S2 ss 와 S3 evals 요약에 쓴다 -- gain_residual_db·ss.block_gain·ss.rout_residual_ohm' +
# metrics CONTRACT 10.7('kernel.evaluate 가 S3 evals 줄에 block_residual 을 쓴다', [U17 ①-b] S1v 필드가 있는 커널 컨텍스트). (a) 회로 C 는 단일 이득 블록
# (CS + PMOS 전류원 부하) -> 분해 = 전회로, 잔차 0, 전회로 이득 = 같은 점의 gain_ss_db 값.

def test_u7_structure_writes_block_residual_to_evals(tmp_path, lut_sealed_cdd, short_root):
    lut_sealed = lut_sealed_cdd      # [WB-1 E-18] 구조 경로의 drain 용량은 CDD 열 -- CDD 열이 있는 같은 r4 toy
    from gmid_engine.graph import build_s1, build_s1v
    from gmid_engine.search import build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=AXIS_CONS + SS_CONS)
    inputs = dc_inputs_from_spec(case.spec)
    run = dict(donors=case.dc.donors, counters=case.dc.counters)      # [XRUN-F1 card B C6] 같은 test = 같은 실행
    s1 = build_s1(case.td, dict(inputs.supplies_v), **run)
    s1v = build_s1v(s1, case.spec, count_budget=10 ** 6, stop_on_unsupported=False, **run)
    # [U17 ①-b] 구조 입력 = S1v 필드가 있는 S0 수준 S1Graph 로 만든 커널 컨텍스트(build_search_context(s1v=) 삭제, 40 §2.4.7·§2.4.8)
    dc = build_kernel_context(s1v, inputs, case.dc.lut, **run)
    s = build_search_context(dc, case.spec, case.settings, short_root, case.pdk, case.rule, code_fp=CODE_FP)
    assert s.structure is not None and len(s.structure.views) >= 1
    r = evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    assert r.status == STATUS_SEALED
    (rec,) = read_evals(short_root, s.context_fp)
    rows = [dict(x) for x in (tuple(tuple(kv) for kv in rep) for rep in rec["block_residual"])]
    assert len(rows) == 1
    assert abs(rows[0]["gain_residual_db"]) <= 1e-9
    ss_row = [x for x in r.constraints if x.name == "ss:0:gain_ss_db>="]
    assert len(ss_row) == 1
    ref = ss_evaluate(r.evaluation.sealed, case.dc, theta_r4c(), s.ss_constraints, (), junction=s.junction)
    (g,) = [res.value for req, res in ref.ss.entries if req.metric == "gain_ss_db"]
    assert rows[0]["full_gain_db"] == pytest.approx(g, rel=1e-12)


def test_u7_without_structure_no_block_residual_record(tmp_path, lut_sealed, short_root):
    # [FS-1 A-196 판정 §6 test_kernel] `case_c` 는 정정 경로 `build_case`(단계 A -> B, A-188)라 구조(S1v)가 생겼다 -> 'without structure' 전제가 test 입력과 어긋났다.
    # 구조 없는 컨텍스트(S1v 필드 없는 S0 수준 S1Graph 로 커널·탐색 컨텍스트, `test_off_judged._path_case` 와 같은 구성)를 따로 만든다.
    from gmid_engine.graph import build_s1
    from gmid_engine.search import SearchSettings, build_search_context, open_run
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
    from .conftest import SRC, load_spec, new_access, write_decls
    td, spec = load_spec(tmp_path / "case", circuit_c(), constraints=AXIS_CONS + SS_CONS)
    inputs = dc_inputs_from_spec(spec)
    donors, counters_ = open_run()
    dc = build_kernel_context(build_s1(td, dict(inputs.supplies_v), donors=donors, counters=counters_), inputs, new_access(lut_sealed),
                              donors=donors, counters=counters_)
    pdk, rule = write_decls(tmp_path / "pdk")
    s = build_search_context(dc, spec, SearchSettings(600.0, 40, None, SRC, None), short_root, pdk, rule, code_fp=CODE_FP)
    assert s.dc.base.value("graph", "s1v", "metric_structure") is None, "전제: S1v 측정 구조(metric_structure)가 없다"
    evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    (rec,) = read_evals(short_root, s.context_fp)
    assert "block_residual" not in rec



# ---------------------------------------------------------------- [회귀 9065d5f, _audit_u17_1c_r2 §F-2] 비봉인점 경로의 passive_values extras
# 설계 40 §2.4.1 'FD 스텝은 그 성분을 읽는 블록만 계산(WP-23 (5))'. 비봉인점(pending_seal_7)에서도 `evaluate` 가 GB5 블록 `passive_values` 를
# 부른다(§2.4.7). 같은 dc_gm 스냅샷을 고정하려고 DC 풀이(`size_and_seal`)를 첫 점의 평가로 바꿔 끼우고(그 스냅샷엔 첫 점의 passive_value
# 필드·입력 버전이 있다), MOS θ 만 다른 θ 로 평가하면 블록은 재사용(computes 0)이어야 한다 -- 호출부가 θ 전체를 extras 로 넘기면 computes 1.
# 수동소자 θ(capacitance·ss_resistance)를 바꾸면 computes 1, 값은 새 θ 값(손).

def test_pending_point_passive_values_reused_on_mos_theta_only_change(tmp_path, lut_pending, monkeypatch):
    import importlib
    from gmid_engine.metrics import passive_values
    from .conftest import Z_ELEMENTS, circuit_z, theta_z
    kernel = importlib.import_module("gmid_engine.search.kernel")
    case = build_case(tmp_path, circuit_z(), lut_pending, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10),
                      constraints=SS_CONS)
    s = case.sctx
    th0 = theta_z(case.dc)
    r0 = evaluate(s, th_sorted(th0), CELLS_C)
    assert r0.status == STATUS_PENDING_SEAL7
    pv0 = dict(r0.evaluation.snapshot.column("device", "passive_value"))
    assert pv0 == {"Cz": th0[("capacitance", "Cz")], "Rz": th0[("ss_resistance", "Rz")]}
    fixed = r0.evaluation
    monkeypatch.setattr(kernel, "size_and_seal", lambda dc, theta, wf, parent=None, w_request=(), realized=None, layout=None: fixed)       # [FS-1 §4.1] wf 필수 위치 인자

    th_mos = dict(th0)
    th_mos[("ln_idu", "M1")] = th0[("ln_idu", "M1")] + 0.01
    # [XRUN-F1 card B C1·C6] 계수 = 그 탐색 컨텍스트 실행(sctx.dc.counters)의 passive_values 행 구간 증분
    before = block_row(s.dc.counters, passive_values.name)
    r1 = evaluate(s, th_sorted(th_mos), CELLS_C)
    assert r1.status == STATUS_PENDING_SEAL7
    st = row_delta(block_row(s.dc.counters, passive_values.name), before)
    assert (st[4], st[1]) == (0, 1), st
    assert dict(r1.evaluation.snapshot.column("device", "passive_value")) == pv0

    for key in (("capacitance", "Cz"), ("ss_resistance", "Rz")):
        th_p = dict(th0)
        th_p[key] = th0[key] * 1.1
        before = block_row(s.dc.counters, passive_values.name)
        r2 = evaluate(s, th_sorted(th_p), CELLS_C)
        st = row_delta(block_row(s.dc.counters, passive_values.name), before)
        assert (st[4], st[5]) == (1, 0), (key, st)
        assert dict(r2.evaluation.snapshot.column("device", "passive_value"))[key[1]] == th0[key] * 1.1


# =====================================================================================================================
# [XRUN-F1 card B] interface card C4·C7·C8 -- 계보 무관 이식(B-T18), 실패 평가의 부분 스냅샷(B-T19), 부분 스냅샷 재사용(B-T20).
# oracle: (식) C4 판정 2 '같은 lineage 가 아니고 색인에 같은 입력 결과가 있으면 이식(graft, 블록 함수 0)', C7 부분 스냅샷 정의 문장,
# (비교) 실패 줄 snapshot_fp == partial.fp, 실행 계수(C1, sctx.dc.counters) 행의 구간 증분. 실패를 일으키는 입력은 구성으로 정한다 --
# (1) 빈 창 회로(MA nmos (x, vdd, vdd) -> x ≥ V(vdd), MB pmos (x, gnd, gnd) -> x ≤ V(gnd): 기둥 블록 창이 빈다, test_find_front 와 같은 회로),
# (2) 봉인 7 위반 θ(test_candidate_failure_recorded_and_cached 와 같은 θ), (3) ss 단계 LUT 조회 실패(용량 표 VS 축이 소자 VSB 0 을 덮지 않는
# r4 LUT -- DC 는 슬라이스 표로 봉인되고 ss_dev 의 caps 조회만 축 밖, metrics test_lut_failure_is_seal_violation 'caps_vs_axis' 와 같은 구성).
# 각 경우 전제(status == failed, 실패 분류·detail 원인)를 먼저 단언한다.
# =====================================================================================================================

DC_ORDER = ("dc_currents", "dc_lengths", "dc_solve", "dc_solve")          # sizing CONTRACT 7절 평가 블록 4개 호출 순서


def _rows_now(s):
    return {r.block: tuple(getattr(r, f) for f in ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input"))
            for r in s.dc.counters.snapshot().blocks}


def _assert_no_same_input_recompute(s):
    # oracle 대조: card B 판정 '같은 입력 재계산 0' -- 실행 전체(C8 'blocks = 실행 전체')의 모든 행 recomputes_same_input = 0
    assert all(r[5] == 0 for r in _rows_now(s).values()), _rows_now(s)


def test_graft_across_lineage_without_parent(tmp_path, lut_sealed):
    """B-T18(C4·C8): parent 없이 두 평가 -- 전류 성분 같고 M1 L 만 다르다(칸 0 -> 1). 두 번째 평가의 전류 블록은 같은 lineage 가 아니고
    (두 평가 모두 S0 수준 기준 스냅샷에서 시작) 같은 입력이 이 실행 색인에 있으므로 이식(grafts +1, computes +0). 같은 입력 재계산 0."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    s = case.sctx
    r1 = evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    before = block_row(s.dc.counters, "dc_currents")
    r2 = evaluate(s, th_sorted(theta_r4c(l1=2e-6)), (1, 1))
    assert counters(s)["kernel_calls"] == 2                                  # 전제: 두 평가 모두 커널 평가
    assert r1.status != STATUS_OUTSIDE_DOMAIN and r2.status != STATUS_OUTSIDE_DOMAIN
    d = row_delta(block_row(s.dc.counters, "dc_currents"), before)
    assert (d[0], d[1], d[2], d[4], d[5]) == (1, 0, 1, 0, 0), d               # calls 1, reuse 0, graft 1, compute 0, 재계산 0
    _assert_no_same_input_recompute(s)


def _empty_window_case(tmp_path, lut, root):
    from .conftest import mos, topo
    window = topo("hand_empty_window_ps",
                  [mos("MA", "nmos", "x", "vdd", "vdd"), mos("MB", "pmos", "x", "gnd", "gnd"), mos("MC", "nmos", "x", "inp", "gnd")],
                  {"inp": ("input", "single_ended_input"), "x": ("output", "single_ended_output")})
    return build_case(tmp_path, window, lut, eval_budget=20, archive_root=root)


def _failed_line_and_result(case, root):
    """find_front 가 남긴 S3 evals 실패 줄 하나와 그 θ 의 EvalResult(같은 탐색 컨텍스트 캐시 적중 -- 같은 객체)."""
    from gmid_engine.search import find_front
    find_front(case.sctx, [])
    lines = read_evals(root, case.sctx.context_fp)
    failed = [x for x in lines if x["status"] == STATUS_FAILED]
    assert failed, "전제: 실패 평가가 S3 에 기록됐다"
    line = failed[0]
    r = evaluate(case.sctx, {tuple(k): v for k, v in line["theta"]}, tuple(line["cells"]))
    assert r.seq == line["seq"]
    return line, r


def test_partial_snapshot_dc_block_failure(tmp_path, lut_sealed, short_root):
    """B-T19 (1) C7: DC 블록 단계(전류·길이·기둥·폭) 실패 -- partial.block_versions 에 앞 블록은 있고 실패한 블록(여기서는 기둥 dc_solve,
    빈 창)은 없다, 봉인 보고 없음. 실패 줄 snapshot_fp == partial.fp, evaluation 은 None."""
    from gmid_engine.core import GraphSnapshot
    case = _empty_window_case(tmp_path, lut_sealed, short_root)
    line, r = _failed_line_and_result(case, short_root)
    assert r.status == STATUS_FAILED and r.failure is not None                          # 전제
    assert r.failure.failure_class == "SEAL_VIOLATION" and dict(r.failure.detail)["reason"] == "empty_window"
    assert r.evaluation is None
    assert isinstance(r.partial, GraphSnapshot)
    bv = r.partial.block_versions
    assert "dc_currents" in bv and "dc_lengths" in bv                                   # 앞 블록
    assert "dc_solve" not in bv and "dc_solve" not in bv                             # 실패한 블록과 그 뒤
    assert "dc_seal_report" not in bv
    assert line["ok"] is False and "fail" in line
    assert line["snapshot_fp"] == r.partial.fp                                          # C7 S3 evals 실패 줄
    _assert_no_same_input_recompute(case.sctx)


def test_partial_snapshot_seal_violation(case_c):
    """B-T19 (2) C7: 봉인 위반 -- partial.block_versions 에 dc_seal_report 가 있다(봉인 판정까지 쓴 스냅샷), ss 블록은 없다."""
    from gmid_engine.core import GraphSnapshot
    case, root = case_c
    s = case.sctx
    r = evaluate(s, th_sorted(theta_r4c(y=0.1, v1=1.5)), CELLS_C)
    assert r.status == STATUS_FAILED and r.failure is not None                          # 전제
    assert r.failure.failure_class == "SEAL_VIOLATION" and "items" in dict(r.failure.detail)   # seal_dc 의 위반(항목 표)
    assert isinstance(r.partial, GraphSnapshot)
    bv = r.partial.block_versions
    assert "dc_seal_report" in bv
    assert all(b in bv for b in DC_ORDER)
    assert "ss_dev" not in bv
    (line,) = [x for x in read_evals(root, s.context_fp) if x["seq"] == r.seq]
    assert line["ok"] is False and line["snapshot_fp"] == r.partial.fp


def _write_r4_lut_narrow_cap(root):
    """sizing conftest `write_r4_lut` 과 같은 슬라이스 표(DC 봉인 가능) + 용량 표 VS 축만 0.5 V 부터(소자 VSB 0 이 축 밖) -- ss_dev caps 조회 실패."""
    import hashlib
    import numpy as np
    from gmid_engine.lut import load_lut_set
    from sizing.conftest import DEVICE_OF, R4_GRIDS, SUFFIX, TOY_SPEC, W_M, r4_arrays
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for kind in ("nmos", "pmos"):
        p = root / ("r4_%s.npz" % kind)
        np.savez(p, **r4_arrays(kind, True, 0, (), R4_GRIDS))
        entries.append({"device": DEVICE_OF[kind], "file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    gL, gG, gD, _gS = (np.asarray(g, dtype=float) for g in R4_GRIDS)
    gS = np.asarray((0.5, 1.0, 1.5, 2.0))                               # VSB 0 을 덮지 않는 용량 표 VS 축(구성)
    shp = (len(gL), len(gG), len(gD), len(gS))
    cap = {"L": gL, "VGS": gG, "VDS": gD, "VS": gS, "w_ref_m": np.float64(W_M), "corner": np.str_("tt"), "temp_c": np.float64(27.0)}
    for kind in ("nmos", "pmos"):
        cap["CGG" + SUFFIX[kind]] = np.full(shp, 1e-15)
        cap["CGD" + SUFFIX[kind]] = np.full(shp, 2e-16)
        # [JC-1] 접합 항 입력 열(손 식: CGS = CGG − CGD = 8e-16, CSS − CGS = 5e-16, CDD − CGD = 3e-16 -- 모든 칸 같은 값)
        cap["CGS" + SUFFIX[kind]] = np.full(shp, 8e-16)
        cap["CSS" + SUFFIX[kind]] = np.full(shp, 1.3e-15)
        cap["CDD" + SUFFIX[kind]] = np.full(shp, 5e-16)
    np.savez(root / "cap.npz", **cap)
    from toy_bins import retrofit_bins as _retro
    _tb = _retro(root)
    return load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC, bin_rule=_tb.bin_rule, pdk_root=_tb.pdk_root)


def test_partial_snapshot_ss_stage_failure(tmp_path, short_root):
    """B-T19 (3) C7: ss 단계 실패 -- partial.block_versions 에 봉인 스냅샷의 블록(dc_seal_report 포함)이 있다, 실패한 ss_dev 는 없다."""
    from gmid_engine.core import GraphSnapshot
    lut = _write_r4_lut_narrow_cap(tmp_path / "lut_narrow_cap")
    case = build_case(tmp_path / "case", circuit_c(), lut, constraints=SS_CONS, archive_root=short_root)
    s = case.sctx
    r = evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    assert r.status == STATUS_FAILED and r.failure is not None                          # 전제
    det = dict(r.failure.detail)
    assert r.failure.failure_class == "SEAL_VIOLATION" and det["reason"] == "lut_query_failed" and det["device_query"] == "caps"
    assert isinstance(r.partial, GraphSnapshot)
    bv = r.partial.block_versions
    assert "dc_seal_report" in bv and all(b in bv for b in DC_ORDER)
    assert "ss_dev" not in bv
    (line,) = [x for x in read_evals(short_root, s.context_fp) if x["seq"] == r.seq]
    assert line["ok"] is False and line["snapshot_fp"] == r.partial.fp


SEAL_STAGE_BLOCK_ATTRS = ("dc_seal_node_conflict", "dc_seal_vgs_match", "dc_seal_kcl", "dc_seal_bulk_reverse",
                          "dc_seal_region", "dc_seal_kvl_branch", "dc_seal_report")      # [EO-1 범위 4] 7·9 블록 하나


@pytest.mark.parametrize("block_attr", SEAL_STAGE_BLOCK_ATTRS)
def test_partial_snapshot_seal_stage_block_failure(tmp_path, lut_sealed, short_root, monkeypatch, block_attr):
    """B-T19 (4) C5·C7: 봉인 단계 블록(봉인 항목 블록 6개·dc_seal_report) 자체가 후보 실패 예외를 내면 -- (a) 실패에 partial 이 붙고
    (b) 그 partial 은 그 블록에 들어가기 직전 스냅샷(앞 단계 블록 필드까지 있고 그 블록·이후 블록 필드 없음) (c) S3 실패 줄
    snapshot_fp == partial.fp.

    실패 주입(공개 경로): C4 블록 호출 `ComputeBlock.__call__`(gmid_engine.core) 을 클래스 수준에서 감싸, 대상 블록(`block.name`,
    gmid_engine.sizing 공개 블록 객체) 호출에서 블록 함수 대신 C5 `SealViolationError.from_record(record)` 를 올린다. record 는 별도
    탐색 컨텍스트의 봉인 7 위반 평가(test_candidate_failure_recorded_and_cached 와 같은 θ)가 낸 FailureRecord 다.
    oracle 대조: (a) C5 '엔진이 붙이는 곳 -- 커널 DC 블록 단계(그 블록에 들어간 스냅샷)' 규칙을 봉인 단계 블록에 같은 규칙으로 적용(card B
    재판정 결함 -- 봉인 항목 블록 실패에 부분 스냅샷 부착 계약), C7 실패 평가 = 부분 스냅샷. (b) (독립) 감쌈이 잡은 대상 블록 호출 인자 스냅샷(= 들어가기 직전
    스냅샷)의 fp 와 같음 + 감쌈이 센 호출 순서(대상 블록 앞에 불린 블록은 있고 대상·이후는 없다 -- 순서는 피검 출력이 아닌 독립 관찰).
    (c) (비교) C7 'S3 evals 실패 줄에도 snapshot_fp = partial.fp'."""
    import gmid_engine.sizing as sizing
    from gmid_engine.core import ComputeBlock, GraphSnapshot, SealViolationError
    target = getattr(sizing, block_attr).name

    # 주입할 기록: 별도 컨텍스트의 실제 봉인 위반 기록(구성 -- 봉인 7 위반 θ)
    src = build_case(tmp_path / "src", circuit_c(), lut_sealed)
    bad = evaluate(src.sctx, th_sorted(theta_r4c(y=0.1, v1=1.5)), CELLS_C)
    assert bad.status == STATUS_FAILED and bad.failure is not None                    # 전제
    rec = bad.failure

    case = build_case(tmp_path / "case", circuit_c(), lut_sealed, constraints=AXIS_CONS + SS_CONS, archive_root=short_root)
    s = case.sctx
    seen, entered, raised = [], [], []
    orig = ComputeBlock.__call__

    def wrapped(self, snapshot, *extras, **kw):
        seen.append(self.name)
        if self.name == target:
            entered.append(snapshot)
            exc = SealViolationError.from_record(rec)
            raised.append(exc)
            raise exc
        return orig(self, snapshot, *extras, **kw)

    monkeypatch.setattr(ComputeBlock, "__call__", wrapped)
    r = evaluate(s, th_sorted(theta_r4c()), CELLS_C)                                   # 주입 없으면 봉인되는 θ(test_partial_snapshot_none_on_success_...)
    monkeypatch.undo()

    assert len(entered) == 1 and len(raised) == 1                                      # 전제: 대상 블록에 정확히 한 번 들어갔다
    assert r.status == STATUS_FAILED and r.failure is not None and r.evaluation is None  # 전제: 후보 실패
    assert r.failure.failure_class == rec.failure_class
    # (a) partial 부착
    assert isinstance(r.partial, GraphSnapshot)
    assert raised[0].partial is not None and raised[0].partial.fp == r.partial.fp
    # (b) 들어가기 직전 스냅샷
    assert r.partial.fp == entered[0].fp
    bv = r.partial.block_versions
    before = seen[:seen.index(target)]
    assert all(b in bv for b in DC_ORDER)                                               # 앞 단계(DC 블록) 필드 있음
    assert all(b in bv for b in before), [b for b in before if b not in bv]
    assert target not in bv                                                             # 실패한 그 블록 없음
    assert "dc_seal_report" not in bv and "ss_dev" not in bv                            # 이후 블록 없음
    after = [getattr(sizing, a).name for a in SEAL_STAGE_BLOCK_ATTRS if getattr(sizing, a).name not in before]
    assert all(b not in bv for b in after), [b for b in after if b in bv]
    # (c) S3 실패 줄
    (line,) = [x for x in read_evals(short_root, s.context_fp) if x["seq"] == r.seq]
    assert line["ok"] is False and "fail" in line
    assert line["snapshot_fp"] == r.partial.fp


def test_partial_snapshot_none_on_success_and_outside_domain(case_c):
    """B-T19 C7: 성공(봉인) 평가와 정의역 밖 평가의 partial = None(칸 기본값), 실패 평가의 evaluation 은 여전히 None(위 test)."""
    case, root = case_c
    s = case.sctx
    ok = evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    out = evaluate(s, th_sorted(theta_r4c(i2=-1e-5)), CELLS_C)
    assert ok.status == STATUS_SEALED and out.status == STATUS_OUTSIDE_DOMAIN           # 전제
    assert ok.partial is None and out.partial is None
    (line,) = [x for x in read_evals(root, s.context_fp) if x["seq"] == ok.seq]
    assert line["ok"] is True and "snapshot_fp" in line                                 # 성공 줄 형식은 card A 그대로


def test_partial_snapshot_results_reused_by_later_evaluation(tmp_path, lut_sealed):
    """B-T20(C7·C4): 실패 평가(봉인 7 위반)가 계산한 블록 결과(전류·길이 -- 입력은 θ 전류·L 성분뿐)를 같은 블록 입력의 뒤 평가(parent 없음,
    다른 좌표)가 이식한다 -- 그 행 grafts ≥ 1, computes 증분 0, 같은 입력 재계산 0. 실패 평가가 이 실행의 첫 평가라 이식 원천은 그 실패 평가뿐이다."""
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    s = case.sctx
    bad = evaluate(s, th_sorted(theta_r4c(y=0.1, v1=1.5)), CELLS_C)
    assert bad.status == STATUS_FAILED and bad.partial is not None                     # 전제
    assert "dc_currents" in bad.partial.block_versions and "dc_lengths" in bad.partial.block_versions
    before = {b: block_row(s.dc.counters, b) for b in ("dc_currents", "dc_lengths")}
    good = evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    assert good.status == STATUS_SEALED                                                # 전제: 커널 평가
    for b in ("dc_currents", "dc_lengths"):
        d = row_delta(block_row(s.dc.counters, b), before[b])
        assert d[2] >= 1 and d[4] == 0 and d[5] == 0, (b, d)
    _assert_no_same_input_recompute(s)


# =====================================================================================================================
# [XRUN-F1 card C] interface card xrunf1c C6 (C-T9) -- kernel.evaluate 는 eval_times 만 기록한다. sctx.eval_budget·eval_budget_source 불변.
# oracle: (손) 구성 -- 유도 실행(eval_budget None)에서 서로 다른 θ 로 n_θ + 2 번 평가(위 test_eval_budget_derived_once_after_n_plus_one 가
# 옛 계약에서 n_θ + 1 번째 평가가 유도했던 지점을 지나 한 번 더). 평가 전과 같은 값이어야 한다. 평가 시간 목록 길이 = 커널 평가 수(손: 매번 새 θ).
# =====================================================================================================================

def test_evaluate_does_not_derive_or_change_eval_budget(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=None, budget_s=30.0)
    s = case.sctx
    n = len(s.domain.variables)
    b0, src0 = s.eval_budget, s.eval_budget_source
    assert b0 is None
    for k in range(n + 2):
        evaluate(s, th_sorted(theta_r4c(i2=1e-5 * (1 + 0.01 * k))), CELLS_C)
        assert s.eval_budget is None and s.eval_budget_source == src0, k
    assert len(s.eval_times) == n + 2 == dict(s.counters)["kernel_calls"]        # 평가 시간은 기록한다
    assert all(t >= 0.0 for t in s.eval_times)


# =====================================================================================================================
# [FS-1 §4.5] 평가 키에 w_f 칸 키 -- oracle (식) interface card 20261107-fs1 §4.5: E-2 같은 θ·cells·다른 keys = 캐시 적중 0, E-3 같은 wf 두 번 = 적중,
# E-4 실현 키 = 실현 표지만(탐색 스냅샷 지문 없음), E-5 S3 줄 wf_keys (위 test_evals_record_fields).
# =====================================================================================================================
def _two_slice_case(tmp_path, short_root):
    from gmid_engine.search import evaluate as raw_evaluate   # noqa: F401
    from sizing.wb1_toy import write_r4_bins_lut
    lut, _, _ = write_r4_bins_lut(tmp_path / "lut2", widths=(1e-6, 2e-6), jc1_cols=True)      # CDD 열 있는 toy (단계 B 요구, A-190 M-2c)
    return build_case(tmp_path, circuit_c(), lut, constraints=AXIS_CONS + SS_CONS, archive_root=short_root)


def _wf_keys(s, key):
    from gmid_engine.sizing import WfCell, WfInput
    base = hand_wf_of(s)
    return WfInput(tuple(WfCell(c.members, key) for c in base.cells_ref), tuple(key for _ in base.cells_ref))


def test_e2_different_wf_keys_are_different_evaluations(tmp_path, short_root):
    s = _two_slice_case(tmp_path, short_root).sctx
    th = th_sorted(theta_r4c())
    k0 = counters(s)["kernel_calls"]
    ra = evaluate(s, th, CELLS_C, wf=_wf_keys(s, 100))
    rb = evaluate(s, th, CELLS_C, wf=_wf_keys(s, 200))
    c = counters(s)
    assert c["kernel_calls"] - k0 == 2 and c["hits"] == 0                                # 캐시 적중 0, 커널 2회
    assert ra.key.wf_fp != rb.key.wf_fp and ra.key != rb.key


def test_e3_same_wf_twice_hits(tmp_path, short_root):
    s = _two_slice_case(tmp_path, short_root).sctx
    th = th_sorted(theta_r4c())
    wf = _wf_keys(s, 100)
    r1 = evaluate(s, th, CELLS_C, wf=wf)
    h0 = counters(s)["hits"]
    r2 = evaluate(s, th, CELLS_C, wf=wf)
    assert counters(s)["hits"] == h0 + 1 and r2 is r1


def test_e4_realize_key_is_marker_only(tmp_path, short_root):
    """E-4: 실현 evaluate(..., realized=RealizeInput(s1)) 와 RealizeInput(s2) (같은 θ·cells·wf, 다른 탐색 스냅샷 객체) 는 같은 키(실현 표지만)."""
    from gmid_engine.sizing import RealizeInput
    s = _two_slice_case(tmp_path, short_root).sctx
    th = th_sorted(theta_r4c())
    wf = _wf_keys(s, 100)
    s1 = evaluate(s, th, CELLS_C, wf=wf)
    s2 = evaluate(s, th_sorted(theta_r4c(i2=1.1e-5)), CELLS_C, wf=wf)
    assert s1.evaluation.snapshot is not s2.evaluation.snapshot                          # 전제: 다른 스냅샷 객체
    ra = evaluate(s, th, CELLS_C, wf=wf, realized=RealizeInput(s1.evaluation.snapshot))
    rb = evaluate(s, th, CELLS_C, wf=wf, realized=RealizeInput(s2.evaluation.snapshot))
    assert ra.key == rb.key and ra.key.w_fixed_fp is not None
    assert ra.key != s1.key                                                              # 실현 표지가 탐색 키와 갈린다
