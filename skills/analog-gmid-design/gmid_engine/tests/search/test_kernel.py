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
    evaluate,
)

from .conftest import (
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
    assert counters(s) == {"requests": 1, "kernel_calls": 1, "hits": 0, "fail_hits": 0, "disk_hits": 0,
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


def test_disk_failure_hit_same_code_and_invalid_when_code_differs(tmp_path, lut_sealed, short_root):
    """I-3: 같은 S0·code_fp 의 새 context 는 디스크 실패 적중(커널 0, seq −1). code_fp 가 다른 줄은 무효."""
    th = th_sorted(theta_r4c(y=0.1, v1=1.5))
    a = build_case(tmp_path / "a", circuit_c(), lut_sealed, archive_root=short_root)
    ra = evaluate(a.sctx, th, CELLS_C)
    assert ra.status == STATUS_FAILED
    b = build_case(tmp_path / "b", circuit_c(), lut_sealed, archive_root=short_root)
    assert b.sctx.context_fp == a.sctx.context_fp
    assert ra.key in dict(b.sctx.disk_failures)
    rb = evaluate(b.sctx, th, CELLS_C)
    assert rb.status == STATUS_FAILED and rb.seq == -1 and rb.failure is not None
    c = counters(b.sctx)
    assert (c["disk_hits"], c["kernel_calls"]) == (1, 0)
    # code_fp 를 바꾼 줄만 남기면 디스크 적중 없음 -> 커널 1.
    p = Path(short_root) / a.sctx.context_fp / "evals.jsonl"
    recs = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    for rec in recs:
        rec["code_fp"] = "0" * 64
    p.write_text("".join(json.dumps(rec) + "\n" for rec in recs), encoding="utf-8")
    d = build_case(tmp_path / "d", circuit_c(), lut_sealed, archive_root=short_root)
    assert dict(d.sctx.disk_failures) == {}
    rd = evaluate(d.sctx, th, CELLS_C)
    assert rd.status == STATUS_FAILED and counters(d.sctx)["kernel_calls"] == 1 and counters(d.sctx)["disk_hits"] == 0


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
              "power_resolution_w", "constraints", "unmeasured", "snapshot_fp", "code_fp"):
        assert k in rec, k
    assert rec["seq"] == r.seq == 1 and rec["ok"] is True and rec["status"] == STATUS_SEALED
    assert rec["schema_fp"] == s.schema_fp and rec["code_fp"] == s.code_fp
    assert rec["theta_hex"] == [float(v).hex() for _, v in th_sorted(th)]
    assert rec["objectives"]["power_dc_w"] == r.objectives.power_w
    assert rec["objectives"]["area_search_m2"] == r.objectives.area_m2
    assert [c["name"] for c in rec["constraints"]] == [x.name for x in r.constraints]


def test_eval_budget_derived_once_after_n_plus_one(tmp_path, lut_sealed):
    """1.1·3.10 7: eval_budget None -> 평가 시간 수가 n(정의역 연속 변수 수)을 넘는 순간 한 번 E_B 를 정하고 기록."""
    case = build_case(tmp_path, circuit_c(), lut_sealed, eval_budget=None, budget_s=30.0)
    s = case.sctx
    n = len(s.domain.variables)
    assert s.eval_budget is None
    for k in range(n + 1):
        evaluate(s, th_sorted(theta_r4c(i2=1e-5 * (1 + 0.01 * k))), CELLS_C)
        if k < n:
            assert s.eval_budget is None, k
    eb = s.eval_budget
    assert isinstance(eb, int) and eb > 0
    m = re.fullmatch(r"derived_once:floor\(B/median_t_eval\)@n_evals=(\d+)", s.eval_budget_source)
    assert m and int(m.group(1)) == n + 1
    evaluate(s, th_sorted(theta_r4c(i2=3e-5)), CELLS_C)
    assert s.eval_budget == eb                      # 한 번만


def test_parent_reuses_lineage(case_c):
    """parent = 앞 결과 -> sizing 은 그 lineage 에서 이어 계산(current 성분만 다르면 dc_columns 재계산 0, I-4 와 같은 근거)."""
    from gmid_engine.sizing import dc_columns, dc_currents
    case, _ = case_c
    s = case.sctx
    base = evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    c0, u0 = dc_columns.stats().computes, dc_currents.stats().computes
    r = evaluate(s, th_sorted(theta_r4c(i2=1.1e-5)), CELLS_C, parent=base)
    assert r.status == STATUS_SEALED
    assert dc_columns.stats().computes == c0
    assert dc_currents.stats().computes == u0 + 1


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
# metrics CONTRACT 10.7('kernel.evaluate 가 S3 evals 줄에 block_residual 을 쓴다', `build_search_context(s1v=)`). (a) 회로 C 는 단일 이득 블록
# (CS + PMOS 전류원 부하) -> 분해 = 전회로, 잔차 0, 전회로 이득 = 같은 점의 gain_ss_db 값.

def test_u7_structure_writes_block_residual_to_evals(tmp_path, lut_sealed, short_root):
    from gmid_engine.graph import build_s1, build_s1v
    from gmid_engine.search import build_search_context
    from gmid_engine.sizing import dc_inputs_from_spec
    case = build_case(tmp_path, circuit_c(), lut_sealed, constraints=AXIS_CONS + SS_CONS)
    s1 = build_s1(case.td, dict(dc_inputs_from_spec(case.spec).supplies_v))
    s1v = build_s1v(s1, case.spec, count_budget=10 ** 6, stop_on_unsupported=False)
    s = build_search_context(case.dc, case.spec, case.settings, short_root, case.pdk, case.rule, s1v=s1v, code_fp=CODE_FP)
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


def test_u7_without_structure_no_block_residual_record(case_c):
    case, root = case_c
    s = case.sctx
    evaluate(s, th_sorted(theta_r4c()), CELLS_C)
    (rec,) = read_evals(root, s.context_fp)
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
    monkeypatch.setattr(kernel, "size_and_seal", lambda dc, theta, parent=None, w_request=(): fixed)

    th_mos = dict(th0)
    th_mos[("ln_idu", "M1")] = th0[("ln_idu", "M1")] + 0.01
    passive_values.reset_stats()
    r1 = evaluate(s, th_sorted(th_mos), CELLS_C)
    assert r1.status == STATUS_PENDING_SEAL7
    st = passive_values.stats()
    assert (st.computes, st.reuses) == (0, 1), st
    assert dict(r1.evaluation.snapshot.column("device", "passive_value")) == pv0

    for key in (("capacitance", "Cz"), ("ss_resistance", "Rz")):
        th_p = dict(th0)
        th_p[key] = th0[key] * 1.1
        passive_values.reset_stats()
        r2 = evaluate(s, th_sorted(th_p), CELLS_C)
        st = passive_values.stats()
        assert (st.computes, st.recomputes_same_input) == (1, 0), (key, st)
        assert dict(r2.evaluation.snapshot.column("device", "passive_value"))[key[1]] == th0[key] * 1.1
