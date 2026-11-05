"""S2 `dc` 값 형식·어휘·필드 권한표 -- 데이터 선언 모듈 (설계 design_gb7_dc_canonical 2절, 확정 사항 1·2, 계획 N3.3·N3.4).

공개 정의는 frozen dataclass 뿐이다(규칙 A 데이터 선언 모듈). 계산은 다른 파일이 한다.

S2 `dc` 는 S1 과 **같은** core `GraphSnapshot` 위에 산다: 권한표 `S2_WRITERS` = S1 권한표 전부 + 아래 dc 필드 + ss·metric
필드(`SS_WRITES`, writer = metrics 계산 블록 -- metrics CONTRACT 7절 ss_linearize).
`lift_s1` 이 S1 스냅샷을 이 권한표로 옮기고, 그 뒤 dc 계산 블록이 필드를 쓴다(필드마다 writer 하나, 값과 함께 입력
버전 -- 필드가 곧 캐시). graph 레코드 key: node = 넷, device = 원소 이름, graph = `DC_KEY`.
"""
import dataclasses

from gmid_engine.core import WriterTable
from gmid_engine.graph import S1_WRITERS

DC_KEY = "dc"                                          # S2 dc graph 레코드의 유일 key(S1 은 graph.GRAPH_KEY)
KERNEL_KEY = "kernel"                                  # S0 수준 graph/kernel 레코드 key -- 커널 컨텍스트 구조 파생(설계 40 §2.4.7·§2.4.8, v1.9.1 D8)

# ---- 원소 kind 어휘(스키마 낱말) -- graph 가 공개하지 않는 지원 kind 를 여기서 이름 붙인다
RESISTOR = "resistor"
CAPACITOR = "capacitor"
CURRENT_SOURCE = "current_source"

# ---- 노드 writer 티어(계획 N3.4) 와 쓰는 관계
TIER_W0 = "W0"
TIER_W1 = "W1"
TIER_W2 = "W2"
TIER_W3 = "W3"
TIER_W4 = "W4"
REL_RAIL = "rail"                                      # W0: supplies_v
REL_TARGET = "declared_target"                         # W3: spec node_voltage_targets_v
REL_INPUT_DC = "input_dc"                              # W2 (d): spec input_dc 가 선언된 입력 포트
REL_VGS_GATE = "vgs_gate"                              # 쓰기 소자가 source 에서 gate 를 쓴다(diode 면 W1)
REL_VGS_SOURCE = "vgs_source"                          # 쓰기 소자가 gate 에서 source 를 쓴다(소스 추종, W2)
REL_RESISTOR = "resistor_drop"                         # V(far) = V(near) -/+ I*R (W2 (b))
REL_WINDOW = "free_window"                             # W4: θ 의 y 성분 -> 창 안 위치
REL_INPUT_POINT = "input_point"                        # 입력 DC 미선언 차동 입력쌍의 두 포트가 묶인 입력 점(DEC-106): W4 뿌리 하나, F 에 닿으면 KVL 종속

# ---- path_values 관계 종류(봉인 1 입력의 relation[0])
PATH_MOS = "vgs"                                       # MOS 좌표에서 VGS 역산으로 함의한 gate·source 전압
PATH_RESISTOR = "resistor"
PATH_Y = "y"
PATH_FIXED = "fixed"

# ---- 소자 좌표 역할(DEC-88: 쓰기 소자 좌표 = ln IDu, 종속 소자는 VGS 정합 순방향)
COORD_WRITER = "writer"
COORD_DEPENDENT = "dependent"
DEP_PARALLEL = "parallel_vgs"                          # DEC-64 v0: 같은 (gate, source) 평행 엣지
DEP_CYCLE = "cycle_vgs"                                # DEC-64 v1·v2: G_vgs 기본 사이클의 비트리 엣지
DEP_FIXED = "fixed_vgs"                                # gate·source 둘 다 고정 노드
DEP_TREE = "tree"                                      # 쓰기 소자(트리 엣지)

