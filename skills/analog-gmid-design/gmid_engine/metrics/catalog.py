"""metric 카탈로그 -- spec 로더 주입용 {이름: MetricSignature} (설계 design_spec_format 3.2 `metric_catalog`).

진입점: `metric_catalog`.

MOD2 spec 로더는 MOD5 를 import 할 수 없으므로(층 방향) MOD10 파이프라인이 이 함수의 결과를 `load_sizing_spec` 의
`metric_catalog` 인자로 넘긴다. 정본은 `metric_registry` 하나이고 여기서는 서명만 투영한다.

[U5] 계산 대기 서명(`pending_metrics.PENDING_METRIC_ROWS`)을 더한다: offset·미러비·스윙·ICMR(설계 40 §3.8-8)과 잡음(41 §7.1) 이름은
spec 이 제약으로 선언할 수 있지만 레지스트리(=계산 가능)에는 아직 없다. 카탈로그에는 있고 레지스트리에 없는 이름이 계산 대기다
(탐색 문맥이 이를 `constraint_notes` 의 `unmeasured`/`metric_computation_pending` 으로 기록한다 -- 보고에 드러난다). 레지스트리 이름과 겹치면 `ValueError`.
"""
import types

from gmid_engine.core import MetricSignature

from .pending_metrics import PENDING_METRIC_ROWS
from .registry import metric_registry


def metric_catalog():
    """읽기 전용 매핑 {metric 이름: MetricSignature}(이름 정렬) -- 레지스트리 서명 + 계산 대기 서명."""
    table = {name: entry.signature for name, entry in metric_registry().items()}
    for name, unit, domain, view_kind, axis in PENDING_METRIC_ROWS:
        if name in table:
            raise ValueError("계산 대기 metric %r 가 레지스트리에도 있다(구현 단위가 대기 표에서 지워야 한다)" % name)
        table[name] = MetricSignature(unit, domain, view_kind, axis)
    return types.MappingProxyType(dict(sorted(table.items())))
