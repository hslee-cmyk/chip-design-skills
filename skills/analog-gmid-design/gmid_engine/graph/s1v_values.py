"""S1v(SP1 뷰 구조) 값 형식·어휘 -- 데이터 선언 모듈 (설계 41 §1, 계획 N3.2).

공개 정의는 frozen dataclass 와 상수뿐이다(규칙 A 데이터 선언 모듈). S1v 는 `build_s1v` 가 만들고 모든 값은 tuple·frozenset·
frozen dataclass 라 `fp_of` 로 지문한다(같은 입력 = 같은 S1v, 이름 전단사에는 그 사상으로만 바뀐다).

* `Mos`·`TwoTerm`·`NetModel` -- S1 필드를 뷰 계산용으로 한 번 풀어 놓은 읽기 전용 모형(`net_model` 이 만든다).
* `ViewSeed` -- 수집한 뷰 하나(여기·감지). `ViewS1v` -- 뷰 하나의 유도 결과 전부.
* `Finding` -- `review_needed`·`unsupported_rule_branch` 기록 하나(항상 근거 코드와 대상 소자·넷이 있다).
* `S1v` -- 전체 결과와 키.
"""
import dataclasses

# ---- rule_fp 대상: S1v 필드 값을 정하는 graph 파일(이 패키지 안 basename). `s1v_rule_fp` 가 파일 바이트로 지문한다.
S1V_RULE_FILES = (
    "ac_ground_view.py", "blocks.py", "buffer_bundles.py", "cells.py", "composite_blocks.py", "declared_compare.py",
    "drive_kind.py", "feedforward_cells.py", "l_classes.py", "loop_classify.py", "loop_cuts.py", "loop_roles.py", "loops.py",
    "net_model.py", "node_impedance.py", "output_direction.py", "polarity.py", "pole_nodes.py", "s1v_build.py", "s1v_values.py",
    "signal_reach.py", "stage_bfs.py", "structure_load.py", "view_analysis.py", "views.py", "virtual_ground.py",
)
# ---- `structure_rule_fp` 대상 = S1V_RULE_FILES 합집합 이 파일들: 사실이 대조하거나 덮어쓰는 값을 만드는 S1 쪽 소비 파일(40 §3.2-3 `rule_hash`)
STRUCTURE_RULE_EXTRA_FILES = ("composite_diode.py", "dc_roles.py", "gs_groups.py", "matching_groups.py")
# ---- structure.json (40 §3.2-3): 형식 버전, concept 닫힌 어휘, 값 어휘
STRUCTURE_SCHEMA_VERSION = "1"
CONCEPT_DRIVE_KIND = "drive_kind"
CONCEPT_STAGE_MEMBERS = "stage_members"
CONCEPT_DC_ROLE = "dc_role"
CONCEPT_LOOP_ROLE = "loop_role"
CONCEPT_FEEDFORWARD_CELL = "feedforward_cell"
CONCEPT_AC_GROUND_EXCEPTION = "ac_ground_exception"
CONCEPT_MATCHING_PAIR = "matching_pair"
CONCEPT_L_OWNER = "l_owner"         # L 동치류 주인(override, 41 §1.12.5, C-3): subject = 동치류 멤버 이름 정렬 JSON 배열, value = 주인 소자 이름
CONCEPTS = (CONCEPT_DRIVE_KIND, CONCEPT_STAGE_MEMBERS, CONCEPT_DC_ROLE, CONCEPT_LOOP_ROLE, CONCEPT_FEEDFORWARD_CELL,
            CONCEPT_AC_GROUND_EXCEPTION, CONCEPT_MATCHING_PAIR, CONCEPT_L_OWNER)