# ---- θ 성분 종류(설계 3.1 5. DOF 표)
THETA_LN_IDU = "ln_idu"
THETA_L = "L"
THETA_Y = "y"
THETA_CURRENT = "current"
THETA_RESISTANCE = "resistance"                        # DC 경로 저항(값 미선언) -- dc_columns 가 읽는다
THETA_CAPACITANCE = "capacitance"                      # [DEC-92] engine 커패시터 -- DC 블록이 읽지 않는다
THETA_SS_RESISTANCE = "ss_resistance"                  # [DEC-92 (3)(b)] DC 전류 0(잎 가지치기) engine 저항 중 구조 규칙 밖
THETA_KINDS = (THETA_CAPACITANCE, THETA_CURRENT, THETA_L, THETA_LN_IDU, THETA_RESISTANCE, THETA_SS_RESISTANCE, THETA_Y)
THETA_PASSIVE_KINDS = (THETA_CAPACITANCE, THETA_SS_RESISTANCE)   # 소신호 회로에만 들어가는 θ(DC 반복 밖, DEC-70)

# ---- [DEC-92 (3)] 영점 상쇄 저항 구조 규칙이 R 을 정하지 못한 사유(`ZeroCancel.reason`, None = 구조 규칙으로 정함)
ZC_NO_CAPACITOR = "network_without_capacitor"          # 저항이 든 수동 망에 커패시터가 없다(RC 영점 망이 아니다)
ZC_MULTIPLE_RESISTORS = "network_multiple_resistors"   # 망에 저항이 둘 이상 -- 1/Σgm 을 어느 저항에 둘지 정해지지 않는다
ZC_RESISTOR_END = "resistor_end_not_unique"            # 저항의 두 단자 중 망 경계 넷이 정확히 하나가 아니다
ZC_NO_CELL = "no_cs_cell"                              # 망이 gate–drain 을 잇는 CS 셀이 없다
ZC_MIXED_DIRECTION = "cs_cell_direction_mixed"         # 저항 끝 넷이 어떤 셀에는 drain, 다른 셀에는 gate

# ---- 봉인 항목(계획 N3.6 표 순서 -- 항목 번호 = 이 tuple 의 위치 + 1)
SEAL_ITEM_NAMES = ("node_conflict", "vgs_match", "kcl", "versions", "writer_unique", "bulk_reverse", "saturation",
                   "kvl_branch", "conduction")
SEAL_NODE_CONFLICT = SEAL_ITEM_NAMES.index("node_conflict") + 1
SEAL_VGS_MATCH = SEAL_ITEM_NAMES.index("vgs_match") + 1
SEAL_KCL = SEAL_ITEM_NAMES.index("kcl") + 1
SEAL_VERSIONS = SEAL_ITEM_NAMES.index("versions") + 1
SEAL_WRITER_UNIQUE = SEAL_ITEM_NAMES.index("writer_unique") + 1
SEAL_BULK_REVERSE = SEAL_ITEM_NAMES.index("bulk_reverse") + 1
SEAL_SATURATION = SEAL_ITEM_NAMES.index("saturation") + 1
SEAL_KVL_BRANCH = SEAL_ITEM_NAMES.index("kvl_branch") + 1
SEAL_CONDUCTION = SEAL_ITEM_NAMES.index("conduction") + 1   # [r8] 전도 여유: VGS=0 누설 ≤ ε·ID

# ---- 봉인 상태
SEAL_PASS = "pass"
SEAL_FAIL = "fail"
SEAL_UNDEFINED = "undefined"
REPORT_SEALED = "sealed"
REPORT_VIOLATED = "violated"
REPORT_UNDEFINED = "undefined"

