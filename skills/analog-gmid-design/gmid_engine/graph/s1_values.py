"""S1 그래프의 값 형식·어휘·필드 권한표 -- 데이터 선언 모듈 (설계 design_mod3_s1_graph 3절, 확정 사항 1·2).

공개 정의는 데이터 클래스와 예외뿐이다(규칙 A 데이터 선언 모듈):

* `S1Key` -- S1 지문 {topology_fp, rule_fp, supplies_v_fp}(설계 5.1).
* `BulkResult` -- 소자 하나의 bulk 넷과 그 출처(DEC-61, 사용자 확정 2026-10-07 6번).
* `FieldNotComputed` -- 권한표에 있으나 그 writer 가 아직 돌지 않은 필드를 질의함(조용한 빈 값 금지, WP-02).

S1 은 core `GraphSnapshot` 위에 산다. 필드마다 writer 하나(`S1_WRITERS`), 값과 함께 그 값을 만든 입력 버전을
core `FieldValue` 가 기록한다(필드가 곧 캐시). 이번 단계가 쓰는 writer 는 `S1_STRUCTURE_WRITER`·`S1_BULK_WRITER`
둘이고, 나머지 행(`dc_role`·`relation`·`branches`·`columns`)은 다음 단계 writer 자리다(값은 아직 없다 ->
질의하면 `FieldNotComputed`).
"""
import dataclasses

from gmid_engine.core import WriterTable

# ---- 원소 분류·kind 어휘 (지원 kind 밖 원소는 S1 에 넣되 `unsupported` 필드에 분기 이름을 남긴다, DEC-59·61·76)
ELEMENT_MOS = "mos"
ELEMENT_PASSIVE = "passive"
ELEMENT_SOURCE = "ideal_source"
NMOS = "nmos"
PMOS = "pmos"
MOS_KINDS = (NMOS, PMOS)
SUPPORTED_PASSIVE_KINDS = ("capacitor", "resistor")
SUPPORTED_SOURCE_KINDS = ("current_source",)          # 이상 전압원은 교류접지 (3) 미구현 -> 기록만(설계 2.2)
UNSUPPORTED_BRANCHES = (
    (ELEMENT_MOS, "mos_kind_unsupported"),
    (ELEMENT_PASSIVE, "passive_kind_unsupported"),
    (ELEMENT_SOURCE, "source_kind_unsupported"),
)

# ---- 단자 이름: MOS 채널 3단자(bulk 는 단자 인덱스에 넣지 않는다, 설계 3절). 2단자는 authoring TWO_TERMINAL_NAMES.
MOS_DRAIN = "d"
MOS_GATE = "g"
MOS_SOURCE = "s"
MOS_TERMINAL_NAMES = (MOS_DRAIN, MOS_GATE, MOS_SOURCE)
MOS_CHANNEL_TERMINALS = (MOS_DRAIN, MOS_SOURCE)

# ---- 뷰와 무관한 교류접지 분류(N3.2-1 (1)(2))
AC_GROUND_RAIL = "rail"
AC_GROUND_GATE_ONLY = "gate_only_undriven"

# ---- bulk 출처·미결 사유
BULK_DECLARED = "declared"
BULK_DEFAULT_RULE = "default_rule"
BULK_UNDETERMINED = "undetermined"
BULK_NEEDS_SUPPLIES = "needs_supplies_v"
BULK_UNSUPPORTED_KIND = "unsupported_kind"

# ---- bulk 기본 규칙이 조용히 묶지 않고 정지하는 분기(core StructureUnresolvedError, detail reason)
UNSUPPORTED_RULE_BRANCH = "unsupported_rule_branch"
BRANCH_MULTI_DOMAIN = "bulk_multi_domain"
BRANCH_POTENTIAL_TIE = "bulk_rail_potential_tie"

# ---- 필드 (kind, field) 와 writer
S1_STRUCTURE_WRITER = "s1_structure"
S1_BULK_WRITER = "s1_bulk"
STRUCTURE_WRITES = (
    ("node", "ac_ground_class"), ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"),
    ("node", "terminals"),
    ("device", "bulk_declared"), ("device", "element_class"), ("device", "is_diode"), ("device", "kind"),
    ("device", "pins"), ("device", "unsupported"), ("device", "value"), ("device", "value_key"),
)
BULK_READS = (
    ("device", "bulk_declared"), ("device", "element_class"), ("device", "kind"), ("device", "pins"),
    ("node", "is_rail"),
)
BULK_WRITES = (("device", "bulk"),)
RESERVED_FIELDS = (                                    # 다음 단계 writer 자리(설계 3절 U2·U3·U4)
    ("device", "dc_role", "dc_roles"),
    ("edge", "relation", "relations"),
    ("graph", "branches", "dc_conduction"),
    ("graph", "columns", "columns"),
)
S1_WRITERS = WriterTable(
    tuple((kind, field, S1_STRUCTURE_WRITER) for kind, field in STRUCTURE_WRITES)
    + tuple((kind, field, S1_BULK_WRITER) for kind, field in BULK_WRITES)
    + RESERVED_FIELDS
)

# ---- rule_fp 대상: S1 필드 값을 정하는 graph 파일(이 패키지 안 basename). s1_key 가 파일 바이트로 지문한다.
S1_RULE_FILES = ("ac_ground_static.py", "bulk_default.py", "s1_build.py", "s1_index.py", "s1_structure.py",
                 "s1_values.py", "supplies.py")
NO_SUPPLIES_FP = "none"


@dataclasses.dataclass(frozen=True)
class S1Key:
    """S1 지문. `topology_fp` = TopologyDoc.connectivity_fp, `rule_fp` = `S1_RULE_FILES` 코드 지문,
    `supplies_v_fp` = 정규화한 supplies_v 지문(없으면 `NO_SUPPLIES_FP`)."""

    topology_fp: str
    rule_fp: str
    supplies_v_fp: str


@dataclasses.dataclass(frozen=True)
class BulkResult:
    """소자 bulk. `net` = 넷 이름 또는 None, `origin` ∈ {declared, default_rule, undetermined},
    `reason` = undetermined 일 때 사유(needs_supplies_v | unsupported_kind), 아니면 None."""

    net: object
    origin: str
    reason: object = None


class FieldNotComputed(LookupError):
    """S1 권한표에 있는 필드지만 그 writer 가 이 스냅샷에서 아직 돌지 않았다(빈 값을 돌려주지 않는다)."""