FF_ARROW = "->"                     # `feedforward_cell` 값 `<종류>:<탭>-><merge>` 의 탭·merge 구분(넷 이름에 들어 있으면 로드 거부)
FF_SEPARATOR = ":"
FF_CELL = "ff"
FF_BIAS = "ff_bias"
FF_LOAD = "ff_load"
FF_KINDS = (FF_CELL, FF_BIAS, FF_LOAD)
MATCH_PAIR_VALUE = "branch_symmetric"
# ---- 뷰 종류
VIEW_TRANSFER = "transfer"
VIEW_LOOP = "loop"
# ---- 뷰 씨앗 출처(`collect_views` 가 `ViewSeed.source` 에 쓴다)와 spec metric 이름(authoring/metrics 카탈로그와 같은 값 -- graph 는 그 패키지를 import 할 수 없다)
VIEW_SOURCE_DEFAULT = "default_port_view"
VIEW_SOURCE_DECLARED = "spec_constraint_view"
METRIC_PM_SS = "pm_ss_deg"            # 전체 안정도(루프) 제약 -- 중첩 Miller 내부 루프를 덮는다(41 §1.12.3)
METRIC_GAIN_SS = "gain_ss_db"         # gain 제약 전달 뷰 -- L 동치류 주인 규칙 main_path_signal 이 읽는다(41 §1.12.5)
# ---- 쌍(둘)의 크기: pass 묶음의 정·역방향 소자, 기모드 여기의 두 넷, 능동 셀 둘
PAIR = ("first", "second")
# ---- spec 제약 뷰 mode 어휘(authoring ViewDecl.mode 와 같은 값)와 입력 포트 role(authoring `ports.ROLE_*` 와 같은 값 --
#      authoring 이 `__all__` 로 내보내면 그쪽으로 교체한다, U5 요청)
SPEC_VIEW_PORT = "port"
SPEC_VIEW_LOOP = "loop"
SPEC_VIEW_TRANSFER = "transfer"
SPEC_VIEW_RATIO = "ratio"
PORT_ROLE_DIFF_P = "differential_input_p"
PORT_ROLE_DIFF_N = "differential_input_n"
# ---- 셀 어휘(41 §1.4)
CELL_CS = "cs"
CELL_CG = "cg"
CELL_CD = "cd"
CELL_PASS = "pass"
CELL_DIODE_LOAD = "diode_load"
CELL_OFF = "off"
CELL_KINDS = (CELL_CS, CELL_CG, CELL_CD, CELL_PASS, CELL_DIODE_LOAD, CELL_OFF)
# ---- 입력 노드 구동 종류(41 §1.5)
DRIVE_VOLTAGE = "voltage"
DRIVE_CURRENT = "current"
# ---- 구동 종류 근거(basis)
BASIS_PORT = "port"
BASIS_SOURCE_ENTRY = "source_entry"
BASIS_DRAIN_GATE_EXIT = "drain_entry_gate_exit"
BASIS_DRAIN_CHANNEL_EXIT = "drain_entry_channel_exit"
BASIS_DRAIN_STAGE_BOUNDARY = "drain_entry_gate_and_channel_exit"
BASIS_DRAIN_TAP = "drain_entry_tap"
BASIS_DRAIN_TERMINAL = "drain_entry_no_exit"
BASIS_MIXED_BIAS = "mixed_bias_drain"
BASIS_MIXED_SIGNAL = "mixed_signal_drain"
BASIS_INHERIT_PASSIVE = "inherit_passive"
BASIS_INHERIT_PASS = "inherit_pass_bundle"
BASIS_RATIFIED = "ratified_fact"
BASIS_UNDRIVEN = "undriven"
# ---- 블록·소자 AC 역할
BLOCK_GAIN = "gain"
BLOCK_BUFFER = "buffer"
BLOCK_COMPOSITE = "composite"
ROLE_INPUT = "input"
ROLE_CASCODE = "cascode"
ROLE_FOLLOWER = "follower"
ROLE_PASS = "pass"
ROLE_MIRROR = "mirror"
ROLE_LOAD = "load"
ROLE_TAIL = "tail_source"   # 계획 N3.2-6 의 tail. 값 "tail" 은 library 넷 이름과 같아 구조 규칙 E(회로 이름 리터럴 금지)가 거부한다
ROLE_DIODE_LOAD = "diode_load"
# ---- 임피던스 등급(41 §1.7-4)
IMP_LOW = "low"
IMP_HIGH = "high"
IMP_VALUE = "value_dependent"
# ---- 출력 방향 셀 구분(DEC-65)과 토폴로지
DIR_BETA = "beta"
DIR_SIGMA = "sigma"
DIR_KAPPA = "kappa"
TOPO_PUSH_PULL = "push_pull"
TOPO_CLASS_A = "class_a"
TOPO_NONE = "none"
# ---- 기록 종류
SEVERITY_REVIEW = "review_needed"
SEVERITY_UNSUPPORTED = "unsupported_rule_branch"
# ---- 루프 분류(41 §1.8, 계획 N3.2-2)
LOOP_BIAS_SCC = "bias_scc"
LOOP_MILLER = "miller"
LOOP_VIEW = "loop_view"
LOOP_RECORD_ONLY = "record_only"
LOOP_SOURCE = "loop_cut"
PORT_ROLE_DIFF_OUT_P = "differential_output_p"
PORT_ROLE_DIFF_OUT_N = "differential_output_n"
SEVERITY_INFO = "info"
LOOP_LOCAL_FEEDBACK = "local_feedback"
LOOP_COMPOSITE_INTERNAL = "composite_diode_internal"     # (1.6) 복합 diode 묶음 안 DC 국소 루프(41 §1.12.1-3), 루프 뷰 없음
LOOP_COMPENSATION_INTERNAL = "compensation_internal"     # 중첩 Miller 내부 루프(41 §1.12.3), 루프 뷰 없음, 안정도는 T 의 pm_ss_deg
LOOP_ROLES = (LOOP_VIEW, LOOP_COMPENSATION_INTERNAL, LOOP_COMPOSITE_INTERNAL, LOOP_BIAS_SCC)   # `loop_role` 사실 값 어휘
# ---- 루프 엣지 종류(41 §1.8)
EDGE_GATE_DRAIN = "gate_drain"
EDGE_GATE_SOURCE = "gate_source"
EDGE_SOURCE_DRAIN = "source_drain"
EDGE_RESISTOR = "resistor"
EDGE_CAPACITOR = "capacitor"
EDGE_PASS = "pass"
PASSIVE_EDGES = (EDGE_RESISTOR, EDGE_CAPACITOR)
# ---- Finding 코드(분기 이름)
F_CELL_AMBIGUOUS = "cell_ambiguous"
F_PASS_GROUP = "pass_group_unsupported"
F_DRIVE_CYCLE = "drive_inherit_cycle"
F_MIXED_SIGNAL = "mixed_drive_signal_drain"
F_MIXED_UNRESOLVED = "mixed_drive_unresolved_group"
F_GATE_ON_CURRENT = "gate_on_current_node"
F_CURRENT_INPUT_CG = "current_input_cg"
F_CS_LOW_IMPEDANCE = "cs_output_low_impedance"
F_NODE_OVERLAP = "block_node_overlap"
F_MULTI_INPUT = "multi_input_block"
F_COMPOSITE_BRANCH = "composite_dag_not_chain"
F_COMPOSITE_PENDING = "composite_block_pending_ratify"
F_BUFFER_MULTI_OUTPUT = "buffer_multi_output"
F_COMPOSITE_BUDGET = "composite_over_budget"
F_CYCLE_BUDGET = "cycle_enumeration_over_budget"
REASON_CYCLE_BUDGET = "cycle_enumeration_over_budget"
F_LOOP_RECORD_ONLY = "loop_record_only"
F_LOOP_NO_CUT = "loop_no_cut_candidate"
F_LOOP_POLARITY = "loop_polarity_undefined"
F_LOOP_3A = "loop_active_cell_off_forward"
F_UNDECLARED_LOOP = "undeclared_loop_constraint"
F_LOOP_CUT_UNMATCHED = "loop_cut_unmatched"
F_CM_LOOP_UNCONSTRAINED = "cm_loop_unconstrained"
F_DECLARED_MISMATCH = "declared_stage_mismatch"
F_UNSUPPORTED_VIEW = "unsupported_view"
F_VIEW_REQUIRED = "view_required"
F_STRUCTURE_STALE = "structure_fact_stale"
F_DC_ROLE_UNRESOLVED = "dc_role_unresolved_group"
F_L_CLASS_SPLIT = "l_class_conflict"
F_FACT_MISMATCH = "structure_fact_mismatch"
F_FACT_ORPHAN = "structure_fact_orphan"
F_LOOP_POLARITY_CONFLICT = "loop_polarity_conflict"
F_LOOP_POLARITY_AC_ONLY = "loop_polarity_ac_only"
F_COMPOSITE_INTERNAL = "composite_diode_internal"
F_MAIN_PATH_AMBIGUOUS = "main_path_ambiguous"
F_L_OWNER_NAME_ORDER = "l_owner_name_order"
REASON_COMPENSATION_NEEDS_PM = "compensation_internal_needs_overall_pm"


