"""평가 커널 조립 -- θ 하나 -> GB7 DC 정본 + 봉인 + 목적 + 제약, 캐시·S3 (설계 design_mod6_search_front 2.2·2.3·7절).

진입점: `evaluate(sctx, theta, cells, parent=None, origin=()) -> EvalResult`.

* `theta` = {(kind, key): 값} 또는 쌍 iterable(스키마 전 성분), `cells` = L 칸 index 벡터(MOS 이름순), `parent` = 같은
  컨텍스트의 이전 EvalResult(그 `evaluation` 스냅샷을 sizing 이 재사용 -- 바뀐 성분을 읽는 블록만 다시 계산, 필드가 곧 캐시),
  `origin` = S3 기록용 ((키, 값), ...)(단계·ε·시작점 -- 키 밖).
* 순서: 요청 계수 -> 키(`eval_key`) -> 메모리 캐시 적중이면 그대로(커널 0) -> 디스크 실패 캐시(S3 evals 재구성) 적중이면
  실패 결과(커널 0) -> 원뿔 행(`cone_rows`)에 c ≤ 0 이 있으면 `STATUS_OUTSIDE_DOMAIN`(커널 0, 정의역 밖) -> `size_and_seal`.
* 후보 실패는 `CANDIDATE_FAILURE_CLASSES` 만 이름으로 잡아 `STATUS_FAILED` + FailureRecord(N3.14). ValueError·TypeError 등은
  호출 계약 위반이라 잡지 않는다(넓은 except 없음).
* 성공: `seal_status`(봉인 7 대기 스위치) -> 목적(`objective_values`, 점의 b_P 포함 -- None 이면 `STATUS_UNDEFINED`) ->
  제약(`constraint_rows` + 목적 축 spec 제약(전력 분모 = 그 점의 b_P) + `ss_constraint_rows`, 재지 못한 ss 제약은 `unmeasured`).
* E_B(평가 수 예산)가 선언되지 않았으면 평가 수가 n + 1 을 넘는 순간 한 번 ⌊B / median(평가 시간)⌋ 로 정한다(기록).
* 커널을 부른 평가만 S3 evals 에 한 줄(설계 8절). 같은 키를 두 번 계산하면 `recompute_same_key` +1(정상 0).
"""
import statistics
import time
from collections.abc import Mapping

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES
from gmid_engine.metrics import metrics_dc, ss_evaluate
from gmid_engine.sizing import THETA_PASSIVE_KINDS, THETA_RESISTANCE, DcEvaluation, size_and_seal

from .cone_rows import cone_rows
from .constraints import constraint_rows
from .eval_key import eval_key
from .tie_expand import expand_ties
from .objectives import objective_values
from .search_values import (
    ACCEPTED_STATUSES,
    AXIS_AREA,
    AXIS_POWER,
    STATUS_FAILED,
    STATUS_OUTSIDE_DOMAIN,
    STATUS_SEALED,
    STATUS_UNDEFINED,
    ConstraintRow,
    EvalResult,
)
from .seal7_pending import seal_status
from .ss_constraints import ss_constraint_rows

_THETA_PASSIVES = (THETA_RESISTANCE,) + THETA_PASSIVE_KINDS


def _spec_rows(sctx, objectives):
    rows = []
    scale = {AXIS_POWER: objectives.power_resolution_w, AXIS_AREA: sctx.domain.area_resolution_m2}
    value = {AXIS_POWER: objectives.power_w, AXIS_AREA: objectives.area_m2}
    for metric, op, target in sctx.judged_constraints:
        c = (value[metric] - target) / scale[metric] if op == ">=" else (target - value[metric]) / scale[metric]
        rows.append(ConstraintRow("spec:" + metric + op, c, c <= 1))
    return tuple(rows)


def _record(sctx, result, origin):
    if sctx.archive is None:
        return
    rec = {"seq": result.seq, "schema_fp": sctx.schema_fp, "cells": list(result.key.cells),
           "w_fixed_fp": result.key.w_fixed_fp, "theta_hex": list(result.key.theta_hex),
           "theta": [[list(k), v] for k, v in result.theta], "status": result.status,
           "ok": result.status in ACCEPTED_STATUSES, "origin": dict(origin)}
    if result.failure is not None:
        rec["fail"] = result.failure.to_json()
    if result.objectives is not None:
        rec["objectives"] = {AXIS_POWER: result.objectives.power_w, AXIS_AREA: result.objectives.area_m2}
    rec["constraints"] = [{"name": r.name, "c": r.c, "active": r.active} for r in result.constraints]
    rec["unmeasured"] = [list(u) for u in result.unmeasured]
    if result.objectives is not None:
        rec["power_resolution_w"] = result.objectives.power_resolution_w
    if result.evaluation is not None:
        rec["snapshot_fp"] = result.evaluation.snapshot.fp
    sctx.archive.append_eval(rec)


