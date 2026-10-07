"""metric 값 읽기 (설계 design_mod1_lut_mod5_mna 3.4 공통 행 -- metric 은 이미 계산된 값 묶음의 필드).

진입점: `metric_value`.

이름으로 레지스트리 항목을 찾아 결과 묶음 형식을 확인하고 필드를 읽는다. 미등록 이름은 KeyError(평가 시점 거부가
아니라 spec 로드에서 `metric_unknown` 으로 먼저 걸린다 -- 여기 닿으면 배선 결함). 값이 정의되지 않은 metric
(None, 묶음의 `undefined` 에 사유)은 `StructureUnresolvedError`(detail: metric, reason).
"""
from gmid_engine.core import StructureUnresolvedError

from .registry import metric_registry


def metric_value(name, source):
    """metric 이름, 결과 묶음 -> float."""
    entry = metric_registry()[name]
    if not isinstance(source, entry.source_type):
        raise TypeError(
            "metric %r 는 %s 에서 읽는다 -- 받은 것: %s" % (name, entry.source_type.__name__, type(source).__name__)
        )
    value = getattr(source, entry.field)
    if value is None:
        reason = next((r for m, r in source.undefined if m == name), None)
        raise StructureUnresolvedError(detail={"reason": "metric_undefined", "metric": name, "cause": reason})
    return value
