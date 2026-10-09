"""출발 구간 값 형식·어휘 -- 데이터 선언 모듈 (설계 41 §6, 40 §11 U13, D-SIa~g).

공개 정의는 frozen dataclass 와 어휘 상수뿐이다(규칙 A 데이터 선언 모듈). 계산은 `iv_*`·`macro_poles`·`dominant_node`·`start_intervals` 가 한다.

* 경계 어휘: `Bound(quantity, side, source, value)` -- 한 소자의 gm/ID(1/V) 또는 L(m) 경계 하나와 그 출처(식 이름). 구간은 경계들의 교집합이다.
* 충돌 `StartConflict` (41 §6.6): 하한 > 상한, 전류 > 상자 상한, 면적 추정 > 예산(보고만). **충돌이 있어도 구간을 자르지 않는다** -- 양 끝 후보를 '충돌' 표시와 함께 낸다.
* 비활성 `inactive`: 입력이 없어(선언 제약·LUT 데이터·U9 인증 값 없음) 계산하지 않은 경계 -- ((경계 식 이름, 사유), ...). 조용히 빠지지 않고 보고에 남는다.
* `StartRow` = 소자 하나의 보고 행(41 §6.6 `start_intervals[{device, gm_id_lo/hi/chosen, L_lo/hi/chosen, bin, I_start, sources, inactive_reasons, conflicts}]`).
"""
import dataclasses
import math

PM_FLOOR_DEG = math.degrees(math.atan(1))   # PM 목표가 없을 때의 경계: 2극점 근사 PM = atan(f_np/GBW) 에서 비주극점이 UGF 에 놓인 f_np = GBW 일 때의 값(45°)
QUANTITY_GM_ID = "gm_id"
QUANTITY_L = "L"
QUANTITY_AREA = "area"
SIDE_LO = "lo"
SIDE_HI = "hi"
EDGE_VDS = "vds"            # 헤드룸 경로 엣지 종류(U9 `headroom_bound` 어휘)
EDGE_VGS = "vgs"
# ---- 경계 식 이름(보고 `sources`·`inactive` 에 쓰인다; 41 절 번호)
SRC_LUT_RANGE = "lut_gm_id_range"                 # 곡선 분지 끝(gm/ID 정점·최소)
SRC_HEADROOM_VDSAT = "headroom_vdsat_6.2"         # 41 §6.2 VDSAT 예산 -> gm/ID 하한
SRC_HEADROOM_VGS = "headroom_vgs_6.2"             # 41 §6.2 VGS 예산 -> gm/ID 하한
SRC_SPEED_FT = "speed_ft_6.3"                     # 41 §6.3 f_T >= f_np -> gm/ID 상한
SRC_SPEED_L = "speed_l_6.4_4"                     # 41 §6.4-4 f_T(gm/ID_lo, L) >= f_np -> L 상한
SRC_GAIN_L = "gain_l_6.4_1"                       # 41 §6.4-1 이득 L 하한
SRC_MATCH_L = "matching_l_6.4_2"                  # 41 §6.4-2 절대 offset L 하한
SRC_OFFSET_GUARD = "offset_guard_6.4_2a"          # 41 §6.4-2a 부하 gm/ID 상한
SRC_NOISE_GUARD = "noise_guard_7.5"               # 41 §7.5 열잡음 가드 부하 gm/ID 상한
SRC_NOISE_FLICKER_L = "flicker_l_6.4_3"           # 41 §6.4-3 1/f L 하한
SRC_NOISE_THERMAL_C = "thermal_c_7.5"             # 41 §7.5 열잡음 C_eff 하한
SRC_AREA_L = "area_l_6.4_5"                       # 41 §6.4-5 면적 L 상한
SRC_AREA_GM_ID = "area_gm_id_6.4_5"               # 41 §6.4-5 면적 -> gm/ID 상한(IDu 하한)
SRC_W_MIN = "w_min_gm_id"                         # W >= W_min(PDK 최소 finger 폭) -> gm/ID 상한(IDu 하한)
SRC_LUT_DOMAIN = "lut_inverse_domain"             # lut/CONTRACT 3.1 vgs_for_current_density 역산이 받는 ln IDu 창 -> gm/ID 하한·상한
SRC_LUT_L = "lut_l_range"                         # LUT L 격자 끝
SRC_L_CLASS = "l_class_intersection"              # L 동치류 교집합
# ---- 비활성 사유
WHY_NO_TARGET = "constraint_not_declared"
WHY_NO_LUT = "lut_data_unavailable"
WHY_NO_RAILS = "rail_potentials_undeclared"
WHY_NO_CERT = "u9_value_not_certified"
WHY_NO_DOMINANT = "dominant_node_undefined"
WHY_NO_GBW = "gbw_target_missing"
WHY_NO_PM = "pm_target_missing"
WHY_NO_CURRENT = "stage_current_unavailable"
WHY_PENDING_DEP = "depends_on_unmerged_unit"
# ---- 매크로 기록 코드(41 §6.5)
MACRO_NONCONVERGENT = "macro_nonconvergent"
MACRO_ROOT_MISSING = "macro_root_missing"
MACRO_INACTIVE = "macro_inactive"


