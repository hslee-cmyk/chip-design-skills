"""metric 서명 -- 데이터 선언 모듈 (설계 design_spec_format 3.2 `metric_catalog`, design_mod1_lut_mod5_mna 3.4 공통 행).

공개 정의는 frozen dataclass `MetricSignature` 뿐이다. MOD2 spec 로더(metric 이름 검사)와 MOD5 metric 레지스트리가
함께 쓰므로 core 에 둔다. 이름표(어떤 metric 이 있는가)는 여기 두지 않는다 -- 정본은 MOD5 레지스트리 하나다.
"""
import dataclasses

from .units import DOMAINS, METRIC_UNITS


@dataclasses.dataclass(frozen=True)
class MetricSignature:
    """metric 하나의 서명.

    * `unit`: 정규 단위(`core.units.METRIC_UNITS` 원소, metric 이름 접미사와 같은 어휘 -- DEC-68).
    * `domain`: 영역(`core.units.DOMAINS` 원소, DEC-67).
    * `view_kind`: 필요한 뷰 종류 문자열, 뷰가 필요 없으면 None(spec 로더가 `view` 요구 여부를 여기서 읽는다).
    * `objective_axis`: 예산을 걸 수 있는 목적 축 이름(DEC-77), 목적 축이 아니면 None.
    """

    unit: str
    domain: str
    view_kind: object = None
    objective_axis: object = None

    def __post_init__(self):
        if self.unit not in METRIC_UNITS:
            raise ValueError("MetricSignature.unit %r 은 core.units.METRIC_UNITS 밖이다" % (self.unit,))
        if self.domain not in DOMAINS:
            raise ValueError("MetricSignature.domain %r 은 core.units.DOMAINS 밖이다" % (self.domain,))
        for field in ("view_kind", "objective_axis"):
            value = getattr(self, field)
            if value is not None and (not isinstance(value, str) or not value):
                raise TypeError("MetricSignature.%s 는 None 또는 비어 있지 않은 문자열이어야 한다" % field)
