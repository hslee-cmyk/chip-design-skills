"""metric 서명 -- 데이터 선언 모듈 (설계 design_spec_format 3.2 `metric_catalog`, design_mod1_lut_mod5_mna 3.4 공통 행).

공개 정의는 frozen dataclass `MetricSignature` 와 그 닫힌 어휘 상수 `VIEW_KINDS`·`OBJECTIVE_AXES` 다(규칙 A 데이터 선언
모듈). 단위·영역 어휘는 `core.units`(`METRIC_UNITS`·`DOMAINS`) 한 곳이 정본이다.

* MOD2(authoring)는 MOD5(metric 레지스트리)를 import 할 수 없다(계획 N3.10, 작은 층 쪽으로만). 그래서 spec 로더는
  `{metric 이름: MetricSignature}` 불변 매핑을 **인자로 주입**받는다. 이 데이터 클래스는 두 쪽이 함께 쓰므로 core 에 둔다.
* 이름표(어떤 metric 이 있는가)는 여기 두지 않는다 -- 정본은 MOD5 레지스트리 하나다(개념 하나 저장 위치 하나, DEC-68).
"""
import dataclasses

from .units import DOMAINS, METRIC_UNITS

# 뷰 종류 어휘(MOD5 레지스트리 어휘의 정본, 이 한 곳). 뷰를 쓰지 않는 metric 은 문자열이 아니라 None 이다.
#   transfer    -- 선언 전달 뷰 하나(ac_excite -> sense)
#   loop        -- β 루프(선언 되먹임 수동소자, 없으면 β = 1 -- 계획 N3.8 PM)
#   cm_loop     -- 공통 모드 루프: 선언된 차동 출력 포트 쌍에 동일 부호 Middlebrook 주입(되먹임 선언 없음, 입력 교류접지)
#   output_port -- 출력 포트 전류 주입 열(여기원 전부 교류접지)
#   ratio       -- 같은 계의 num·den 두 여기 열
VIEW_KINDS = ("transfer", "loop", "cm_loop", "output_port", "ratio")

# 예산을 걸 수 있는 목적 축(DEC-77) -- spec `objective.budgets` 키로 쓸 수 있는 metric.
OBJECTIVE_AXES = ("power", "area")


@dataclasses.dataclass(frozen=True)
class MetricSignature:
    """metric 하나의 서명. 어휘 밖 값이면 `ValueError`(주입하는 쪽의 프로그램 오류).

    * `unit`: 정규 단위(`core.units.METRIC_UNITS` 원소, metric 이름 접미사와 같은 어휘 -- DEC-68).
    * `domain`: 영역(`core.units.DOMAINS` 원소, DEC-67).
    * `view_kind`: None(뷰를 쓰지 않는 metric) 또는 `VIEW_KINDS` 원소(spec 로더가 `view` 요구 여부·모양을 여기서 읽는다).
    * `objective_axis`: None(목적 축 아님) 또는 `OBJECTIVE_AXES` 원소(DEC-77).
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
        if self.view_kind is not None and self.view_kind not in VIEW_KINDS:
            raise ValueError("MetricSignature.view_kind %r 은 None 또는 %r 중 하나여야 한다" % (self.view_kind, VIEW_KINDS))
        if self.objective_axis is not None and self.objective_axis not in OBJECTIVE_AXES:
            raise ValueError("MetricSignature.objective_axis %r 은 None 또는 %r 중 하나여야 한다"
                             % (self.objective_axis, OBJECTIVE_AXES))
