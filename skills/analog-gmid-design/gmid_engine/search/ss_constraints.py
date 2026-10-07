"""spec 성능 제약(ss 영역) 행 -- MOD5 `ss_evaluate` 결과 묶음에서 (설계 5절 'metric 선언' 행, DEC-67·72·74, NFR-5, 오케스트레이터
결정 2026-10-08 S-1 배선·S-19 분해능).

진입점: `ss_constraint_rows(bundle, declared, model_error=()) -> (rows, unmeasured)`.

* `declared` = spec `ConstraintDecl` tuple(`build_search_context` 가 고른 것: 판정 대상·값 있음·목적 축 밖·metric 레지스트리에서
  view_kind 가 있는 metric). `bundle` = 그 점의 `graph.metrics_ss` `MetricBundle`(`ss_evaluate(...).ss`), 봉인 안 된 점은 None.
  `model_error` = ((metric, 값), ...) DEC-72 모델 오차 선언(`value_from_model_error` -- 아직 선언이 없어 부르는 쪽은 ()).
* 봉인 안 된 점(None): 행 없음, 선언마다 (metric, op, "ss_requires_sealed_snapshot") -- ss 는 SealedSnapshot 에서만(DEC-67).
* 봉인 점: 선언 k(선언 순서 0 부터)마다 요청 `MetricRequest(metric, view)` 의 결과.
  - 값 None(Undefined): 행 없이 `unmeasured` 에 (metric, op, Undefined code 집합을 정렬해 '+' 로 이음, 없으면 "undefined").
  - [r6 S-19] 분해능 s = 결과 `MetricResult.resolution`(metrics 9절: LUT tol_V 1차 전파와 MNA 사후 오차 중 큰 값). resolution 이
    None 이면 행 없이 unmeasured(사유 "resolution_undefined"). resolution 이 0 이면 s = 그 metric 의 모델 오차(선언 시); 선언이
    없으면 0 으로 나누지 않고 unmeasured(사유 "resolution_zero_model_error_undeclared"). resolution > 0 이고 모델 오차 선언이 있으면
    s = max(둘)(NFR-5 바닥).
  - 행 `ss:<k>:<metric><op>`, c = (값 − 목표)/s(>=) 또는 (목표 − 값)/s(<=), `active` = c ≤ 1(여유가 분해능 한 칸 이하).
"""
from gmid_engine.metrics import MetricRequest

from .search_values import ConstraintRow

_NOT_SEALED = "ss_requires_sealed_snapshot"
_RES_NONE = "resolution_undefined"
_RES_ZERO = "resolution_zero_model_error_undeclared"


def ss_constraint_rows(bundle, declared, model_error=()):
    if not declared:
        return (), ()
    if bundle is None:
        return (), tuple((d.metric, d.op, _NOT_SEALED) for d in declared)
    results = dict(bundle.entries)
    errors = dict(model_error)
    rows, unmeasured = [], []
    for k, d in enumerate(declared):
        res = results[MetricRequest(d.metric, d.view)]
        if res.value is None:
            unmeasured.append((d.metric, d.op, "+".join(sorted({u.code for u in res.undefined})) or "undefined"))
            continue
        if res.resolution is None:
            unmeasured.append((d.metric, d.op, _RES_NONE))
            continue
        scale = max(res.resolution, errors.get(d.metric) or 0.0)
        if not scale > 0:
            unmeasured.append((d.metric, d.op, _RES_ZERO))
            continue
        c = (res.value - d.value) / scale if d.op == ">=" else (d.value - res.value) / scale
        rows.append(ConstraintRow("ss:" + str(k) + ":" + d.metric + d.op, float(c), c <= 1))
    return tuple(rows), tuple(unmeasured)