@dataclasses.dataclass(frozen=True)
class Mos:
    """MOS 하나: 이름, kind, 세 단자 넷, S1 DC 역할 문자열과 그 status."""

    name: str
    kind: str
    d: str
    g: str
    s: str
    dc_role: str
    dc_status: str


@dataclasses.dataclass(frozen=True)
class TwoTerm:
    """2단자 원소(수동소자·이상원): 이름, kind, 두 단자 넷."""

    name: str
    kind: str
    a: str
    b: str


@dataclasses.dataclass(frozen=True)
class NetModel:
    """S1 필드를 뷰 계산용으로 풀어 놓은 읽기 전용 모형. `by_gate`·`by_drain`·`by_source` = {넷: Mos tuple}, `by_passive` =
    {넷: TwoTerm tuple}, `mos_by_name` = {이름: Mos}(모두 읽기 전용 매핑, 값 tuple 은 이름순).

    `inputs`·`outputs` = (넷, role) 정렬 tuple. `static_ground` = S1 `ac_ground_class` 가 None 이 아닌 넷.
    `diode_nodes` = gate == drain 인 MOS 의 그 넷(diode 연결 단자, AC 1/gm 노드) ∪ 복합 diode 소자의 gate 넷(41 §1.12.1),
    `composite_mos` = 복합 diode 묶음의 MOS 멤버 이름(셀 분류에서 diode_load), `composite_bundles` = 묶음 멤버(MOS·수동소자 이름) frozenset 의 tuple(루프 (1.6)),
    `composite_internal` = 묶음 멤버의 단자만 닿는 넷(묶음 내부 노드 -- 구동 종류 판정 대상이 아니다, 41 §1.12.1-2)."""

    mos: tuple
    passives: tuple
    sources: tuple
    rails: frozenset
    static_ground: frozenset
    inputs: tuple
    outputs: tuple
    nets: tuple
    by_gate: object
    by_drain: object
    by_source: object
    by_passive: object
    mos_by_name: object
    diode_nodes: frozenset
    composite_mos: frozenset = frozenset()
    composite_bundles: tuple = ()
    composite_internal: frozenset = frozenset()