# ---- 실패 사유(detail reason) -- 정지(StructureUnresolvedError)는 graph 와 같은 reason 키 + rule_branch
BRANCH_RESISTOR_CYCLE = "dc_resistor_cycle"
BRANCH_INPUT_CM_UNDEFINED = "input_cm_undefined"       # 입력 DC 미선언 + 입력 포트가 차동쌍 하나가 아님(DEC-106): 탐색 전 정지
BRANCH_INPUT_TARGET_ONE_PORT = "input_target_one_port"   # 입력 DC 미선언 + 차동 입력 두 포트 중 한 포트만 node_voltage_targets_v 선언: 입력 점이 안 묶여 ΔV 가 θ 함수(DEC-106): 탐색 전 정지
BRANCH_MOS_ZERO_CURRENT = "mos_zero_current_structural"
BRANCH_OFF_ONLY_NODE = "off_only_node"                   # `off` 소자 d·s 가 닿는 비고정 넷 중 off 채널 밖 전압 결정 DC 요소(켜진 채널·R·L·전압원)로 고정 넷에 닿지 않는 넷: 전도 경로 없이 θ 변수가 되는 것을 막는다(EO-1 범위 4)
BRANCH_ORIENTATION = "mos_orientation_unsupported"
REASON_DECLARED_KCL = "declared_source_kcl_conflict"
REASON_EMPTY_WINDOW = "empty_window"
REASON_TOL_UNDEFINED = "tol_v_undefined"
REASON_VDSAT_MISSING = "lut_vdsat_column_missing"
REASON_LUT_QUERY = "lut_query_failed"
REASON_NO_ROOT = "no_root_in_window"
REASON_STRICT_RECHECK = "strict_recheck_residual"     # 다변수 SCC 수렴 뒤 strict 검증 바퀴 잔차 > tol
REASON_NEWTON_START = "newton_start_outside_domain"    # 감쇠 Newton 시작점이 정의역 밖(LUT 조회 실패·빈 창)
REASON_NEWTON_SINGULAR = "newton_singular"             # 야코비안 LU 영 피벗
REASON_NEWTON_LINE_SEARCH = "newton_line_search"       # 역추적 선 탐색이 잔차를 줄이는 α 를 못 찾음
REASON_NEWTON_CAP = "newton_iteration_cap"             # Newton 반복이 K_max 에 닿음
SCC_GAUSS_SEIDEL = "gauss_seidel"                      # SccLog.method
SCC_NEWTON = "newton"
SCC_BISECTION = "bisection"
SCC_DIRECT = "direct"

# ---- 남은 동률(구조 색이 같은 후보)을 이름 순서로 깬 결정의 종류(`TieBreak.decision`)
INPUT_STATUS_MEASURED = "measured"                     # `Window.input_status`(설계 41 4.7-2): 입력 포화 창을 재고 되풀이가 tol 안에서 수렴 / cfg: 선형 감도 끝을 쟀다
INPUT_STATUS_UNSETTLED = "unsettled"                   # 창은 잰 해에서 쟀으나 되풀이가 k_max 안에 수렴하지 않았거나 tol 미정 (커널 창 전용 -- card WB-1 이 지운다)
INPUT_STATUS_UNMEASURED = "unmeasured"                 # 창을 잴 수 없다(커널 뿌리 항목 / cfg 자기 측정 실패)
TIE_KRUSKAL = "writer_edge"                           # 같은 (순위, 구조 색) MOS·저항 엣지 묶음이 트리/비트리로 갈림
TIE_ROOT = "w4_root"                                   # F 없는 성분의 W4 뿌리 후보가 같은 구조 색
TIE_CURRENT_PIVOT = "current_pivot"                    # 같은 구조 색 원소 열이 θ 전류 기저/종속으로 갈림

# ---- 필드 writer(= 계산 블록 이름)
DC_REGION_DECL_WRITER = "dc_region_decl"                # S0: device.region_decl (의도 영역 선언 술어 필드, 쓰기 계획 앞)
DC_RAILS_WRITER = "dc_rails"
DC_CURRENT_BASIS_WRITER = "dc_current_basis"
DC_WRITER_PLAN_WRITER = "dc_writer_plan"
DC_SCC_ORDER_WRITER = "dc_scc_order"
DC_THETA_SCHEMA_WRITER = "dc_theta_schema"
KERNEL_CONTEXT_WRITER = "kernel_context"               # graph/kernel: fixed_values·resistor_values·l_ties (`build_kernel_context` 의 계산 블록)
DC_CURRENTS_WRITER = "dc_currents"
DC_LENGTHS_WRITER = "dc_lengths"
DC_COLUMNS_WRITER = "dc_columns"
DC_WIDTHS_WRITER = "dc_widths"
DC_TOLERANCES_WRITER = "dc_tolerances"
DC_SEAL_NODE_CONFLICT_WRITER = "dc_seal_node_conflict"
DC_SEAL_VGS_MATCH_WRITER = "dc_seal_vgs_match"
DC_SEAL_KCL_WRITER = "dc_seal_kcl"
DC_SEAL_BULK_WRITER = "dc_seal_bulk_reverse"
DC_SEAL_REGION_WRITER = "dc_seal_region"                # 봉인 7·9: 소자마다 공용 영역 판정 한 번 (EO-1 범위 4)
DC_SEAL_KVL_WRITER = "dc_seal_kvl_branch"
DC_SEAL_REPORT_WRITER = "dc_seal_report"

