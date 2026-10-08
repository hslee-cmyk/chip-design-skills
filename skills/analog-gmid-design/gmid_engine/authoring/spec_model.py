"""회로 사이징 spec 로드 결과의 불변 형식 -- 데이터 선언 모듈 (설계 design_spec_format 3.1 `spec_model.py`, 3.4).

공개 정의는 frozen dataclass 뿐이다(규칙 A 데이터 선언 모듈):

* `SpecSource` -- 선언 하나의 출처(kind·origin·record·citation·decided·plan_id). 지문(`__canonical__`)에는 `kind` 만
  들어간다: `record`·`citation`·`decided` 문구를 고쳐도 캐시가 산다(NFR-2, 설계 3.4). `pending_spice` 는 판정 여부를
  바꾸므로 kind 는 지문에 든다.
* `PendingMark` -- 결정 대기 표지 하나(문서 경로, 결정 ID). `SizingSpecDoc.pending` 에 모인다(설계 1.5).
* `InputDc`·`ElementValue`·`ExciteSense`·`SenseDecl`·`ViewDecl`·`ConstraintDecl`·`TargetDecl`·`SettlingDecl`·`SettingValue`·
  `RuleChoice`·`ObjectiveBudget`·`RegionDecl` -- 검증을 통과한 선언의 투영. `mode` 가 `pending` 이면 `decision` 에
  결정 ID 가 있고 값 필드는 None 이다.
* `SizingSpecDoc` -- spec 전체 투영과 섹션 지문. 직접 만들지 말고 `SizingSpecDoc.from_sections` 로 만든다(지문 계산).
  섹션 지문 = 그 섹션 소비자만 무효화하는 캐시 키(필드가 곧 캐시). `spec_fp` = 섹션 지문들의 지문(S0 'spec 전체 해시').
  `file_sha256` 은 출처 기록이라 지문 밖이다.
"""
import dataclasses

from gmid_engine.core import fp_of, require_immutable, sorted_items


@dataclasses.dataclass(frozen=True)
class SpecSource:
    """선언 하나의 출처. 부필드 규칙은 `spec_sources.source_declaration_checks`."""

    kind: str
    origin: object = None
    record: object = None
    citation: object = None
    decided: object = None
    plan_id: object = None

    def __canonical__(self):
        return (self.kind,)


@dataclasses.dataclass(frozen=True)
class PendingMark:
    """결정 대기 표지 `{"pending": <결정 ID>}` 하나: `path` = 문서 안 위치, `decision` = 결정 ID."""

    path: str
    decision: str


@dataclasses.dataclass(frozen=True)
class InputDc:
    """입력 DC. `mode` ∈ net / value / engine / pending."""

    mode: str
    net: object = None
    value_v: object = None
    source: object = None
    decision: object = None


@dataclasses.dataclass(frozen=True)
class ElementValue:
    """수동소자·이상원 값 선언 하나. `mode` ∈ value / engine / pending. value 일 때 `value_key`·`value`."""

    name: str
    mode: str
    value_key: object = None
    value: object = None
    source: object = None
    decision: object = None
    measurement_load: bool = False      # [결정 11] 측정 부하 표지 -- 설계 면적(area_search_m2)에서 뺀다(spec_elements)


@dataclasses.dataclass(frozen=True)
class ExciteSense:
    """전달 뷰 하나: `ac_excite` = (넷, 진폭) 이름순 tuple, `sense_p`, `sense_n`(None 가능), `sense_mode`."""

    ac_excite: tuple
    sense_p: str
    sense_n: object
    sense_mode: str


@dataclasses.dataclass(frozen=True)
class SenseDecl:
    """관측 하나(여기 없음): `sense_p`, `sense_n`(None 가능), `sense_mode` -- 출력 포트 뷰·루프 뷰(β = 1)의 관측."""

    sense_p: str
    sense_n: object
    sense_mode: str


@dataclasses.dataclass(frozen=True)
class ViewDecl:
    """제약의 뷰. `mode` ∈ none(뷰 없는 metric) / port(포트 전달 뷰) / transfer / ratio / pending / loop / sense / cm_output.

    * port: `weights` = 입력 포트 (넷, 가중) 넷순(role 가중 -- 차동 ±1/|D|, 단일 1), `sense` = 출력 포트 `SenseDecl`
      (topology 교차 검사를 못 한 로드에서는 둘 다 None).
    * loop(7a design 2.2·2.3·2.5): `beta` ∈ declared(spec feedback 비지 않음) / unity(빈 list). declared 면 `cuts` =
      (되먹임 소자, 절단 넷) 소자 이름순, `weights` = 절단 넷의 (넷, 가중) 넷순. unity 면 `weights`·`sense` 가 포트 전달 뷰와 같다.
    * cm_output([CM] 출력 포트 CM 주입 루프): `weights` = 차동 출력 포트 (넷, 1/2) 넷순 -- 두 출력 넷에 동일 부호 주입. `cuts` = ((구동자 MOS 이름, 옮길 출력 넷), ...) **MOS 이름 오름차순**
      (`cm_partition` 결과; 비면 metrics 가 같은 분류를 직접 한다). 순서는 이름 의존이다 -- 값은 순서에 무관하고 소비자는 집합으로 읽는다.
    * sense(출력 포트 뷰, 7a design 3.1): `sense` = 감지 `SenseDecl`(여기 없음).
    * pending: `decision` = 결정 ID(선언 표지, 또는 loop 의 feedback 결정 대기 전파).
    유도된 내용이 여기에 들어가므로 `constraints_fp` 가 feedback·ports 변경을 따라간다."""

    mode: str
    transfer: object = None
    num: object = None
    den: object = None
    decision: object = None
    beta: object = None
    cuts: tuple = ()
    weights: tuple = ()
    sense: object = None