@dataclasses.dataclass(frozen=True)
class ViewSeed:
    """수집한 뷰 하나. `excite` = (넷, 가중) 이름순, `sense` = 감지 넷 이름순, `source` = 출처 문자열(spec 제약 지문 또는 기본).
    루프 뷰는 `cut` = (끊는 소자, gate 넷)이고 여기 = 그 gate 넷(소자 gate 에만 주입), 감지 = 같은 넷(되먹임으로 돌아온 응답)이다."""

    kind: str
    excite: tuple
    sense: tuple
    source: str
    cut: tuple = ()


@dataclasses.dataclass(frozen=True)
class Finding:
    """`review_needed`·`unsupported_rule_branch` 기록 하나. `code` = 분기 이름, `view` = 뷰 id(전역이면 빈 문자열),
    `subject` = 소자·넷 이름 정렬 tuple, `detail` = 사람이 읽는 근거, `basis` = 계획 규칙·J 항목 ID."""

    code: str
    severity: str
    view: str
    subject: tuple
    detail: str
    basis: tuple = ()


@dataclasses.dataclass(frozen=True)
class CellInfo:
    """MOS 하나의 셀 판독. `dev` = MOS 이름, `kind` ∈ CELL_KINDS, `out` = 출력 단자 넷(CS·CG = drain, CD = source, 그 밖은 빈 문자열),
    `forward` = 출력 단자가 순방향 집합 위(pass 는 묶음 두 노드가 모두 순방향 위), `degeneration` = source 가 신호 넷인 CS."""

    dev: str
    kind: str
    out: str
    forward: bool
    degeneration: bool