# ---- 블록별 writes (reads 는 각 블록 파일에 둔다)
DC_WRITES = (
    (DC_REGION_DECL_WRITER, (("device", "region_decl"),)),
    (DC_RAILS_WRITER, (("node", "dc_rail_v"),)),
    (DC_CURRENT_BASIS_WRITER, (("graph", "dc_current_basis"),)),
    (DC_WRITER_PLAN_WRITER, (("node", "dc_writer"), ("device", "dc_coord"), ("graph", "dc_tie_breaks"), ("device", "dc_self_referential"))),
    (KERNEL_CONTEXT_WRITER, (("graph", "fixed_values"), ("graph", "resistor_values"), ("graph", "l_ties"))),
    (DC_SCC_ORDER_WRITER, (("graph", "dc_scc_order"), ("node", "dc_column_nbrs"))),
    (DC_THETA_SCHEMA_WRITER, (("graph", "theta_schema"),)),          # graph/kernel: theta_schema (옛 graph/dc: dc_theta_schema 를 옮김, v1.9.1 D8)
    (DC_CURRENTS_WRITER, (("device", "dc_current"), ("device", "dc_drop_current"))),
    (DC_LENGTHS_WRITER, (("device", "dc_L"),)),
    (DC_COLUMNS_WRITER, (("node", "dc_v"), ("node", "dc_path_values"), ("node", "dc_window"),
                         ("device", "dc_ln_idu"), ("graph", "dc_scc_log"))),
    (DC_WIDTHS_WRITER, (("device", "dc_op"),)),
    (DC_TOLERANCES_WRITER, (("device", "dc_tol_v"), ("device", "dc_gm"))),
    (DC_SEAL_NODE_CONFLICT_WRITER, (("graph", "dc_seal_1"),)),
    (DC_SEAL_VGS_MATCH_WRITER, (("graph", "dc_seal_2"),)),
    (DC_SEAL_KCL_WRITER, (("graph", "dc_seal_3"),)),
    (DC_SEAL_BULK_WRITER, (("graph", "dc_seal_6"),)),
    (DC_SEAL_REGION_WRITER, (("graph", "dc_seal_7"), ("graph", "dc_seal_9"))),
    (DC_SEAL_KVL_WRITER, (("graph", "dc_seal_8"),)),
    (DC_SEAL_REPORT_WRITER, (("graph", "dc_seal_report"),)),
)
# ---- S2 ss·metric 필드(writer = MOD5 계산 블록, metrics CONTRACT 7절). 권한표가 S2 한 곳이라 여기서 선언한다
# (sizing 은 metrics 를 import 하지 않는다 -- 이름은 스키마 낱말이다). graph 레코드 key: device = 소자, graph = METRICS_KEY.
METRICS_KEY = "metrics"
SS_DEV_WRITER = "ss_dev"                               # device.ss_dev: 봉인 op 의 소신호 선형화(MOS 마다)
METRICS_SS_WRITER = "metrics_ss"                       # graph.metrics_ss: 뷰 계 MNA -> 제약 metric 묶음
METRICS_DC_WRITER = "metrics_dc"                       # graph.metrics_dc: 레일 전류·전력·탐색 축 면적 묶음 + graph.gate_area_m2·power_resolution_w(설계 40 §2.4.8)
PASSIVE_VALUES_WRITER = "passive_values"               # device.passive_value: GB5 수동소자 값(spec ∪ θ ∪ 영점 상쇄 R = 1/Σdc_gm, 설계 40 §2.4.8)
METRICS_AUX_WRITER = "metrics_aux"                     # graph.metrics_aux: offset·미러비·스윙·ICMR·FF 비 metric 묶음 + 블록 잔차 보고 (U7)
SS_CIRCUIT_WRITER = "ss_circuit"                       # graph.ss_circuit: S2 열 -> 정수 인덱스 소신호 회로(`SsCircuit`) -- 조립 자리 하나 (card IT-2c)
SS_NODAL_WRITER = "ss_nodal"                           # graph.ss_nodal: 봉인점 소신호 DC 극한 노달 계(`NodalSystem`: G·g_bound·인수분해) (card IT-2c)
SS_OFF_OP_WRITER = "ss_off_op"                       # device.off_op: `off` 선언 소자의 동작점 (EO-1 범위 4)
SS_OFF_DELTA_WRITER = "ss_off_delta"                   # graph.ss_off_delta: off 소자 전류 효과의 1차 ΔV (EO-1 범위 4)
ICM_CONFIG_WRITER = "icm_config"                       # node.dc_window_cfg + graph.icm_config: ICMR 측정 구성·창·V_cm 칸 (card IT-2c)
SS_WRITES = (
    (SS_DEV_WRITER, (("device", "ss_dev"),)),
    (METRICS_SS_WRITER, (("graph", "metrics_ss"),)),
    (METRICS_DC_WRITER, (("graph", "metrics_dc"), ("graph", "gate_area_m2"), ("graph", "power_resolution_w"))),
    (PASSIVE_VALUES_WRITER, (("device", "passive_value"),)),
    (METRICS_AUX_WRITER, (("graph", "metrics_aux"),)),
    (SS_CIRCUIT_WRITER, (("graph", "ss_circuit"),)),
    (SS_NODAL_WRITER, (("graph", "ss_nodal"),)),
    (ICM_CONFIG_WRITER, (("node", "dc_window_cfg"), ("graph", "icm_config"))),
)
# EO-1 범위 4: `off` 선언 소자 층의 필드 -- ss 층(위 SS_WRITES)과 별도 묶음(off 선언이 있을 때만 쓰인다)
SS_OFF_WRITES = (
    (SS_OFF_OP_WRITER, (("device", "off_op"),)),
    (SS_OFF_DELTA_WRITER, (("graph", "ss_off_delta"),)),
)
S2_WRITERS = WriterTable(
    tuple((kind, field, writer) for (kind, field), writer in S1_WRITERS.entries)
    + tuple((kind, field, writer) for writer, writes in DC_WRITES + SS_WRITES + SS_OFF_WRITES for kind, field in writes)
)