def evaluate(sctx, theta, cells, parent=None, origin=()):
    sctx.counters["requests"] += 1
    theta = expand_ties(sctx.domain.ties, theta if isinstance(theta, Mapping) else dict(theta),
                         sctx.domain.negated, sctx.domain.zeros)    # [r12] 묶인 성분은 대표 값
    pairs = tuple(sorted(theta.items()))
    key = eval_key(sctx.context_fp, sctx.schema_fp, pairs, cells, None)
    hit = sctx.cache.get(key)
    if hit is not None:
        sctx.counters["hits"] += 1
        if hit.status == STATUS_FAILED:
            sctx.counters["fail_hits"] += 1
        return hit
    disk = sctx.disk_failures.get(key)
    cone = cone_rows(sctx.dc.schema, pairs)
    if disk is not None:
        sctx.counters["disk_hits"] += 1
        result = EvalResult(key, pairs, STATUS_FAILED, None, None, (), cone, disk, -1)
        sctx.cache[key] = result
        return result
    if any(row.c <= 0 for row in cone):
        sctx.counters["outside_domain"] += 1
        result = EvalResult(key, pairs, STATUS_OUTSIDE_DOMAIN, None, None, (), cone, None, -1)
        sctx.cache[key] = result
        return result
    if key in sctx.computed_keys:
        sctx.counters["recompute_same_key"] += 1
    sctx.computed_keys.add(key)
    sctx.counters["kernel_calls"] += 1
    sctx.seq += 1
    start = time.perf_counter()
    base = None if parent is None else parent.evaluation
    evaluation, failure, objectives, rows, status = None, None, None, (), STATUS_FAILED
    try:
        evaluation = size_and_seal(sctx.dc, dict(pairs), parent=base)
    except CANDIDATE_FAILURE_CLASSES as exc:
        failure = exc.record
    unmeasured, bundle = (), None
    if evaluation is not None:
        status = seal_status(evaluation)
        if status == STATUS_SEALED:
            # 봉인 점: ss_dev -> metrics_ss -> metrics_dc(metrics CONTRACT 7.6). lineage(ss 필드를 담은 DcEvaluation)를 이 점의
            # evaluation 으로 둔다 -- 다음 평가의 parent 가 그 필드를 재사용한다.
            try:
                ssev = ss_evaluate(evaluation.sealed, sctx.dc, pairs, sctx.ss_constraints, (), junction=sctx.junction,
                                area_decl=sctx.area_decl)
                evaluation, bundle = ssev.lineage, ssev.ss
            except CANDIDATE_FAILURE_CLASSES as exc:
                evaluation, failure, status = None, exc.record, STATUS_FAILED
        else:
            # 수동소자 값 = spec 값 ∪ θ 저항·커패시터·ss 저항(DEC-92) -- ss_evaluate 와 같은 규칙. 영점 상쇄 구조 규칙 저항(1/Σgm)은
            # ss_dev(봉인 점 전용)가 있어야 정해져 봉인 아닌 점에서는 값 없음(passive_value_missing -- 면적 단위 선언이 없어 면적 값은 같다)
            values = sctx.spec_passive_values + tuple((k[1], v) for k, v in pairs if k[0] in _THETA_PASSIVES)
            snap = metrics_dc(evaluation.snapshot, tuple(sorted(values)), (), sctx.area_decl)
            evaluation = DcEvaluation(snap, evaluation.report, evaluation.sealed)
    if evaluation is not None:
        objectives = objective_values(evaluation.snapshot)
        if objectives.power_resolution_w is None:
            status = STATUS_UNDEFINED          # 전력 축 분해능 b_P 를 정할 tol 행이 없다 -- 목적 정규화 불가
        if status != STATUS_UNDEFINED:
            seal_rows, _undefined = constraint_rows(evaluation.snapshot, sctx.dc.lut, sctx.domain.w_min_m,
                                                    sctx.domain.grid_m)
            ss_rows, unmeasured = ss_constraint_rows(bundle, sctx.ss_constraints)
            rows = seal_rows + _spec_rows(sctx, objectives) + ss_rows
    sctx.eval_times.append(time.perf_counter() - start)
    if sctx.eval_budget is None and len(sctx.eval_times) > len(sctx.domain.variables):
        # E_B 를 한 번 정한다: 평가 한 sweep(n + 1 = FD Jacobian 한 번) 뒤의 시간 중앙값 t_ref -- 첫 평가의 LUT 파생표(tol_V) 1회
        # 비용이 중앙값을 끌지 않게. 이후 모든 한도는 평가 수(결정론). 값·근거는 기록되고 settings.eval_budget 으로 재현한다.
        sctx.eval_budget = int(sctx.settings.front_budget_s / statistics.median(sctx.eval_times))
        sctx.eval_budget_source = "derived_once:floor(B/median_t_eval)@n_evals=" + str(len(sctx.eval_times))
    result = EvalResult(key, pairs, status, evaluation, objectives, rows, cone, failure, sctx.seq, unmeasured)
    sctx.cache[key] = result
    _record(sctx, result, origin)
    return result