@dataclasses.dataclass(frozen=True)
class StructureFact:
    """`structure.json` 의 ratified 사실 하나: 개념, 대상, 값, 승인 기록 id, 근거 넷."""

    concept: str
    subject: str
    value: str
    approval_id: str
    nets: tuple


@dataclasses.dataclass(frozen=True)
class DriveInfo:
    """넷의 입력 노드 구동 종류. `kind` ∈ {voltage, current}, `value_dependent` = 저항·pass 로만 들어와 상속한 값,
    `tap` = 채널 쪽만 순방향을 잇는 노드,
    `basis` = 판정 근거 ∈ {port(여기 포트), source_entry(CD·CG 등 source 로 진입), drain_entry_gate_exit(drain 진입, gate 로만 나감 -> 전압),
    drain_entry_channel_exit(drain 진입, 채널로만 나감 -> 전류), drain_entry_gate_and_channel_exit(둘 다 -> stage 경계, 전압), drain_entry_tap(채널 쪽만 순방향
    -> tap), drain_entry_no_exit(나가는 엣지 없음), mixed_bias_drain(혼재, drain 쪽이 바이어스 전류원 -> 전압), mixed_signal_drain(혼재, 신호 소자 drain ->
    기록), inherit_passive(저항으로만 들어와 이웃 종류 상속), inherit_pass_bundle(pass 로 상속), ratified_fact(structure.json 이 고정), undriven(구동 없음)}."""

    net: str
    kind: str
    value_dependent: bool
    tap: bool
    basis: str


@dataclasses.dataclass(frozen=True)
class OutputDirection:
    """노드 하나의 방향별 전류 공급 셀. `charge`·`discharge` = (소자, β|σ|κ) 이름순, `topology` ∈ {push_pull(두 방향 모두 σ 셀 공급), class_a(한 방향만 σ), none(어느 방향도 σ 없음 -- β·κ 셀만 있거나 공급 셀이 없다)}."""

    net: str
    charge: tuple
    discharge: tuple
    topology: str


@dataclasses.dataclass(frozen=True)
class PassBundle:
    """pass 묶음 하나(같은 두 노드 사이 반대 방향으로 놓인 소자 둘, 셋 이상이면 `pass_group_unsupported`): `members` = 멤버 소자 이름순, `nodes` = 두 노드 이름순."""

    members: tuple
    nodes: tuple