@dataclasses.dataclass(frozen=True)
class DcInputs:
    """GB7 이 읽는 사람 선언(spec)의 투영. `supplies_v` = ((레일, V), ...) 이름순, `input_dc_v` = 입력 포트 공통 DC(V) 또는
    None(미선언·engine·결정 대기 -> W4, 입력 포트인 뿌리의 y 키 = 그 뿌리 넷), `node_targets` = ((넷, V), ...) W3, `element_values` =
    ((원소, 값 또는 None), ...) 저항(Ω)·이상 전류원(A), `regions` = 의도 영역 선언 `RegionDecl` tuple(이름순, triode·off),
    `pending` = 결정 대기로 '미선언' 취급한 칸 ((경로, 결정 ID), ...), `engine_elements` = spec 값 mode 가 `engine` 인 원소
    이름(정렬) -- 그중 수동소자가 DEC-92 θ 연속 성분·구조 규칙 대상이다(결정 대기 원소는 들지 않는다)."""

    supplies_v: tuple
    input_dc_v: object = None
    node_targets: tuple = ()
    element_values: tuple = ()
    regions: tuple = ()
    pending: tuple = ()
    engine_elements: tuple = ()


@dataclasses.dataclass(frozen=True)
class OrderHints:
    """DEC-95 (3) 종속 소자 선택 앞 단계 입력 (설계 40 §3.7-4) -- 구조 색·이름보다 먼저 쓰이는 순서 정보.
    `independent` = ratified 선택(`structure.json`)이 독립(트리)으로 정한 MOS 이름, `gm_required` = GB5 가 gm 을 요구하는 MOS 이름,
    `stage` = ((MOS, S1v stage 번호), ...) -- 번호가 큰(뒤 stage) 소자가 독립으로 남는다. 셋 다 이름은 소자 식별일 뿐 순서는 값이
    정한다. 출처는 U1 의 S1v·ratified 로더이고 비어 있으면(`NO_ORDER_HINTS`) 구조 색·이름 순서 그대로다."""

    independent: tuple = ()
    gm_required: tuple = ()
    stage: tuple = ()


