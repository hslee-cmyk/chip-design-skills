"""오라클 대조 모델 오차 읽기 -- `derived.model_error_<metric>` -> ((metric, 값), ...) (설계 40 §3.8-6, DEC-72, 체크리스트 D-GB8c).

진입점: `model_error_pairs(derived) -> ((metric, 크기), ...)`.

`derived` = 오라클 대조 결과가 쓴 {키: 값} 매핑(또는 ((키, 값), ...)) -- 키 `model_error_<metric>`(`verified_by.VerifiedBy.model_error_ref`)만 읽는다. metric 은 레지스트리에 있어야 하고(없으면 `KeyError` --
이름을 지어내지 않는다) 값은 유한 비음수 수다(오차의 크기, 그 metric 과 같은 단위). 부호가 있으면 크기를 쓴다. 결과는 metric 이름순이고 `ss_constraint_rows` 의
분해능 바닥(NFR-5)과 `find_front` 의 '모델 오차 미측정' 판정 보류 해제 조건이 읽는다(`build_search_context(model_error=)`).
"""
import math

from .registry import metric_registry
from .verified_by import MODEL_ERROR_PREFIX


def model_error_pairs(derived):
    registry = metric_registry()
    found = {}
    for key, value in dict(derived).items():
        if not isinstance(key, str) or not key.startswith(MODEL_ERROR_PREFIX):
            continue
        metric = key[len(MODEL_ERROR_PREFIX):]
        if metric not in registry:
            raise KeyError("model_error_pairs: 레지스트리에 없는 metric %r (키 %r)" % (metric, key))
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise TypeError("model_error_pairs: %r 는 유한 수여야 한다: %r" % (key, value))
        found[metric] = abs(float(value))
    return tuple(sorted(found.items()))
