"""metric 레지스트리 -- 이름 -> (서명, 값 묶음 형식, 필드) 정본 (설계 design_mod1_lut_mod5_mna 3.4 공통 행, 계획 DEC-53·DEC-68, DF-30).

진입점: `metric_registry`.

metric 하나 = 이미 한 번 계산된 값 묶음(`LoopAnalysis`·`OutputResistance`·`ResponseRatio`·`SupplyCurrents`·`AreaSearch`)의
필드 하나다. 값을 다시 계산하는 함수가 아니라 필드를 가리키므로 같은 응답을 여러 metric 이 공유한다(`pm_ss_deg` 와
`parasitic_pm_ss_deg` 는 같은 필드 `phase_margin_deg` 를 서로 다른 뷰의 묶음에서 읽는다). 회로 이름 키·2단 레지스트리 없음
(옛 `_METRICS_REGISTRY` 의 회로 이름 4개 폐기). 이름의 단위 접미사와 서명 단위가 같아야 한다(DEC-68) -- 접미사가 없는
`supply_current_dc` 는 설계 3.4·spec 설계 objective 표의 이름을 그대로 쓴 예외다(접미사 문제는 CONTRACT 열린 항목).

* view_kind: `transfer`(선언 전달 뷰), `loop`(β 루프 -- 되먹임 수동소자 없으면 β = 1, N3.8 PM), `cm_loop`(공통 모드 루프 -- 차동 출력 포트 쌍 동일 부호 주입, `pm_cm_ss_deg`), `output_port`(출력 포트
  전류 주입 열), `ratio`(같은 계의 num·den 두 여기 열). DC·면적 metric 은 None(뷰 없음). 어휘 정본은
  `core.metric_signature.VIEW_KINDS`.
* domain: 면적 `area_search_m2` 는 레이아웃 기하 `geom`(DM 3.4 영역 열).
* objective_axis: `supply_current_dc` = `power`(DEC-77·78). 면적 판정 축 `area_layout_m2`(MOD7 이후)는 아직 없고,
  탐색 축 `area_search_m2` 는 예산 대상이 아니므로 None.
"""
import dataclasses
import types

from gmid_engine.core import MetricSignature

from .mna_types import AreaSearch, LoopAnalysis, OutputResistance, ResponseRatio, SupplyCurrents


@dataclasses.dataclass(frozen=True)
class RegisteredMetric:
    """레지스트리 항목: 서명, 값을 담는 결과 형식, 그 형식의 필드 이름."""

    signature: MetricSignature
    source_type: type
    field: str


_ROWS = (
    # (metric 이름, 단위, 영역, view_kind, objective_axis, 결과 형식, 필드)
    ("gain_ss_db", "db", "ss", "transfer", None, LoopAnalysis, "gain_db"),
    ("ugf_ss_hz", "hz", "ss", "transfer", None, LoopAnalysis, "ugf_hz"),
    ("gbw_ss_hz", "hz", "ss", "transfer", None, LoopAnalysis, "gbw_hz"),
    ("parasitic_pm_ss_deg", "deg", "ss", "transfer", None, LoopAnalysis, "phase_margin_deg"),
    ("pm_ss_deg", "deg", "ss", "loop", None, LoopAnalysis, "phase_margin_deg"),
    ("pm_cm_ss_deg", "deg", "ss", "cm_loop", None, LoopAnalysis, "phase_margin_deg"),
    ("ratio_ss_db", "db", "ss", "ratio", None, ResponseRatio, "ratio_db"),
    ("rout_ss_ohm", "ohm", "ss", "output_port", None, OutputResistance, "rout_ohm"),
    ("supply_current_dc", "amp", "dc", None, "power", SupplyCurrents, "supply_current_dc"),
    ("power_dc_w", "w", "dc", None, None, SupplyCurrents, "power_dc_w"),
    ("area_search_m2", "m2", "geom", None, None, AreaSearch, "area_search_m2"),
)


def _build():
    table = {}
    for name, unit, domain, view_kind, axis, source_type, field in _ROWS:
        if name in table:
            raise ValueError("metric 이름 %r 중복" % name)
        if field not in {f.name for f in dataclasses.fields(source_type)}:
            raise ValueError("metric %r 의 필드 %r 가 %s 에 없다" % (name, field, source_type.__name__))
        table[name] = RegisteredMetric(MetricSignature(unit, domain, view_kind, axis), source_type, field)
    return types.MappingProxyType(dict(sorted(table.items())))


_REGISTRY = _build()


def metric_registry():
    """읽기 전용 매핑 {metric 이름: RegisteredMetric}(이름 정렬)."""
    return _REGISTRY