NO_ORDER_HINTS = OrderHints()


@dataclasses.dataclass(frozen=True)
class LutAccess:
    """계산 블록 추가 인자로 넘기는 LUT 손잡이. `memo` = lut.LutMemo(graph 밖 유일 memo), `w_keys` = ((kind, w_key), ...)
    -- 레이아웃 전 사이징이 쓰는 폭 슬라이스. 지문(`__canonical__`)은 (LUT 내용 지문, w_keys) 라서 같은 LUT·같은 슬라이스면
    블록 입력 버전이 같고, memo 상태(캐시)는 결과에 영향이 없어 지문에 들지 않는다."""

    memo: object
    w_keys: tuple

    def __canonical__(self):
        return (self.memo.lut.fp, self.w_keys)


@dataclasses.dataclass(frozen=True)
class CurrentTerm:
    """원소 전류 하나의 선형식 항: 원천 원소 `source` 의 전류 × (num/den)."""

    source: str
    num: int
    den: int


@dataclasses.dataclass(frozen=True)
class CurrentBasis:
    """원소 단위 KCL 해 공간(θ 무관). `ends` = ((원소, from 넷, to 넷), ...) -- 양의 전류가 from -> to 로 흐르는 방향
    (nmos d->s, pmos s->d, 2단자 t0->t1). `mos` = MOS 원소, `free` = θ 전류 성분 원소(독립 기저), `fixed` = ((원소, A), ...)
    값 선언 이상 전류원, `rows` = ((원소, (CurrentTerm, ...)), ...) 모든 DC 원소의 전류 = Σ 항, `pruned` = 잎 가지치기된
    저항(전류 0), `resistors` = DC 경로 저항(가지치기 제외), `ties` = 같은 구조 색 열이 기저/종속으로 갈린 기록(TieBreak)."""

    ends: tuple
    mos: tuple
    free: tuple
    fixed: tuple
    rows: tuple
    pruned: tuple
    resistors: tuple = ()
    ties: tuple = ()


@dataclasses.dataclass(frozen=True)
class TieBreak:
    """구조 색으로 가르지 못한 동률을 이름 순서로 깬 기록. `decision` ∈ TIE_*, `candidates` = 같은 키의 후보(이름순),
    `chosen` = 이름 순서로 고른 쪽(writer·뿌리·θ 기저 등)."""

    decision: str
    candidates: tuple
    chosen: tuple


@dataclasses.dataclass(frozen=True)
class NodeWrite:
    """노드 하나의 writer. `tier` ∈ W0..W4, `relation` = 쓰는 관계, `element` = 쓰는 원소(MOS·저항) 또는 None,
    `known` = 읽는 아는 쪽 노드 또는 None, `y_key` = W4 의 θ y 키 또는 None, `order` = 쓰기 계획 순번(결정론)."""

    tier: str
    relation: str
    element: object = None
    known: object = None
    y_key: object = None
    order: int = 0


@dataclasses.dataclass(frozen=True)
class DeviceCoord:
    """MOS 좌표 역할. `role` ∈ {writer, dependent}, `relation` ∈ {tree, parallel_vgs, cycle_vgs, fixed_vgs},
    `partner` = parallel_vgs 이면 같은 (gate, source) 의 쓰기 소자, 아니면 None."""

    role: str
    relation: str
    partner: object = None


