"""metric 이름표 한 칸의 형식 -- 데이터 선언 모듈 (설계 design_spec_format 3.2, import 방향 해법).

공개 정의는 frozen dataclass `MetricSignature` 하나와 그 닫힌 어휘 상수다(규칙 A 데이터 선언 모듈).

* MOD2(authoring)는 MOD5(metric 레지스트리)를 import 할 수 없다(계획 N3.10, 작은 층 쪽으로만). 그래서 spec 로더는
  `{metric 이름: MetricSignature}` 불변 매핑을 **인자로 주입**받는다. 이 데이터 클래스는 두 쪽이 함께 쓰므로 core 에 둔다.
* 레지스트리(이름표) 정본은 MOD5 하나이고, core 에는 이름을 두지 않는다(개념 하나 저장 위치 하나, DEC-68).
* `unit`: 정규 단위 접미사(DEC-68, 예 `db`·`hz`·`deg`·`ohm`·`mv`·`amp`·`m2`). `domain` ∈ `METRIC_DOMAINS`.
  `view_kind` ∈ `VIEW_KINDS`: `none`(뷰를 쓰지 않는 metric -- 선언 view 가 오면 거부), `transfer`(전달 뷰 하나 --
  없으면 포트 뷰), `ratio`(분자·분모 전달 뷰 두 개 -- 선언 필수). `objective_axis`: None(제약 metric) 또는
  `OBJECTIVE_AXES` 원소(DEC-77 목적 축 -- spec `objective.budgets` 키로 쓸 수 있는 metric).
"""
import dataclasses

METRIC_DOMAINS = ("dc", "ss", "ls", "geom")
VIEW_KINDS = ("none", "transfer", "ratio")
OBJECTIVE_AXES = ("power", "area")


@dataclasses.dataclass(frozen=True)
class MetricSignature:
    """metric 레지스트리 항목 중 spec 로드가 읽는 부분. 어휘 밖 값이면 `ValueError`(주입하는 쪽의 프로그램 오류)."""

    unit: str
    domain: str
    view_kind: str
    objective_axis: object = None

    def __post_init__(self):
        if not isinstance(self.unit, str) or not self.unit:
            raise ValueError("MetricSignature.unit 은 비어 있지 않은 문자열이어야 한다: " + repr(self.unit))
        if self.domain not in METRIC_DOMAINS:
            raise ValueError("MetricSignature.domain 은 " + repr(METRIC_DOMAINS) + " 중 하나: " + repr(self.domain))
        if self.view_kind not in VIEW_KINDS:
            raise ValueError("MetricSignature.view_kind 는 " + repr(VIEW_KINDS) + " 중 하나: " + repr(self.view_kind))
        if self.objective_axis is not None and self.objective_axis not in OBJECTIVE_AXES:
            raise ValueError("MetricSignature.objective_axis 는 None 또는 " + repr(OBJECTIVE_AXES) + " 중 하나: "
                             + repr(self.objective_axis))