@dataclasses.dataclass(frozen=True)
class Block:
    """블록 하나. `key` = 출력노드 넷 이름의 정렬 tuple, `kind` ∈ {gain, buffer, composite}(composite = 복합 블록이 멤버를 대체한 블록, `CompositeBlock` 기록과 짝),
    `stage` = 시작 셀 입력 넷 `stage_dist` + 1(버퍼 블록은 입력 넷 `stage_dist`, 복합은 멤버 최소),
    `inputs` = 블록 입력 넷, `outputs` = 출력노드, `roles` = (소자, AC 역할) 이름순, AC 역할 ∈ {input(시작 CS·CG), cascode(CG), mirror(미러 입력을 gate 로 읽는 CS), diode_load(소유 노드의 diode 소자),
    pass(pass 묶음), follower(버퍼 블록의 CD), tail_source(= 계획 N3.2-6 tail, 바이어스 전류원이고 drain 이 블록 안 둘 이상 멤버의 source), load(그 밖 블록 소유 노드에 닿는 MOS·수동소자)} --
    계획 N3.2-6 의 input·cascode·follower·pass·load·tail(= 값 tail_source) 에 mirror·diode_load 를 load 의 세분으로 더한 것, `nodes` = 블록 노드 집합(교류접지 제외),
    `impedance` = (출력노드, 등급 ∈ {low, high, value_dependent}) 이름순 -- `node_impedance` 표 그대로(극점 노드와 같은 값),
    `status` ∈ {derived, review_needed}."""

    key: tuple
    kind: str
    stage: int
    inputs: tuple
    outputs: tuple
    roles: tuple
    nodes: tuple
    impedance: tuple
    status: str


@dataclasses.dataclass(frozen=True)
class CompositeBlock:
    """복합 블록 기록(DEC-81). `merge_nodes` = 합류 노드, `members` = 묶인 블록 키(블록마다 한 원소), `inputs`·`outputs` = 묶음의
    바깥 입출력 넷, `paths` = (넷 열, 부호) -- 입력에서 출력까지 셀 부호(CS = -1, 그 밖 +1)의 곱, `cells` = 묶인 MOS 셀 수(격자 곱 Π 의 밑),
    `chain` = 묶은 뒤 블록 DAG 가 stage 단계마다 이어지는 사슬인가, `status`."""

    merge_nodes: tuple
    members: tuple
    inputs: tuple
    outputs: tuple
    paths: tuple
    cells: int
    chain: bool
    status: str


@dataclasses.dataclass(frozen=True)
class PoleNode:
    """극점 노드 하나(교류접지가 아닌 모든 노드). `block` = 소속 블록 키(없으면 빈 tuple), `impedance` = 등급, `drive` = 구동 종류."""

    net: str
    block: tuple
    impedance: str
    drive: str


@dataclasses.dataclass(frozen=True)
class LoopEdge:
    """루프 신호 그래프의 방향 엣지 하나: 출발 넷, 도착 넷, 소자(pass 묶음은 멤버 이름을 '+'로 이은 tuple 의 첫 원소가 아니라 묶음 멤버 tuple),
    종류(EDGE_*)."""

    src: str
    dst: str
    element: object
    etype: str


@dataclasses.dataclass(frozen=True)
class Loop:
    """루프 하나. `nodes` = 사이클 노드 열(이름 정렬 첫 노드에서 시작), `devices` = 지나는 소자 이름 열, `classes` = 분류 tuple
    (둘 이상이면 모두 단다), `cut` = 끊는 점(소자, 게이트 넷) 또는 빈 tuple, `polarity` ∈ {-1, 1, 0}(커패시터를 지나는 사이클은 0 = `ac_only`),
    `cm_pair` = 선언된 차동 출력 포트쌍 대응 여부, `ac_only` = 커패시터를 지나 DC 극성이 없는 사이클(41 §1.12.4)."""

    nodes: tuple
    devices: tuple
    classes: tuple
    cut: tuple
    polarity: int
    cm_pair: bool
    ac_only: bool = False


