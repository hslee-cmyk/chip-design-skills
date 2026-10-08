"""spec 성능 제약(ss 영역) 행 -- MOD5 `ss_evaluate` 결과 묶음에서 (설계 5절 'metric 선언' 행, DEC-67·72·74, NFR-5, 오케스트레이터
결정 2026-10-08 S-1 배선·S-19 분해능).

진입점: `ss_constraint_rows(bundle, declared, model_error=()) -> (rows, unmeasured)`.

* `declared` = spec `ConstraintDecl` tuple(`build_search_context` 가 고른 것: 판정 대상·값 있음·목적 축 밖·metric 레지스트리에서
  view_kind 가 있는 metric). `bundle` = 그 점의 `graph.metrics_ss` `MetricBundle`(`ss_evaluate(...).ss`), 봉인 안 된 점은 None.
  `model_error` = ((metric, 값), ...) DEC-72 모델 오차 선언(`value_from_model_error` -- 아직 선언이 없어 부르는 쪽은 ()).
* 봉인 안 된 점(None): 행 없음, 선언마다 (metric, op, "ss_requires_sealed_snapshot") -- ss 는 SealedSnapshot 에서만(DEC-67).
* 봉인 점: 선언 k(선언 순서 0 부터)마다 요청 `MetricRequest(metric, view)` 의 결과.
  - [CM] view_kind `cm_loop` metric 의 PM 이 `dc_not_above_level`(|T_cm(0)| ≤ 1, CMFB 무효)로 None 이면 **위반 행**: c = 20·log10|T_cm(0)|/s
    < 0 (s = 이득 dB 분해능, 없으면 1 dB), active True. 개루프 RHP 극점 등 다른 사유는 아래 unmeasured 그대로.
  - 값 None(Undefined): 행 없이 `unmeasured` 에 (metric, op, Undefined code 집합을 정렬해 '+' 로 이음, 없으면 "undefined").
  - [r6 S-19] 분해능 s = 결과 `MetricResult.resolution`(metrics 9절: LUT tol_V 1차 전파와 MNA 사후 오차 중 큰 값). resolution 이
    None 이면 행 없이 unmeasured(사유 "resolution_undefined"). resolution 이 0 이면 s = 그 metric 의 모델 오차(선언 시); 선언이
    없으면 0 으로 나누지 않고 unmeasured(사유 "resolution_zero_model_error_undeclared"). resolution > 0 이고 모델 오차 선언이 있으면
    s = max(둘)(NFR-5 바닥).
  - 행 `ss:<k>:<metric><op>`, c = (값 − 목표)/s(>=) 또는 (목표 − 값)/s(<=), `active` = c ≤ 1(여유가 분해능 한 칸 이하).
"""
import math

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE
from gmid_engine.metrics import MetricRequest, metric_registry

from .search_values import ConstraintRow

_NOT_SEALED = "ss_requires_sealed_snapshot"
_RES_NONE = "resolution_undefined"
_RES_ZERO = "resolution_zero_model_error_undeclared"
_CM_KIND = "cm_loop"                  # 구조 유도 CM 루프 뷰의 view_kind (core VIEW_KINDS)
_LEVEL_CODE = "dc_not_above_level"    # |T(0)| ≤ 1 -- 교차·PM 없음
_MAGNITUDE_KEY = "dc_magnitude"       # 그 사유 detail 의 |T(0)|


def _cm_level_violation(d, res, k):
    """[CM] 공통 모드 루프(view_kind cm_loop) PM 이 |T_cm(0)| ≤ 1 이라 정의 불가면 CMFB 무효 = 제약 **위반** 행.
    c = 20·log10|T_cm(0)| / s (dB, 0 dB 기준 -- 새 상수 없음; T(0) < 1 이면 c < 0), s = 이득 dB 분해능(`MetricResult.resolution`),
    없거나 0 이면 dB 그대로(s = 1 은 단위 환산이지 상수 선택이 아니다 -- dB 가 c 의 단위). |T_cm(0)| = 0 이면 c = −∞.
    값이 아닌 사유(개루프 RHP 극점 등)는 해당 없음 -> None (기존 unmeasured). 임계값 d.value 는 쓰지 않는다(CMFB 무효는 PM 크기와 무관)."""
    if metric_registry()[d.metric].signature.view_kind != _CM_KIND:
        return None
    hit = next((u for u in res.undefined if u.code == _LEVEL_CODE), None)
    if hit is None:
        return None
    mag = dict(hit.detail).get(_MAGNITUDE_KEY)
    if mag is None:
        return None
    scale = res.resolution if res.resolution and res.resolution > 0 else 1.0
    c = -math.inf if not mag > 0 else AMPLITUDE_DB_PER_DECADE * math.log10(mag) / scale
    return ConstraintRow("ss:" + str(k) + ":" + d.metric + d.op, float(c), True)


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
            violation = _cm_level_violation(d, res, k)
            if violation is not None:
                rows.append(violation)
                continue
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
