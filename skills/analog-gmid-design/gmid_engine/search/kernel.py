"""평가 커널 조립 -- θ 하나 -> GB7 DC 정본 + 봉인 + 목적 + 제약, 캐시·S3 (설계 design_mod6_search_front 2.2·2.3·7절).

진입점: `evaluate(sctx, theta, cells, parent=None, origin=(), geometry=None) -> EvalResult`.

* `theta` = {(kind, key): 값} 또는 쌍 iterable(스키마 전 성분), `cells` = L 칸 index 벡터(MOS 이름순), `parent` = 같은
  컨텍스트의 이전 EvalResult(그 `evaluation` 스냅샷을 sizing 이 재사용 -- 바뀐 성분을 읽는 블록만 다시 계산, 필드가 곧 캐시),
  `origin` = S3 기록용 ((키, 값), ...)(단계·ε·시작점 -- 키 밖).
* [U14] `geometry` = `RealizedGeometry`(MOD8 재검증, LY7·LY8) -- 레이아웃 뒤 실현 기하로 평가한다: 고정 W(`w_request`)·실현 폭 슬라이스(`w_keys`, 이 평가의
  `LutAccess`)·실현 확산 기하(`diffusion`, 접합 용량)를 쓴다. 키의 `w_fixed_fp` = 기하 지문(없으면 None), 나머지 흐름은 같다 -- 같은 (θ, 기하)는
  캐시 적중이고 기하가 다르면 다른 점이다. 슬라이스를 바꿔도 base writer(`ctx.base.block_versions`)의 block_version 은 그대로라 `parent` 를 쓸 수 있다.
* 순서: 요청 계수 -> 키(`eval_key`) -> 메모리 캐시(그 실행에서 평가한 성공·실패) 적중이면 그대로(커널 0) -> 원뿔 행(`cone_rows`)에 c ≤ 0 이 있으면 `STATUS_OUTSIDE_DOMAIN`(커널 0, 정의역 밖) -> `size_and_seal`.
* 후보 실패는 `CANDIDATE_FAILURE_CLASSES` 만 이름으로 잡아 `STATUS_FAILED` + FailureRecord(N3.14) + 부분 스냅샷(`EvalResult.partial` = 예외의 `partial`, 실패 직전까지
  쓴 스냅샷 -- S3 evals 실패 줄 `snapshot_fp` = `partial.fp`). ValueError·TypeError 등은 호출 계약 위반이라 잡지 않는다(넓은 except 없음).
* 블록 호출(`passive_values`·`metrics_dc`)은 `dc`(`KernelContext`)의 색인·계수로 부른다 -- 같은 입력은 계보와 무관하게 이식·재연된다.
* 성공: `seal_status`(봉인 7 대기 스위치) -> 목적(`objective_values`, 점의 b_P 포함 -- None 이면 `STATUS_UNDEFINED`) ->
  제약(`constraint_rows` + 목적 축 spec 제약(전력 분모 = 그 점의 b_P) + `ss_constraint_rows`, 재지 못한 ss 제약은 `unmeasured`).
* E_B(평가 수 예산)가 선언되지 않았으면 평가 수가 n + 1 을 넘는 순간 한 번 ⌊B / median(평가 시간)⌋ 로 정한다(기록).
* 커널을 부른 평가만 S3 evals 에 한 줄(설계 8절). 같은 키를 두 번 계산하면 `recompute_same_key` +1(정상 0).
"""
import dataclasses
import statistics
import time
from collections.abc import Mapping

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, fp_of
from gmid_engine.metrics import REPORT_BLOCK_RESIDUAL, metrics_dc, passive_values, ss_evaluate, theta_passive_pairs
from gmid_engine.sizing import KERNEL_KEY, METRICS_KEY, DcEvaluation, LutAccess, size_and_seal

from .cone_rows import cone_rows
from .constraints import constraint_rows
from .eval_budget import EvalBudget
from .eval_key import eval_key
from .ls_constraints import ls_constraint_rows
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

def _spec_rows(sctx, objectives):
    rows = []
    scale = {AXIS_POWER: objectives.power_resolution_w, AXIS_AREA: sctx.domain.area_resolution_m2}
    value = {AXIS_POWER: objectives.power_w, AXIS_AREA: objectives.area_m2}
    for metric, op, target in sctx.judged_constraints:
        c = (value[metric] - target) / scale[metric] if op == ">=" else (target - value[metric]) / scale[metric]
        rows.append(ConstraintRow("spec:" + metric + op, c, c <= 1))
    return tuple(rows)


def _block_residual_rows(snapshot):
    """S3 evals 요약 -- 그 점의 블록 분해 잔차 보고(41 §2.2: `gain_residual_db`·`ss.block_gain`·`ss.ff_contrib`·`ss.rout_residual_ohm`). `metrics_aux` 가 안 돈 점은 빈 목록."""
    try:
        bundle = snapshot.value("graph", METRICS_KEY, "metrics_aux")
    except KeyError:
        return []
    return [[list(kv) for kv in rep] for name, rep in bundle.reports if name == REPORT_BLOCK_RESIDUAL]


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
        residual_rows = _block_residual_rows(result.evaluation.snapshot)
        if residual_rows:
            rec["block_residual"] = residual_rows
    elif result.partial is not None:
        rec["snapshot_fp"] = result.partial.fp      # 후보 실패 줄도 부분 스냅샷 지문을 남긴다(사용자 결정 X-3·X-10)
    sctx.archive.append_eval(rec)


