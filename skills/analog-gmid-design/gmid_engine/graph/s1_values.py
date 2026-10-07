"""S1 그래프의 값 형식·어휘·필드 권한표 -- 데이터 선언 모듈 (설계 design_mod3_s1_graph 3절, 확정 사항 1·2).

공개 정의는 데이터 클래스와 예외뿐이다(규칙 A 데이터 선언 모듈):

* `S1Key` -- S1 지문 {topology_fp, rule_fp, supplies_v_fp}(설계 5.1).
* `BulkResult` -- 소자 하나의 bulk 넷과 그 출처(DEC-61, 사용자 확정 2026-10-07 6번).
* `FieldNotComputed` -- 권한표에 있으나 그 writer 가 아직 돌지 않은 필드를 질의함(조용한 빈 값 금지, WP-02).

S1 은 core `GraphSnapshot` 위에 산다. 필드마다 writer 하나(`S1_WRITERS`), 값과 함께 그 값을 만든 입력 버전을
core `FieldValue` 가 기록한다(필드가 곧 캐시). writer = 구조·bulk 블록과 U2~U4 구조 유도 블록 9개
(설계 design_mod3_structure_u2_u5 4.0 표, C2: 옛 예약 4행을 유형별 필드로 바꿈). U2~U4 값 형식 `Evidence`·`Segment`·
`Branch`·`Column`·`ColumnOrphan`·`GsGroup`·`DcRole`·`RelEdge`·`GvgsSummary` 도 여기 둔다.
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

# ---- U2~U4 구조 유도 어휘 (설계 design_mod3_structure_u2_u5 1~3절)
GRAPH_KEY = "s1"                                       # graph 레코드(스냅샷 전체 필드)의 유일 key
STATUS_DERIVED = "derived"                             # 계획 N3.3 전이표: 엔진 규칙만으로 확정
STATUS_PROPOSED = "proposed"                           # 엔진 제안(선언·ratify 대조 전)
STATUS_REVIEW_NEEDED = "review_needed"                 # 구조로 못 가름(정지 아님, 기록)
ROLE_DIODE = "diode_reference"
ROLE_BIAS = "bias_current_source"
ROLE_SIGNAL = "signal"
ROLE_RULE_DIODE = "1"                                  # 용어집 91행 (1)(2)(3)(5) -- (4) 상속은 ratified 사실 0 이라 발동 0
ROLE_RULE_GS_GROUP = "2"
ROLE_RULE_GATE_GROUND = "3"
ROLE_RULE_REST = "5"
REL_EQUAL_VGS = "equal_vgs"
REL_VDS_EQ_VGS = "vds_eq_vgs"
REL_KCL_GROUP = "kcl_group"
REL_MATCHING_RATIO = "matching_ratio"
REL_MATCHING_OFFSET = "matching_offset"
REL_L_CLASS = "l_class"
REL_KVL_BRANCH = "kvl_branch"
REL_PORT_DIFF = "port_diff"                            # G_vgs v1 사이클(제약 없음, 대조만)
REL_VDS_SATURATION = "vds_saturation"                  # VDS-1 사이클(포화 하한 부등식)
DOMAIN_DC = "dc"
DOMAIN_DC_TO_SS = "dc_to_ss"
DOMAIN_GEOM = "geom"
CYCLE_V2_RAIL = "v2_rail"                              # 레일 고정 노드 F 를 지나는 v2 사이클(ΔV = 레일 차)
CYCLE_V2_ZERO = "v2_zero"                              # F 를 지나지 않는 v2 사이클(ΣVGS = 0)
COLUMN_RULE = "rail_pair_simple_path"
# J 항목(설계 6절 기본안)에 기댄 판정이 evidence.basis 에 남기는 ID
J_PARALLEL_MERGE = "J13-a"
J_PRUNE_ORDER = "J13-b"
J_RAIL_PAIRS = "J13-c"
J_IDEAL_SOURCE = "J13-d"
J_ALL_VIEW_GROUND = "J-U3-a"
J_UNRESOLVED_GROUP = "J-U3-c"
J_L_CLASS = "J-U4-a"
J_DIFF_PAIR = "J-U4-b"
J_GVGS_READING = "J12-c"
# U2~U4 정지 분기(core StructureUnresolvedError, detail reason = UNSUPPORTED_RULE_BRANCH)
BRANCH_DC_SELF_LOOP = "dc_self_loop"
BRANCH_DC_ISOLATED_LOOP = "dc_isolated_loop"
BRANCH_COLUMN_BUDGET = "column_enumeration_over_budget"
BRANCH_MOS_KIND = "mos_kind_unsupported"
BRANCH_GVGS_SELF_EDGE = "gvgs_self_edge"

# ---- 필드 (kind, field) 와 writer
S1_STRUCTURE_WRITER = "s1_structure"
S1_BULK_WRITER = "s1_bulk"
S1_DC_CONDUCTION_WRITER = "s1_dc_conduction"
S1_BRANCHES_WRITER = "s1_branches"
S1_COLUMNS_WRITER = "s1_columns"
S1_GS_GROUPS_WRITER = "s1_gs_groups"
S1_DC_ROLES_WRITER = "s1_dc_roles"
S1_REL_VGS_WRITER = "s1_rel_vgs"
S1_REL_KCL_WRITER = "s1_rel_kcl"
S1_REL_MATCHING_WRITER = "s1_rel_matching"
S1_GVGS_WRITER = "s1_gvgs"
STRUCTURE_WRITES = (
    ("node", "ac_ground_class"), ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"),
    ("node", "terminals"),
    ("device", "bulk_declared"), ("device", "dc_nets"), ("device", "element_class"), ("device", "is_diode"),
    ("device", "kind"), ("device", "pins"), ("device", "unsupported"), ("device", "value"), ("device", "value_key"),
)
BULK_READS = (
    ("device", "bulk_declared"), ("device", "element_class"), ("device", "kind"), ("device", "pins"),
    ("node", "is_rail"),
)
BULK_WRITES = (("device", "bulk"),)
DC_CONDUCTION_READS = (
    ("device", "dc_nets"), ("device", "element_class"), ("device", "kind"), ("device", "unsupported"),
    ("node", "is_rail"), ("node", "port_direction"),
)
DC_CONDUCTION_WRITES = (("graph", "dc_pruned"), ("graph", "dc_segments"))
BRANCHES_READS = (("graph", "dc_segments"), ("device", "element_class"), ("node", "is_rail"))
BRANCHES_WRITES = (("graph", "branches"), ("node", "dc_branch_node"))
COLUMNS_READS = (("graph", "branches"), ("node", "is_rail"))
COLUMNS_WRITES = (("graph", "column_orphans"), ("graph", "column_pairs"), ("graph", "columns"))
GS_GROUPS_READS = (("device", "element_class"), ("device", "kind"), ("device", "pins"))
GS_GROUPS_WRITES = (("graph", "gs_groups"),)
DC_ROLES_READS = (
    ("device", "element_class"), ("device", "is_diode"), ("device", "kind"), ("device", "pins"),
    ("node", "ac_ground_class"), ("node", "is_rail"), ("graph", "gs_groups"),
)
DC_ROLES_WRITES = (("device", "dc_role"),)
REL_VGS_READS = (("graph", "gs_groups"), ("device", "is_diode"), ("device", "pins"))
REL_VGS_WRITES = (("graph", "rel_equal_vgs"), ("graph", "rel_vds_eq_vgs"))
REL_KCL_READS = (("graph", "branches"),)
REL_KCL_WRITES = (("graph", "rel_kcl_group"),)
REL_MATCHING_READS = (
    ("graph", "gs_groups"), ("device", "element_class"), ("device", "kind"), ("device", "pins"), ("node", "is_rail"),
)
REL_MATCHING_WRITES = (("graph", "rel_l_class"), ("graph", "rel_matching_offset"), ("graph", "rel_matching_ratio"))
GVGS_READS = (
    ("device", "element_class"), ("device", "is_diode"), ("device", "kind"), ("device", "pins"),
    ("node", "is_rail"), ("node", "port_direction"),
)
GVGS_WRITES = (("graph", "gvgs_summary"), ("graph", "rel_kvl_branch"))
S1_WRITERS = WriterTable(
    tuple((kind, field, writer)
          for writer, writes in ((S1_STRUCTURE_WRITER, STRUCTURE_WRITES), (S1_BULK_WRITER, BULK_WRITES),
                                 (S1_DC_CONDUCTION_WRITER, DC_CONDUCTION_WRITES),
                                 (S1_BRANCHES_WRITER, BRANCHES_WRITES), (S1_COLUMNS_WRITER, COLUMNS_WRITES),
                                 (S1_GS_GROUPS_WRITER, GS_GROUPS_WRITES), (S1_DC_ROLES_WRITER, DC_ROLES_WRITES),
                                 (S1_REL_VGS_WRITER, REL_VGS_WRITES), (S1_REL_KCL_WRITER, REL_KCL_WRITES),
                                 (S1_REL_MATCHING_WRITER, REL_MATCHING_WRITES), (S1_GVGS_WRITER, GVGS_WRITES))
          for kind, field in writes)
)

# ---- rule_fp 대상: S1 필드 값을 정하는 graph 파일(이 패키지 안 basename). s1_key 가 파일 바이트로 지문한다.
S1_RULE_FILES = ("ac_ground_static.py", "branches.py", "bulk_default.py", "columns.py", "dc_conduction.py",
                 "dc_roles.py", "gs_groups.py", "gvgs_cycles.py", "rel_kcl.py", "rel_matching.py", "rel_vgs.py",
                 "s1_build.py", "s1_index.py", "s1_structure.py", "s1_values.py", "supplies.py")
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


@dataclasses.dataclass(frozen=True)
class Evidence:
    """판정 근거. `rule` = 규칙 이름, `nets` = 판정에 쓴 넷, `group` = 묶음 멤버(없으면 ()),
    `basis` = 기댄 J 항목 ID(설계 6절 기본안, 없으면 ())."""

    rule: str
    nets: tuple = ()
    group: tuple = ()
    basis: tuple = ()


@dataclasses.dataclass(frozen=True)
class Segment:
    """같은 무향 넷 쌍 사이 DC 엣지 묶음(병렬 소자 = segment 하나). `nets` 정렬 2-tuple, `elements` 이름순."""

    nets: tuple
    elements: tuple


@dataclasses.dataclass(frozen=True)
class Branch:
    """닻(레일·분기 노드·차수 1 넷) 사이 극대 직렬 segment 사슬. `id` = 생성 순번(int), `ends` = (출발 닻, 도착 닻),
    `segments` = 걷는 순서, `has_ideal_source` = 이상원 원소 포함."""

    id: int
    ends: tuple
    segments: tuple
    has_ideal_source: bool


@dataclasses.dataclass(frozen=True)
class Column:
    """레일 쌍 사이 가지 그래프의 노드-단순 경로 하나. `rails` = (r1, r2) 이름순, `branch_order` = 경로의 가지 id,
    `parallel_expansion` = 경로 위 segment 원소 수의 곱(병렬 소자를 따로 셀 때의 경로 수), `status`, `evidence`."""

    id: int
    rails: tuple
    branch_order: tuple
    parallel_expansion: int
    status: str
    evidence: Evidence


@dataclasses.dataclass(frozen=True)
class ColumnOrphan:
    """어느 레일 쌍 기둥에도 들지 않는 가지(DEC-71 (1), 정지 아님)."""

    branch: int
    status: str


@dataclasses.dataclass(frozen=True)
class GsGroup:
    """같은 (kind, gate 넷, source 넷)인 MOS 2개 이상. `members` 이름순."""

    kind: str
    gate: str
    source: str
    members: tuple


@dataclasses.dataclass(frozen=True)
class DcRole:
    """소자 DC 역할(용어집 91행). `role` ∈ {diode_reference, bias_current_source, signal}."""

    role: str
    status: str
    evidence: Evidence


@dataclasses.dataclass(frozen=True)
class RelEdge:
    """관계 엣지(계획 N3.3 엣지 스키마). `type`·`domain`·`members`(소자 이름 또는 segment 원소 tuple)·`status`·`evidence`."""

    type: str
    domain: str
    members: tuple
    status: str
    evidence: Evidence


@dataclasses.dataclass(frozen=True)
class GvgsSummary:
    """G_vgs(DEC-64) 요약. `cyclomatic` = 단순 그래프 순환수, `v2_port0`·`v2_port1`·`v1` = 순환수 분해,
    `fixed_vgs` = gate·source 가 둘 다 레일인 MOS, `port_diff` = v1 사이클(RelEdge), `vds_saturation` = VDS-1 사이클(RelEdge)."""

    cyclomatic: int
    v2_port0: int
    v2_port1: int
    v1: int
    fixed_vgs: tuple
    port_diff: tuple
    vds_saturation: tuple