@dataclasses.dataclass(frozen=True)
class ColumnNeighbor:
    """기둥 하나에서 노드의 이웃. `rails` = (출발 레일, 도착 레일)(S1 기둥 방향), `pred`·`succ` = 경로 앞·뒤 노드,
    `position`·`length` = 경로 위 위치(출발 레일 0, 도착 레일 length)."""

    rails: tuple
    pred: str
    succ: str
    position: int
    length: int


@dataclasses.dataclass(frozen=True)
class SccEntry:
    """순환 블록 하나(위상 순서). `nodes` = 쓰기 계획 순서, `cyclic` = 반복 필요(크기 > 1 또는 자기 참조),
    `devices` = 단자(d·g·s)가 이 노드들에 닿는 MOS(허용오차 조회 대상)."""

    index: int
    nodes: tuple
    cyclic: bool
    devices: tuple


@dataclasses.dataclass(frozen=True)
class ThetaSchema:
    """θ 성분 목록 ((kind, key), ...) 정렬 -- 설계 3.1 5. DOF 표. `current_cone` = θ 전류 정의역: MOS 마다
    (MOS, (CurrentTerm, ...)) -- 그 MOS 전류 = Σ (num/den)·(θ 전류 또는 고정값) 이 > 0 이어야 한다(KCL 기저에서 유도,
    `fixed` = 그 식이 읽는 값 선언 이상원 ((원소, A), ...)). 기저 원소 자신이 MOS 면 그 행은 θ_I > 0 상자 하한이 된다.
    `zero_cancel` = DC 전류 0(잎 가지치기) engine 저항마다 `ZeroCancel`(이름순) -- reason None 이면 θ 가 아니라 봉인 스냅샷
    gm 의 파생값(DEC-92 (3)(a)), 아니면 `ss_resistance` θ 성분(DEC-92 (3)(b))."""

    components: tuple
    current_cone: tuple = ()
    fixed: tuple = ()
    zero_cancel: tuple = ()


@dataclasses.dataclass(frozen=True)
class ZeroCancel:
    """DEC-92 (3) 영점 상쇄 저항 구조 규칙의 판정 하나(연결만으로, θ 무관). `resistor` = 저항, `end_net` = 저항 단자 중 수동
    망 경계 넷(없거나 둘이면 None), `far_nets` = 망의 나머지 경계 넷(정렬), `cells` = S(이름순 -- source 가 교류접지이고
    {gate, drain} 이 {end_net, far_net 하나} 인 MOS), `reason` = None(R = 1/Σ_{c∈S} gm_c) 또는 `ZC_*` 사유(θ 폴백)."""

    resistor: str
    end_net: object
    far_nets: tuple
    cells: tuple
    reason: object = None


@dataclasses.dataclass(frozen=True)
class Theta:
    """후보 θ. `values` = (((kind, key), float), ...) 정렬. `check_theta` 가 만든다."""

    values: tuple


@dataclasses.dataclass(frozen=True)
class PathValue:
    """노드에 닿는 관계 하나가 함의하는 그 노드 전압. `relation` = (관계 종류, 원소 또는 y 키), `value` = V."""

    relation: tuple
    value: float


@dataclasses.dataclass(frozen=True)
class Window:
    """노드 창 [lo, hi](V) -- 커널 `node.dc_window`(W4 뿌리 항목, 설계 41 4.7-2)와 측정 구성 `node.dc_window_cfg`(입력 포트 항목, `constraints` 0)의 값 꼴.
    `constraints` = 창을 만든 인접 전도 MOS 순서 제약 수(0 이면 레일 전압 범위). `input_status` = None(입력 포트가 아닌 W4 뿌리) 또는 `INPUT_STATUS_*` 중 하나
    (cfg 는 measured·unmeasured 뿐), `tol_v` = 그 창을 잰 해의 tolerance(cfg: 봉인점 `device.dc_tol_v` 최솟값, 미정이면 None).
    (`op_mismatch`·`status_detail` 은 EO-1 묶음 몫 -- 사용자 결정 O-98.)"""

    lo: float
    hi: float
    constraints: int
    input_status: object = None
    tol_v: object = None


