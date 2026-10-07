"""metric 카탈로그 -- spec 로더 주입용 {이름: MetricSignature} (설계 design_spec_format 3.2 `metric_catalog`).

진입점: `metric_catalog`.

MOD2 spec 로더는 MOD5 를 import 할 수 없으므로(층 방향) MOD10 파이프라인이 이 함수의 결과를 `load_sizing_spec` 의
`metric_catalog` 인자로 넘긴다. 정본은 `metric_registry` 하나이고 여기서는 서명만 투영한다.
"""
import types

from .registry import metric_registry


def metric_catalog():
    """읽기 전용 매핑 {metric 이름: MetricSignature}(이름 정렬)."""
    return types.MappingProxyType({name: entry.signature for name, entry in metric_registry().items()})