@dataclasses.dataclass(frozen=True)
class ViewS1v:
    """뷰 하나의 유도 결과 전부(41 §1 출력). 모든 모음은 이름순 tuple 이다.

    `ac_ground` = 이 뷰의 교류접지(정적 + 여기 밖 입력 + (4) 바이어스 종속), `bias_dependent` = (4)로 접지된 넷 ((넷, 사슬 출발 넷 tuple), ...),
    `bias_moving` = 후보였으나 출발 넷이 움직여 접지하지 않은 넷, `virtual_ground` = 기모드 대칭의 자기대응 넷(축약 뷰에서 접지로 본다),
    `signal_nets`·`forward_nets` = 축약 뷰의 신호 넷·순방향 넷, `cells`·`pass_bundles`·`drive_kind`·`dist`(수동소자 포함 거리)·`stage_dist`
    (stage 번호용)·`stage_starts`·`mirror_inputs` = 축약 뷰 기준, `blocks`(이득·버퍼·복합)·`composites`·`pole_nodes`·`output_direction`,
    `loops`·`cuts` = 비축약 뷰 기준(루프는 가상접지를 지나는 되먹임까지 센다), `cm_pair` = 루프 뷰가 선언된 차동 출력 포트쌍을 모두 지나는가(R31), `unreduced_diff` = 축약과 비축약에서 셀 판독이 달라지는
    소자 ((소자 이름, (축약 뷰 셀 kind, forward), (비축약 뷰 셀 kind, forward)), ...) 이름순(둘 중 한쪽이 순방향일 때만)(가상접지가 없으면 빈 tuple), `findings` = 이 뷰의 기록.

    J 공동분석 필드(41 §1.12, 모두 기본값 있음): `main_path` = 주경로 셀 이름순(§1.12.2, 전달 뷰만; 루프 뷰는 빈 tuple), `feedforward` = `FeedforwardCell` 목록,
    `ff_ratio_candidates` = `FfRatioCandidate` 목록, `loop_roles` = 이 전달 뷰의 `LoopRole` 목록, `polarity` = 루프 뷰의 극성(그 뷰의 DC 사이클 극성, §1.12.4,
    루프 뷰 아니면 0), `compensation_candidates` = `ac_only` 사이클의 수동소자 이름(GB5 보상 후보), `ac_ground_exceptions` = 이 뷰에 적용한 `ac_ground_exception` 넷."""

    id: str
    kind: str
    excite: tuple
    sense: tuple
    ac_ground: tuple
    bias_dependent: tuple
    bias_moving: tuple
    virtual_ground: tuple
    signal_nets: tuple
    forward_nets: tuple
    cells: tuple
    pass_bundles: tuple
    drive_kind: tuple
    dist: tuple
    stage_dist: tuple
    stage_starts: tuple
    mirror_inputs: tuple
    blocks: tuple
    composites: tuple
    pole_nodes: tuple
    output_direction: tuple
    loops: tuple
    cuts: tuple
    cm_pair: bool
    unreduced_diff: tuple
    findings: tuple
    main_path: tuple = ()
    feedforward: tuple = ()
    ff_ratio_candidates: tuple = ()
    loop_roles: tuple = ()
    polarity: int = 0
    compensation_candidates: tuple = ()
    ac_ground_exceptions: tuple = ()


@dataclasses.dataclass(frozen=True)
class LoopRole:
    """루프 하나의 역할(41 §1.12). `loop_id` = 루프 뷰면 `loop:<끊는 소자>:<끊는 넷>`, 아니면 사이클 노드 이름 열(이름 정렬 첫 노드에서 시작)의 JSON 배열 텍스트,
    `role` ∈ LOOP_ROLES, `view` = 판정한 전달 뷰 id, `reason` = 근거 문자열(없으면 빈 문자열), `status` ∈ {derived, ratified}(`loop_role` 사실이 일치하면 ratified),
    `approval_id` = 그 사실의 승인 기록 id(ratified 일 때)."""

    loop_id: str
    role: str
    view: str
    reason: str = ""
    status: str = "derived"
    approval_id: str = ""