@dataclasses.dataclass(frozen=True)
class Bound:
    """경계 하나. `quantity` ∈ QUANTITY_GM_ID·QUANTITY_L, `side` ∈ SIDE_LO·SIDE_HI, `source` = SRC_*, `value` = 값(gm/ID 1/V, L m)."""

    quantity: str
    side: str
    source: str
    value: float


@dataclasses.dataclass(frozen=True)
class StartConflict:
    """충돌 레코드(41 §6.6). `device` = 소자 이름(또는 L 동치류 주인), `quantity` ∈ QUANTITY_*, `bounds` = ((출처, 값), ...), `gap` = 어긋난 크기(같은 단위)."""

    device: str
    quantity: str
    bounds: tuple
    gap: float


@dataclasses.dataclass(frozen=True)
class DeviceInfo:
    """MOS 하나의 구조 사실. `owner` = L 주인 소자 이름(S1v L 동치류 주인과 자기동형 묶음 대표를 따라간 θ L 성분의 소자, 둘 다 아니면 자기 이름), `colour` = 구조 색 순위
    (순회·합산 순서를 이름이 아니라 이 순위로 정한다), `group` = 같은 VGS 묶음(쓰기 계획 `parallel_vgs` 종속 -- 미러 출력 등 gate–source 전압이 같은 소자)의 뿌리 소자 이름: 묶음 멤버는 같은 gm/ID 를
    가진다(같은 kind 면 IDu 도 같다)."""

    name: str
    kind: str
    w_key: object
    drain: str
    gate: str
    source: str
    bulk: object
    owner: str
    colour: int
    group: str


@dataclasses.dataclass(frozen=True)
class StartRow:
    """소자 하나의 출발 구간 행(41 §6.6). 값이 없으면 None. `bin` = 선택 L 이 든 L 칸 index, `i_start`·`ln_idu`·`w_m` = 출발 전류(A)·ln IDu·폭 추정(m),
    `sources` = (Bound, ...), `inactive_reasons` = ((경계 식, 사유), ...), `conflicts` = (StartConflict, ...)."""

    device: str
    kind: str
    gm_id_lo: object
    gm_id_hi: object
    gm_id_chosen: object
    l_lo: object
    l_hi: object
    l_chosen: object
    bin: object
    i_start: object
    ln_idu: object
    w_m: object
    sources: tuple
    inactive_reasons: tuple
    conflicts: tuple


@dataclasses.dataclass(frozen=True)
class MacroResult:
    """매크로 모델 풀이 결과(41 §6.5). `gm` = ((블록 키, gm_i S), ...), `cap_values` = ((소자, F), ...) 보상 커패시터 출발값, `resistor_values` = ((소자, Ω), ...),
    `ugf_hz`·`pm_deg` = 마지막 풀이의 값, `sweeps` = 한 바퀴 수, `records` = ((코드, 상세 쌍들), ...) -- `macro_nonconvergent`·`macro_root_missing`·`macro_inactive`,
    `poles_hz` = 마지막 풀이의 극점 주파수(Hz, 오름차순)."""

    gm: tuple
    cap_values: tuple
    resistor_values: tuple
    ugf_hz: object
    pm_deg: object
    sweeps: int
    records: tuple
    poles_hz: tuple


@dataclasses.dataclass(frozen=True)
class StartRung:
    """출발 사다리의 한 칸: 구간 안 위치 `t`(0 = gm/ID 하한 끝, 1 = 상한 끝)에서의 출발 θ. `theta` = ((성분, 값), ...), `cells` = ((MOS, L 칸 index), ...), `current_ref` = ((MOS, A), ...)
    -- `StartIntervals` 의 같은 이름 필드와 같은 뜻."""

    t: float
    theta: tuple
    cells: tuple
    current_ref: tuple


