"""metric 레지스트리 -- 이름 -> (서명, 값 묶음 형식, 필드) 정본 (설계 design_mod1_lut_mod5_mna 3.4 공통 행, 계획 DEC-53·DEC-68, DF-30).

진입점: `metric_registry`.

metric 하나 = 이미 한 번 계산된 값 묶음(`LoopAnalysis`·`OutputResistance`·`SupplyCurrents`·`AreaSearch`)의 필드 하나다.
값을 다시 계산하는 함수가 아니라 필드를 가리키므로 같은 응답을 여러 metric 이 공유한다. 회로 이름 키·2단 레지스트리 없음
(옛 `_METRICS_REGISTRY` 의 회로 이름 4개 폐기). 이름의 단위 접미사와 서명 단위가 같아야 한다(DEC-68) -- 접미사가 없는
`supply_current_dc` 는 설계 3.4·spec 설계 objective 표의 이름을 그대로 쓴 예외다(접미사 문제는 CONTRACT 열린 항목).

* view_kind: `transfer`(선언 전달 뷰), `loop`(β 루프 -- 되먹임 수동소자 없으면 β = 1, N3.8 PM), `output_port`(출력 포트
  전류 주입 열). DC·면적 metric 은 None.
* objective_axis: `supply_current_dc` = `power`(DEC-77·78). 면적 판정 축 `area_layout_m2`(MOD7 이후)는 아직 없고,
  탐색 축 `area_search_m2` 는 예산 대상이 아니므로 None.
"""
import dataclasses
import types

from gmid_engine.core import MetricSignature

from .mna_types import AreaSearch, LoopAnalysis, OutputResistance, SupplyCurrents


@dataclasses.dataclass(frozen=True)
class RegisteredMetric:
    """레지스트리 항목: 서명, 값을 담는 결과 형식, 그 형식의 필드 이름."""

    signature: MetricSignature
    source_type: type
    field: str


_ROWS = (
    ("gain_ss_db", "db", "ss", "transfer", None, LoopAnalysis),
    ("ugf_ss_hz", "hz", "ss", "transfer", None, LoopAnalysis),
    ("gbw_ss_hz", "hz", "ss", "transfer", None, LoopAnalysis),
    ("pm_ss_deg", "deg", "ss", "loop", None, LoopAnalysis),
    ("rout_ss_ohm", "ohm", "ss", "output_port", None, OutputResistance),
    ("supply_current_dc", "amp", "dc", None, "power", SupplyCurrents),
    ("power_dc_w", "w", "dc", None, None, SupplyCurrents),
    ("area_search_m2", "m2", "dc", None, None, AreaSearch),
)


def _build():
    table = {}
    for name, unit, domain, view_kind, axis, source_type in _ROWS:
        if name in table:
            raise ValueError("metric 이름 %r 중복" % name)
        if name not in {f.name for f in dataclasses.fields(source_type)}:
            raise ValueError("metric %r 의 필드가 %s 에 없다" % (name, source_type.__name__))
        table[name] = RegisteredMetric(MetricSignature(unit, domain, view_kind, axis), source_type, name)
    return types.MappingProxyType(dict(sorted(table.items())))


_REGISTRY = _build()


def metric_registry():
    """읽기 전용 매핑 {metric 이름: RegisteredMetric}(이름 정렬)."""
    return _REGISTRY