def evaluate(sctx, theta, cells, parent=None, origin=(), geometry=None):
    sctx.counters["requests"] += 1
    dc = sctx.dc if geometry is None else dataclasses.replace(sctx.dc, lut=LutAccess(sctx.dc.lut.memo, geometry.w_keys))
    theta = expand_ties(sctx.domain.ties, theta if isinstance(theta, Mapping) else dict(theta),
                         sctx.domain.negated, sctx.domain.zeros)    # [r12] 묶인 성분은 대표 값
    pairs = tuple(sorted(theta.items()))
    key = eval_key(sctx.context_fp, sctx.schema_fp, pairs, cells, None if geometry is None else fp_of(geometry))
    hit = sctx.cache.get(key)
    if hit is not None:
        sctx.counters["hits"] += 1
        if hit.status == STATUS_FAILED:
            sctx.counters["fail_hits"] += 1
        return hit
    schema = dc.base.value("graph", KERNEL_KEY, "theta_schema")       # S0 수준 필드(설계 40 §2.4.7)
    cone = cone_rows(schema, pairs)
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
    memo = dc.lut.memo
    if memo.bound_state == "counting":
        memo.open_count()        # 그 컨텍스트의 첫 커널 평가 -- LUT memo 상한을 재는 창 열기(설계 40 §2.4.6). 생성자 memo("fixed")는 부르지 않는다
    start = time.perf_counter()
    base = None if parent is None else parent.evaluation
    evaluation, failure, partial, objectives, rows, status = None, None, None, None, (), STATUS_FAILED
    try:
        evaluation = size_and_seal(dc, dict(pairs), parent=base, w_request=() if geometry is None else geometry.w_request)
    except CANDIDATE_FAILURE_CLASSES as exc:
        failure, partial = exc.record, exc.partial
    unmeasured, bundle = (), None
    if evaluation is not None:
        status = seal_status(evaluation)
        if status == STATUS_SEALED:
            # 봉인 점: ss_dev -> metrics_ss -> metrics_dc(metrics CONTRACT 7.6). lineage(ss 필드를 담은 DcEvaluation)를 이 점의
            # evaluation 으로 둔다 -- 다음 평가의 parent 가 그 필드를 재사용한다.
            try:
                ssev = ss_evaluate(evaluation.sealed, dc, pairs, sctx.ss_constraints, (), junction=sctx.junction,
                                   area_decl=sctx.area_decl, noise_decl=sctx.noise_decl, mismatch=sctx.mismatch, structure=sctx.structure,
                                   driving=sctx.driving, diffusion=() if geometry is None else geometry.diffusion)
                evaluation, bundle = ssev.lineage, ssev.ss
            except CANDIDATE_FAILURE_CLASSES as exc:
                evaluation, failure, partial, status = None, exc.record, exc.partial, STATUS_FAILED
        else:
            # 봉인 아닌 점도 수동소자 값 필드는 같은 GB5 블록이 쓴다(영점 상쇄 R = 1/Σdc_gm 은 dc 단계 필드라 봉인 전에도 정의, 설계 40 §2.4.7)
            snap = passive_values(evaluation.snapshot, dc.inputs.element_values, schema.zero_cancel, theta_passive_pairs(pairs),
                                  donors=dc.donors, counters=dc.counters)
            snap = metrics_dc(snap, (), sctx.area_decl, donors=dc.donors, counters=dc.counters)
            evaluation = DcEvaluation(snap, evaluation.report, evaluation.sealed)
    if evaluation is not None:
        objectives = objective_values(evaluation.snapshot)
        if objectives.power_resolution_w is None:
            status = STATUS_UNDEFINED          # 전력 축 분해능 b_P 를 정할 tol 행이 없다 -- 목적 정규화 불가
        if status != STATUS_UNDEFINED:
            seal_rows, _undefined = constraint_rows(evaluation.snapshot, dc.lut, sctx.domain.w_min_m,
                                                    sctx.domain.grid_m)
            ss_rows, unmeasured = ss_constraint_rows(bundle, sctx.ss_constraints, sctx.model_error)
            ls_rows, ls_unmeasured = ls_constraint_rows(bundle, sctx.driving)
            unmeasured = unmeasured + ls_unmeasured
            rows = seal_rows + _spec_rows(sctx, objectives) + ss_rows + ls_rows
    sctx.eval_times.append(time.perf_counter() - start)
    if sctx.eval_budget is None and len(sctx.eval_times) > len(sctx.domain.variables):
        # E_B 를 한 번 정한다: 평가 한 sweep(n + 1 = FD Jacobian 한 번) 뒤의 시간 중앙값 t_ref -- 첫 평가의 LUT 파생표(tol_V) 1회
        # 비용이 중앙값을 끌지 않게. 이후 모든 한도는 평가 수(결정론). 값·근거는 기록되고 settings.eval_budget 으로 재현한다.
        sctx.eval_budget = EvalBudget(sctx.settings.front_budget_s, sctx.eval_times).limit()
        if sctx.eval_budget is not None:
            sctx.eval_budget_source = "derived_once:floor(B/median_t_eval)@n_evals=" + str(len(sctx.eval_times))
    result = EvalResult(key, pairs, status, evaluation, objectives, rows, cone, failure, sctx.seq, unmeasured,
                        () if bundle is None else bundle.warnings, partial)
    if memo.bound_state == "window_open":
        memo.fix_bound()         # 결과를 만든 직후(성공·후보 실패 모두) 창 닫기 + 상한 (n_θ + 1)·U_eval 고정
    sctx.cache[key] = result
    _record(sctx, result, origin)
    return result