@dataclasses.dataclass(frozen=True)
class StartIntervals:
    """`start_intervals` 결과(41 §6.6 보고 표 + 층 0 입력).

    `rows` = StartRow tuple(색 순서), `conflicts` = StartConflict tuple, `inactive` = ((경계 식, 사유), ...) 회로 전체 비활성, `macro` = MacroResult 또는 None,
    `theta` = ((θ 성분 (kind, key), 자연 좌표 값), ...) 층 0 이 상자 중심 대신 쓰는 출발 θ(구간이 정의된 성분만), `cells` = ((MOS, L 칸 index), ...),
    `area_est_m2`·`area_budget_m2` = 출발점의 면적 추정(MOS W·L + 수동소자)·선언 예산(없으면 None), `area_fraction` = 구간 안 위치 t(0 = gm/ID 하한 끝, 1 = 상한 끝)
    -- 면적 예산에 들어가는 최대 t, `uncovered` = θ 성분 중 구간이 값을 정하지 못해 상자 중심으로 남은 것((kind, key), ...), `records` = 매크로 모델 기록((코드, 상세 쌍들), ...)
    -- 1회차와 확정 풀이의 `macro_nonconvergent`·`macro_root_missing`·`macro_inactive`·`pm_floor_pole_at_ugf`,
    `ladder` = StartRung tuple -- 출발 사다리: 칸 0 = 실행 가능한 최대 t(위 `theta`·`cells`·`current_ref` 와 같다), 다음 칸은 t 를 절반씩 줄인 점(gm/ID 하한 쪽으로, 강반전). 층 0 이 칸 순서로
    커널 봉인 여부를 확인해 처음 봉인되는 칸에서 출발한다. 사다리 길이 = ⌈log2(gm/ID 구간 폭 최댓값 / LUT 곡선 gm/ID 최솟값)⌉ + 1(구간을 LUT 곡선 gm/ID 최솟값 단위까지 반으로 가르는 횟수; 선택 t = 0 이면 1칸),
    `current_ref` = ((MOS, A), ...) 전류를 정하지 못한 소자의 자리값 -- 선택 gm/ID·L 에서 폭이 PDK 최소 finger 폭 W_min 일 때의 전류 I = W_min·IDu/L (가장 작은 실현 가능 소자 = front 의
    최소 전력·면적 쪽 끝점; 층 0 Chebyshev 중심의 기준 전류)."""

    rows: tuple
    conflicts: tuple
    inactive: tuple
    macro: object
    theta: tuple
    cells: tuple
    area_est_m2: object
    area_budget_m2: object
    area_fraction: object
    uncovered: tuple
    records: tuple = ()
    current_ref: tuple = ()
    ladder: tuple = ()


@dataclasses.dataclass(frozen=True, eq=False)
class StartContext:
    """`iv_context.build_start_context` 가 S0 당 한 번 만드는 읽기 전용 입력 묶음(사전을 담아 `eq=False`).

    `curves` = `CurveBook`, `devices` = DeviceInfo tuple(구조 색 순), `by_name` = {이름: DeviceInfo}, `cls`·`kinds`·`pins` = 원소별 element_class·kind·{단자: 넷},
    `rails`·`rail_v` = 레일 넷 집합·{레일: V}, `node_colour` = {넷: 구조 색}, `constraints` = ((metric, op, 값), ...) 값이 있는 판정 제약, `gbw_hz`·`pm_deg` = 보상 목표(없으면 None),
    `area_budget_m2` = 면적 예산(없으면 None), `transfer` = gain 제약 전달 뷰(`ViewS1v`, 없으면 None), `l_owner` = {MOS: L 주인}, `basis` = `CurrentBasis`,
    `element_values` = {수동소자·이상원: 선언값 또는 None}, `zero_cancel` = {저항: ZeroCancel}, `node_targets` = {넷: 선언 노드 전위 V}, `input_dc_v` = 선언 입력 DC(없으면 None),
    `passive_area` = `PassiveAreaDecl`, `theta_bounds` = {수동소자: (하한, 상한)}, `l_cells` = {L 주인 소자: L 칸 ((lo, hi), ...)}, `ach` = U9 `Achievability` 또는 None,
    `port_direction`·`port_role` = {포트 넷: 방향·역할}, `box` = {θ 성분 (kind, key): (하한, 상한) 자연 좌표 값}(`SearchDomain.variables` 의 ln 좌표는 exp 로 되돌린다),
    `current_box` = {kind: (I_off, I_max) A}(`search.current_box` -- LUT 가 특성화한 단일 finger 범위. 면적 예산이 닫은 `SearchDomain.current_box` 상한은 W 상한이 없어 매크로 근 범위로 너무 넓다),
    `w_min_m` = PDK 최소 finger 폭(`SearchDomain.w_min_m`, W 하한 제약 S-18), `pdk` = core `PdkDecl`(mismatch 모델 bin 지도), `memo`·`w_keys` = LUT 손잡이, `gain` = `iv_gain_l.GainInputs`(이득 L 하한 입력; 비활성이면 None)·`gain_inactive` = 그 비활성 사유."""

    curves: object
    devices: tuple
    by_name: object
    cls: object
    kinds: object
    pins: object
    rails: frozenset
    rail_v: object
    node_colour: object
    constraints: tuple
    gbw_hz: object
    pm_deg: object
    area_budget_m2: object
    transfer: object
    l_owner: object
    basis: object
    element_values: object
    zero_cancel: object
    node_targets: object
    input_dc_v: object
    passive_area: object
    theta_bounds: object
    l_cells: object
    ach: object
    port_direction: object
    port_role: object
    box: object
    current_box: object
    w_min_m: float
    pdk: object
    memo: object
    w_keys: object
    gain: object = None
    gain_inactive: tuple = ()


@dataclasses.dataclass(frozen=True, eq=False)
class GainInputs:
    """`local` = `LocalInputs`, `tables` = `ParamTables`, `blocks` = ((BlockSpec, 목표 g_i dB), ...) 전달 뷰의 블록 순서."""

    local: object
    tables: object
    blocks: tuple