@dataclasses.dataclass(frozen=True)
class ConstraintDecl:
    """성능 제약 하나. `metric` 이 결정 대기면 None + `metric_decision`. `value` 는 참조 해석 뒤 값(참조 대상이 결정
    대기면 None + `value_decision`). `judged` = 판정에 쓰는가(`pending_spice` 와 그것을 가리키는 참조는 False, U-17).
    `ref` = 참조 문자열(지문에 넣지 않는다 -- 해석된 값이 든다)."""

    metric: object
    op: str
    value: object
    judged: bool
    view: object
    source: object
    metric_decision: object = None
    value_decision: object = None
    ref: object = None


@dataclasses.dataclass(frozen=True)
class TargetDecl:
    """보상 목표 하나(`gbw_target_hz`·`pm_target_deg`). 결정 대기면 value None + `decision`."""

    key: str
    value: object
    source: object = None
    decision: object = None
    ref: object = None


@dataclasses.dataclass(frozen=True)
class SettlingDecl:
    """정착 목표(F11): 전체 정착 시간 `total_s`, 선형 정착 시간 `linear_s`."""

    total_s: float
    linear_s: float
    source: object = None


@dataclasses.dataclass(frozen=True)
class SettingValue:
    """탐색 설정 값 하나(`search` 섹션). 결정 대기면 value None + `decision`."""

    field: str
    value: object
    source: object = None
    decision: object = None


@dataclasses.dataclass(frozen=True)
class ThetaBound:
    """원소별 θ 상자 하나(`search.theta_bounds`, 2026-10-08). `kind` ∈ resistor(Ω)·capacitor(F), `lo` < `hi` 양수, `source` 출처."""

    element: str
    kind: str
    lo: float
    hi: float
    source: object = None


@dataclasses.dataclass(frozen=True)
class RuleChoice:
    """규칙 이름 선택 하나(`spice_check`·`front_refilter`). 결정 대기면 rule None + `decision`."""

    field: str
    rule: object
    source: object = None
    decision: object = None


@dataclasses.dataclass(frozen=True)
class ObjectiveBudget:
    """목적 축 예산 하나: 목적 metric, op, 값."""

    metric: str
    op: str
    value: float
    source: object = None


@dataclasses.dataclass(frozen=True)
class RegionDecl:
    """의도 영역 선언 하나: 소자 이름, 영역."""

    device: str
    region: str
    source: object = None


@dataclasses.dataclass(frozen=True)
class SizingSpecDoc:
    """검증을 통과한 회로 사이징 spec. 모든 모음 필드는 tuple(이름순 또는 문서 순서), 결정 대기 섹션은 PendingMark."""

    circuit: str
    topology_fp: str
    origin: str
    supplies_v: tuple
    input_dc: object
    element_values: tuple
    feedback: object
    constraints: tuple
    pending_constraints: tuple
    compensation_targets: tuple
    node_voltage_targets_v: object
    intended_region: object
    objective: object
    search: tuple
    spice_check: tuple
    front_refilter: tuple
    pending: tuple
    section_fps: tuple
    spec_fp: str
    file_sha256: str

    def __post_init__(self):
        require_immutable(self)

    @property
    def judged_constraints(self):
        """판정에 쓰는 제약만(`judged` 가 True 인 것)."""
        return tuple(c for c in self.constraints if c.judged)

    @classmethod
    def from_sections(cls, circuit, topology_fp, origin, sections, pending, file_sha256):
        """`sections` = 섹션 이름 -> 값 매핑(아래 `SECTION_GROUPS` 의 이름 전부). 섹션 지문과 `spec_fp` 를 계산한다."""
        fps = _section_fps(sections)
        return cls(circuit, topology_fp, origin, sections["supplies_v"], sections["input_dc"],
                   sections["element_values"], sections["feedback"], sections["constraints"],
                   sections["pending_constraints"], sections["compensation_targets"],
                   sections["node_voltage_targets_v"], sections["intended_region"], sections["objective"],
                   sections["search"], sections["spice_check"], sections["front_refilter"],
                   sorted_items(pending, key=lambda m: (m.path, m.decision)), fps, fp_of(fps), file_sha256)


# 섹션 지문 묶음: (지문 이름, 그 지문에 드는 섹션들). 소비자가 같은 섹션끼리 묶는다(설계 3.4).
SECTION_GROUPS = (
    ("supplies_fp", ("supplies_v",)),
    ("operating_fp", ("input_dc", "node_voltage_targets_v", "intended_region")),
    ("elements_fp", ("element_values",)),
    ("feedback_fp", ("feedback",)),
    ("constraints_fp", ("constraints", "pending_constraints")),
    ("compensation_fp", ("compensation_targets",)),
    ("objective_fp", ("objective",)),
    ("search_fp", ("search",)),
    ("spice_check_fp", ("spice_check",)),
    ("refilter_fp", ("front_refilter",)),
)


def _section_fps(sections):
    # 제약은 문서 순서와 무관하게(내용 지문 정렬) 지문한다 -- 순서만 바꾼 spec 은 같은 캐시를 쓴다.
    out = []
    for name, members in SECTION_GROUPS:
        parts = []
        for member in members:
            value = sections[member]
            if member == "constraints":
                value = sorted_items(value, key=fp_of)
            parts.append((member, value))
        out.append((name, fp_of(tuple(parts))))
    return tuple(out)
