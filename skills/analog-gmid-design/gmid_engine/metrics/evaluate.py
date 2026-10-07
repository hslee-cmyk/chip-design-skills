"""metric 값 읽기 (설계 design_mod1_lut_mod5_mna 3.4 공통 행 -- metric 은 이미 계산된 값 묶음의 필드).

진입점: `metric_value`.

이름으로 레지스트리 항목을 찾아 결과 묶음 형식을 확인하고 필드를 읽어 `MetricResult` 로 낸다. 값이 정의되지 않으면
(None) 예외 없이 `MetricResult(value=None, undefined=그 필드의 사유들)` -- 판정 계층이 문맥(탐색 전 구조 판정 →
STRUCTURE_UNRESOLVED / 탐색 중 평가 → N3.14 후보 실패)으로 분류한다(coordinator 결정 2026-10-07 M3).
미등록 이름(KeyError)·형식 불일치(TypeError)는 배선 결함이라 예외다(spec 로드의 `metric_unknown` 이 먼저 거른다).
"""
from .mna_types import MetricResult, Undefined
from .registry import metric_registry


def metric_value(name, source):
    """metric 이름, 결과 묶음 -> `MetricResult`."""
    entry = metric_registry()[name]
    if not isinstance(source, entry.source_type):
        raise TypeError(
            "metric %r 는 %s 에서 읽는다 -- 받은 것: %s" % (name, entry.source_type.__name__, type(source).__name__)
        )
    value = getattr(source, entry.field)
    if value is not None:
        return MetricResult(name=name, value=value)
    causes = tuple(u for u in source.undefined if u.quantity == entry.field)
    if not causes:
        causes = (Undefined(entry.field, "unrecorded_cause", "numeric"),)
    return MetricResult(name=name, value=None, undefined=causes)