@dataclasses.dataclass(frozen=True)
class SccLog:
    """순환 블록 풀이 기록. `iterations` = 반복 수, `deltas` = 반복별 최대 변화(Newton 이면 반복별 ‖r‖∞), `tol` = 마지막
    허용오차, `k_max` = 상한, `method` ∈ {direct, bisection, gauss_seidel, newton}, `fallback` = Newton 으로 바꾼 경우 그 전
    Gauss-Seidel 의 (반복 수, 마지막 수축비 q 또는 None, Δ 열), 아니면 None."""

    index: int
    nodes: tuple
    iterations: int
    deltas: tuple
    tol: object
    k_max: object
    method: str = SCC_DIRECT
    fallback: object = None


@dataclasses.dataclass(frozen=True)
class DeviceOp:
    """MOS 동작점(S2 dc). 전압은 크기(LUT 부호 규약), `current` = ID(A, 전도 방향 양수), `ln_idu` = 좌표(DEC-88),
    `gm_id` = 노드 전압 점의 순방향 LUT 값(파생 보고), `W` = ID·L/IDu(좌표), `idu_forward` = 노드 전압 점의 순방향 LUT IDu
    (봉인 2·3·8 이 읽는다 -- 같은 순방향 조회를 항목마다 다시 하지 않는다)."""

    kind: str
    current: float
    ln_idu: float
    gm_id: float
    L: float
    W: float
    vgs: float
    vds: float
    vsb: float
    w_key: int
    idu_forward: float


@dataclasses.dataclass(frozen=True)
class SealItem:
    """봉인 항목 결과. `status` ∈ {pass, fail, undefined}, `magnitude` = 최대 위반 크기(단위는 항목), `tol` = 그 허용오차,
    `margin` = magnitude/tol(무차원) 또는 None, `devices`·`nodes` = 위반(또는 미정) 대상, `detail` = 키 정렬 쌍 tuple."""

    item: int
    status: str
    magnitude: object = None
    tol: object = None
    margin: object = None
    devices: tuple = ()
    nodes: tuple = ()
    detail: tuple = ()


@dataclasses.dataclass(frozen=True)
class SealReport:
    """봉인 8항목 묶음. `items` = item 순, `status` ∈ {sealed, violated, undefined}."""

    items: tuple
    status: str


@dataclasses.dataclass(frozen=True)
class SealedSnapshot:
    """봉인 8항목이 모두 pass 인 S2 스냅샷만 감싸는 타입(DEC-67). `ss`·`ls` 계산은 이 타입만 받는다."""

    snapshot: object
    report: SealReport


@dataclasses.dataclass(frozen=True)
class KernelContext:
    """S0 당 1회 만드는 평가 커널 컨텍스트 -- **참조만** 담는다(설계 40 §2.4.7 `KernelContext` 행). `base` = S0 수준 스냅샷(S1 + 쓰기 계획 블록 + 커널 구조
    파생 필드 `graph/kernel: theta_schema·fixed_values·resistor_values·l_ties`, 탐색 컨텍스트가 만든 뒤에는 그 S0 수준 필드도), `inputs` = DcInputs(spec 파싱 결과),
    `lut` = LutAccess(LUT memo 와 폭 키). 설계 값(θ 스키마·고정 노드·저항 값·L 묶음·계획 블록 입력 버전)은 사본으로 두지 않고 `base` 필드와
    `base.block_version` 에서 읽는다. `donors`·`counters` = 호출자가 `search.open_run()` 으로 만든 실행 하나의 블록 결과 색인·계수(참조만 -- 과도기 칸,
    설계 40 §2.4.5 '전달'. 커널 단계의 모든 블록 호출이 이 두 객체로 부른다)."""

    base: object
    inputs: DcInputs
    lut: LutAccess
    donors: object
    counters: object


@dataclasses.dataclass(frozen=True)
class DcEvaluation:
    """`size_and_seal` 결과. `snapshot` = 봉인 결과까지 쓴 S2 스냅샷, `report` = SealReport,
    `sealed` = 8항목 모두 pass 면 SealedSnapshot, 미정 항목이 있으면 None(실패는 예외)."""

    snapshot: object
    report: SealReport
    sealed: object = None