@dataclasses.dataclass(frozen=True)
class FeedforwardCell:
    """feedforward 묶음 하나(41 §1.12.2). `id` = `<탭>-><merge>`, `tap` = 닿은 주경로 넷, `merge` = 합류 노드(주경로 블록 출력노드), `cells` = 신호 셀 이름순,
    `bias_cells` = 묶음 내부 넷에 drain 이 붙은 바이어스 전류원, `load_cells` = 같은 넷의 diode 부하, `bypassed_blocks` = 우회한 주경로 블록 키(앞 stage 부터),
    `sign` = 탭에서 merge 까지 경로 셀 부호의 곱(CS -1, 그 밖 +1; 경로가 모순이면 0), `status` ∈ {derived, ratified}(묶음의 모든 소자에 `feedforward_cell` 사실이
    일치하면 ratified), `approval_id` = 그 사실들의 승인 기록 id(정렬, `,` 로 이음; ratified 일 때)."""

    id: str
    tap: str
    merge: str
    cells: tuple
    bias_cells: tuple
    load_cells: tuple
    bypassed_blocks: tuple
    sign: int
    status: str = "derived"
    approval_id: str = ""


@dataclasses.dataclass(frozen=True)
class FfRatioCandidate:
    """영점 상쇄 비율 제약 후보(41 §1.12.2-5): `ff` = FeedforwardCell id, `bypassed_block` = 처음 우회한 블록 키, `relation` = 관계 문자열, `source` = 문헌 출처."""

    ff: str
    bypassed_block: tuple
    relation: str
    source: str


@dataclasses.dataclass(frozen=True)
class LClass:
    """L 동치류 하나(40 §3.2 보완 1, LR1): 멤버, 주인 소자, 주인 선택 근거 규칙 이름, status.
    `owner_rule` ∈ {tail_owner(동치류에 tail 하나), tail_first_gain_stage(tail 여럿 -> 첫 전달 뷰 최전단 stage), current_source_member(tail 없음 -> diode 기준
    멤버, 복합 diode 포함), main_path_signal(멤버 중 gain 제약 전달 뷰의 주경로 stage 시작 셀, 41 §1.12.5), name_order(그 밖 -> 이름 정렬 첫 멤버, review_needed),
    ratified_fact(structure.json `l_owner` 사실이 주인을 정함 -- status ratified, 40 §3.2-3 C-3)}."""

    members: tuple
    owner: str
    owner_rule: str
    status: str


@dataclasses.dataclass(frozen=True)
class S1v:
    """SP1 전체 결과. `key` = 7원소 (S1 지문, 뷰 입력 지문, 계수 예산, 규칙 코드 지문, declared 지문, ratified 지문, declared_loop_cuts 지문), `views` = ViewS1v:
    전달 뷰(`transfer:<순번>`, 뷰 수집 순서 = 여기·관측 정렬 순) 다음에 루프 뷰(`loop:<소자>:<gate 넷>`, 끊는 점 (소자, 넷) 정렬 순) -- 결정적이고 이름과 무관하다,
    `l_classes` = LClass(주인 포함), `findings` = 뷰 밖 기록(뷰 수집·declared 대조·structure 사실), `declared` = declared 대조 결과 요약,
    `facts_applied` = 적용한 ratified 사실 (개념, 대상) tuple."""

    key: tuple
    views: tuple
    l_classes: tuple
    findings: tuple
    declared: tuple
    facts_applied: tuple

    @property
    def loop_roles(self):
        """전달 뷰들의 `LoopRole` 전부(뷰 순서, 중복 제거 없음)."""
        return tuple(r for v in self.views for r in v.loop_roles)

    @property
    def all_findings(self):
        """뷰 안팎 기록 전부."""
        return self.findings + tuple(f for v in self.views for f in v.findings)

    @property
    def review_needed(self):
        """severity 가 review_needed 인 기록(GB4 앞 정지 대상, DEC-59 안전망)."""
        return tuple(f for f in self.all_findings if f.severity == SEVERITY_REVIEW)

    @property
    def unsupported(self):
        """severity 가 unsupported_rule_branch 인 기록(`기록만` 분기 -- 항상 탐색 전 정지)."""
        return tuple(f for f in self.all_findings if f.severity == SEVERITY_UNSUPPORTED)
