"""MOD7 레이아웃 출력 계약과 graph 필드 값 레코드 (계획 N3.17 출력 계약, design_mod7_layout.md 3절 끝·4절,
사용자 결정 2026-10-07 Q4·Q8).

데이터 선언 모듈(공개 정의 = frozen dataclass 뿐). 모든 값은 불변(tuple·스칼라·frozen dataclass)이라 graph 필드 값과
지문(core `fp_of`)에 그대로 쓰인다. 길이·폭 m, 면적 m^2, 전류 밀도 A/m. 폭 키 = finger_w / 제조 격자(정수).

필드 값: `ConservedPoint`·`DevicePins`·`DeviceAttrs`(device `ly_point`·`ly_pins`·`ly_attrs` -- `LayoutDevice` 칸을 겹치지 않게 나눈 것), `SliceDensity`(device `ly_slices`), `FingerCandidate`(device `ly_fw_cand`), `GroupLayout`·`MatchingDisposition`
(graph `ly_groups`·`ly_dispositions`), `DeviceFinger`(device `ly_finger`), `RowsLayout`·`FloorplanSummary`
(graph `ly_rows`·`ly_floorplan`). 결과: `LayoutResult`(설계점 스냅샷 하나, 설계 40 v1.6 §2.4.7 -- 이번 호출에서 쓴 블록은 RunCounters 행이 정본),
필드 파생 출력: `LayoutOutputs`(맨 앞 `review_needed`, 끝에 재검증 요청 `Revalidation`).
"""
import dataclasses

# 레이아웃 뒤 재검증(Q4 (ii)): 실현 기하로 평가 커널 1회 + 봉인 1~8 을 다시 돌린 뒤 freeze.
REVALIDATION_SEALS = ("seal_1", "seal_2", "seal_3", "seal_4", "seal_5", "seal_6", "seal_7", "seal_8")
REVALIDATION_PENDING = "pending_wiring"
REVALIDATION_CONSUMER = "convergence (MOD8): evaluation kernel + seals 1-8 on realized geometry, then freeze"
REVALIDATION_PENDING_REASON = ("the layout only requests re-validation (LayoutResult is immutable, status stays pending_wiring): "
                               "MOD8 convergence.converge_point consumes it -- evaluates the realized geometry with the evaluation "
                               "kernel + seals 1-8 + junction caps from ly.diffusion and records the outcome in ConvergedPoint")
# 판정 축 면적 포함 항목(Q8 (vii)) -- FloorplanSummary.included 의 항목 이름.
AREA_ITEM_ROW_END_DUMMY = "row_end_dummy_x2_per_row"
AREA_ITEM_TAP = "body_tap_per_group"
AREA_ITEM_PASSIVES = "passive_blocks_mim_poly_resistor"
AREA_ITEM_WELL_SPACING = "well_spacing_between_bodies"
AREA_ITEM_ROW_GAP = "row_gap"
AREA_ITEM_FINGER_OVERHEAD = "finger_pitch_overhead"
# stage 를 넘는 hub 병합(Q8 (viii)) -- 노이즈 결합 우려는 기록만 한다(거부 사유로 쓰지 않는다).
MERGE_NOISE_NOTE = "noise_coupling_not_evaluated (recorded only, not a rejection reason)"


@dataclasses.dataclass(frozen=True)
class ConservedPoint:
    """보존량·동작점(device `ly_point` 의 값): kind, L, ID, gm/ID, VDS, VSB -- `slice_density` 가 소자에서 읽는 칸 전부.
    참고 W(`LayoutDevice.W_m`)는 보존량이 아니라 들어 있지 않다."""

    kind: str
    L_m: float
    ID_A: float
    gm_id: float
    vds_V: float
    vsb_V: float


@dataclasses.dataclass(frozen=True)
class DevicePins:
    """소자 단자 연결(device `ly_pins` 의 값): drain·gate·source 넷. body 는 넣지 않는다(세 블록이 읽지 않는다 -- `DeviceAttrs`).
    값을 dataclass 로 두는 것은 정준 별칭 번역이 값 안의 문자열을 이름과 같을 때만 바꾸기 때문이다(칸 이름은 번역 대상이 아니다)."""

    drain: str
    gate: str
    source: str


@dataclasses.dataclass(frozen=True)
class DeviceAttrs:
    """소자 부가 칸(device `ly_attrs` 의 값): sizing 참고 W `W_m`(보존량이 아니다 -- W 만 바뀌면 이 필드만 바뀐다), `body` 넷, `diode`."""

    W_m: float
    body: str
    diode: bool


@dataclasses.dataclass(frozen=True)
class SliceDensity:
    """PDK 특성화 폭 슬라이스 하나에서의 보존량 실현(Q4 (i)): 그 슬라이스의 gm/ID 근 `vgs_V`, 전류 밀도 `J_A_per_m`(= ID/W),
    `W_need_m` = ID / J, `tol_v_V` = 그 슬라이스 tol_V 셀(`id_equivalent`) 값. `reason` = "" 이면 사용 가능, 아니면 이 폭을
    후보에서 뺀 사유(LUT 실패 reason 또는 `tol_v_undefined`) -- 그때 숫자 필드는 None."""

    finger_w_key: int
    finger_w_m: float
    vgs_V: object
    J_A_per_m: object
    W_need_m: object
    tol_v_V: object
    reason: str


@dataclasses.dataclass(frozen=True)
class WTolerance:
    """W 허용오차(LY1, Q4 (iv)): `lower` = grid/(2 fw), `upper` = tol_V(id_equivalent 셀) x gm/ID,
    `effective` = max(upper, lower), `grid_dominated` = lower > upper."""

    lower: float
    upper: float
    effective: float
    grid_dominated: bool


@dataclasses.dataclass(frozen=True)
class FingerCandidate:
    """finger_w 후보 하나(LY1·LY2): 폭 키, finger 수, 그 슬라이스의 `W_need_m`, 실현 W = nf x fw,
    상대 오차 = |nf fw - W_need| / W_need, 허용오차(`WTolerance` 의 네 값). `ok` = 오차 <= 실효 허용오차 --
    후보 순위 기준일 뿐 합격 판정이 아니다(합격은 레이아웃 뒤 재검증, Q4 (ii))."""

    finger_w_key: int
    finger_w_m: float
    n_fingers: int
    W_need_m: float
    W_realized_m: float
    err_rel: float
    lower: float
    upper: float
    tol_effective: float
    grid_dominated: bool
    ok: bool


@dataclasses.dataclass(frozen=True)
class WRequest:
    """MOD8 에 돌려주는 W 변경 요청(LY3). 레이아웃은 W 를 적용하지 않는다. `W_old_m` = 그 폭 슬라이스의 W_need."""

    device: str
    W_old_m: float
    W_new_m: float
    reason: str
    group: object = None


@dataclasses.dataclass(frozen=True)
class GroupAttempt:
    """그룹 배치 시도 하나(조용한 완화 금지 -- 시도 순서대로 전부 남긴다, LY5)."""

    step: str
    pattern: object
    finger_w_m: object
    n_fingers: tuple
    W_realized_m: tuple
    method: object
    dx: object
    dy: object
    ok: bool
    reason: str


@dataclasses.dataclass(frozen=True)
class PatternRow:
    """패턴 함수가 낸 행 하나(정규화 후). `segments` = ((transistor_sequence, node_sequence), ...)."""

    transistor_sequence: tuple
    node_sequence: tuple
    segments: tuple
    crossover_after: tuple


@dataclasses.dataclass(frozen=True)
class GroupLayout:
    """matching 그룹 결과. `ok` = 멤버 무게중심 일치(dx = dy = 0, finger 피치 단위). `pending` = W_request 를 내고 MOD8
    응답 대기(배치는 `provisional`). LY5: W_request 를 낼 수 없거나(조정 불가·거부·사용 가능 폭 없음) 무게중심이 안 맞아도
    레이아웃은 즉시 완화하지 않는다 -- pattern None + 사유로 두고 판정을 MOD8 에 맡긴다(`review_needed`).
    `l_mismatch` = LY4 `matching_L_mismatch` 기록: 멤버 L 이 서로 다르면 ((멤버 이름, L_m), ...) (멤버 순서), 같으면 ()
    -- 기록만이고 거부 사유가 아니다(L 통일은 LR2 소관)."""

    gid: str
    role: str
    members: tuple
    pattern: object
    method: object
    finger_w_key: object
    finger_w_m: object
    n_fingers: tuple
    rows: tuple
    residual: object
    crossover_count: object
    isolated_pairs: object
    dx: object
    dy: object
    ok: bool
    pending: bool
    provisional: bool
    reason: str
    attempts: tuple
    w_requests: tuple
    l_mismatch: tuple = ()


@dataclasses.dataclass(frozen=True)
class MatchingDisposition:
    """레이아웃 matching 에서 뺀 그룹의 기록(Q8 (iii)): `disposition` = "excluded_from_layout_matching", `reason` = 근거."""

    gid: str
    role: str
    members: tuple
    disposition: str
    reason: str


@dataclasses.dataclass(frozen=True)
class DeviceFinger:
    """소자별 finger 확정(행별 finger_w, LY2·L6). `origin` = "group" | "row". `w_request` 는 실효 허용오차를 못 지킬 때만."""

    name: str
    finger_w_key: int
    finger_w_m: float
    n_fingers: int
    W_need_m: float
    W_realized_m: float
    err_rel: float
    lower: float
    upper: float
    tol_effective: float
    grid_dominated: bool
    ok: bool
    origin: str
    group: object
    w_request: object


@dataclasses.dataclass(frozen=True)
class RowLayout:
    """물리 행 하나. `devices` = ((이름, finger 수), ...), 폭 = sum(nf x (L + PDK 여유)), 높이 = finger_w.
    `method`: "pattern:<방법>" | "euler" | "mirror" | "crossover". `n_components` = diffusion 섬 수.
    `group` = 패턴 행이면 그 gid. `matching` = 이 행에 레이아웃 matching 그룹 멤버가 있음(자동 접기 대상 아님, Q8 (v))."""

    row_id: str
    row_group: str
    kind: str
    finger_w_key: int
    finger_w_m: float
    width_m: float
    devices: tuple
    transistor_sequence: tuple
    node_sequence: tuple
    segments: tuple
    method: str
    crossover_count: int
    n_components: int
    walk_ok: bool
    group: object
    matching: bool


@dataclasses.dataclass(frozen=True)
class BoxVerdict:
    """행 폭 비(max/min)와 길이 비 -- 기록만(Q8 (vi): 하드 box 게이트 없음). `folds` = ((행 id, 접은 행 수), ...)."""

    width_ratio: float
    elongation: float
    total_width_m: float
    total_height_m: float
    widest_row: str
    narrowest_row: str
    folds: tuple


@dataclasses.dataclass(frozen=True)
class FoldAttempt:
    """box 개선 시도 하나(목적 = 판정 축 외곽 면적, Q8 (v)(vi)). `action` = "fold"(matching 없는 행 접기) |
    "rebuild"(matching 패턴 행을 패턴 함수로 n_rows 재구성). dx·dy 는 rebuild 의 재판정 값(fold 는 None)."""

    row_id: str
    action: str
    n_rows: int
    outline_area_m2: float
    dx: object
    dy: object
    adopted: bool
    reason: str


@dataclasses.dataclass(frozen=True)
class MergeDecision:
    """stage 를 넘는 hub 병합 후보 하나의 판정(Q8 (viii)): 병합 전후 판정 축 면적으로 채택, `note` = 노이즈 결합 기록."""

    rows: tuple
    net: str
    merged: bool
    reason: str
    area_before_m2: float
    area_after_m2: object
    note: str


@dataclasses.dataclass(frozen=True)
class GroupRebuild:
    """패턴 행 재구성으로 바뀐 matching 그룹의 최종 배치(Q8 (v)): 행 수·방법·dx·dy."""

    gid: str
    n_rows: int
    method: str
    dx: float
    dy: float


@dataclasses.dataclass(frozen=True)
class RowsLayout:
    """graph `ly_rows` 값: 물리 행 전부(행 id 정렬), 행 폭 비 기록, box 개선 시도, hub 병합 판정, 재구성된 그룹."""

    rows: tuple
    box: BoxVerdict
    fold_attempts: tuple
    merge_decisions: tuple
    rebuilt_groups: tuple


@dataclasses.dataclass(frozen=True)
class FloorplanSummary:
    """floorplan 결과. `outline_area_m2` = 외곽(bbox) 면적(판정 축 면적, 사용자 확정 12번 (나)),
    `grid_m` = 제조 격자(재필터 동률 폭 ΔA_tie = grid_m x max(두 점 bbox 변 4개)의 재료 -- `area_tie.area_tie_m2(a, b)`, DEC-79·DEC-95 (2)).
    `placements` = ((블록 이름, x, y, 폭, 높이), ...) m: 행 id(폭은 dummy 포함), `tap:<행 그룹>`(그룹 경계 tap 띠, LY10),
    `passive:<이름>`(수동소자 블록). `passive_area_m2` = 수동소자 블록 면적 합(외곽 면적 `outline_area_m2` 에 포함).
    `included` = ((항목, 값 m, PDK 규칙 번호), ...) -- 판정 축 면적에 넣은 항목(Q8 (vii), front 표 '포함 항목' 열)."""

    bbox_width_m: float
    bbox_height_m: float
    outline_area_m2: float
    grid_m: float
    aspect_ratio: float
    packing_density: float
    placements: tuple
    included: tuple
    passive_area_m2: float = 0.0


@dataclasses.dataclass(frozen=True)
class DeviceDiffusion:
    """`ly.diffusion[dev]`(LY8, DEC-89 (5)·DEC-91 (2)): 소자 finger 하나 평균 확산 기하와 finger 수. Euler 행의 공유 확산 통계 --
    엔진 접합 용량(`metrics.DiffusionGeometry(finger_w_m, ad_m2, as_m2, pd_m, ps_m, m = n_fingers)`)과 오라클 입력
    (`devices[].diffusion{ad_m2, as_m2, pd_m, ps_m}`)이 같은 값을 쓴다. 길이 m, 면적 m^2. pd·ps 는 BSIM4 perMod=1 둘레
    (게이트 쪽 변 finger_w 를 포함 -- 접합 용량이 `pd - Weffcj` 를 STI 측벽으로 쓴다)."""

    name: str
    finger_w_m: float
    n_fingers: int
    ad_m2: float
    as_m2: float
    pd_m: float
    ps_m: float


@dataclasses.dataclass(frozen=True)
class DeviceLayout:
    """소자별 최종: finger_w·nf·행별 finger 수, 참고 W, 슬라이스 W_need, 실현 W·오차·허용오차(하한·상한·실효·격자 지배),
    후보에서 뺀 폭 슬라이스 ((폭 키, 사유), ...)."""

    name: str
    finger_w_m: float
    n_fingers: int
    rows: tuple
    W_m: float
    W_need_m: float
    W_realized_m: float
    W_err_rel: float
    W_tol_lower: float
    W_tol_upper: float
    W_tol_effective: float
    grid_dominated: bool
    origin: str
    excluded_slices: tuple


@dataclasses.dataclass(frozen=True)
class ReviewItem:
    """결과 맨 앞 `review_needed` 항목(Q8 (iv)): 완화되었거나 배치되지 못한 차동쌍·branch_symmetric 그룹과 그 dx·dy(피치 단위)."""

    gid: str
    role: str
    reason: str
    dx: object
    dy: object


@dataclasses.dataclass(frozen=True)
class RealizedDevice:
    """재검증 입력 소자 하나(Q4 (ii)(iii)): 실현 기하(폭 키·finger_w·nf·실현 W)와 보존량·동작점.
    `recalibrate_id` = False 는 diode 연결 소자(ID 재보정 불필요), `recompute_node_voltages` 는 모든 소자 True."""

    name: str
    kind: str
    finger_w_key: int
    finger_w_m: float
    n_fingers: int
    W_need_m: float
    W_realized_m: float
    ID_A: float
    gm_id: float
    L_m: float
    vds_V: float
    vsb_V: float
    recalibrate_id: bool
    recompute_node_voltages: bool
    diffusion: object = None


@dataclasses.dataclass(frozen=True)
class Revalidation:
    """레이아웃 뒤 재검증 요청(Q4 (ii)): W_request 유무와 관계없이 항상 `required`. `status` = `REVALIDATION_PENDING`
    (평가 커널·봉인이 엔진에 생기기 전까지), `seals` = `REVALIDATION_SEALS`, `consumer` = 이 요청을 소비할 곳."""

    required: bool
    status: str
    seals: tuple
    devices: tuple
    consumer: str
    reason: str


@dataclasses.dataclass(frozen=True)
class LayoutResult:
    """`run_layout` 반환(설계 40 v1.6 §2.4.7): `snapshot` = 레이아웃 `ly_*` 필드를 쓴 설계점 스냅샷(같은 설계점 위 다음 호출의 `previous`),
    레이아웃 값은 스냅샷 필드가 정본이다. '이번 호출에서 쓴 writer'(계산·이식·재사용)는 사본으로 두지 않고 `RunCounters`(perf 행)가 정본이다."""

    snapshot: object = dataclasses.field(repr=False)


@dataclasses.dataclass(frozen=True)
class LayoutOutputs:
    """`layout_outputs(snapshot)` 반환 -- 레이아웃 필드에서 파생한 출력 계약 항목(필드 사본이 아니라 읽을 때 만드는 반환값).
    맨 앞 `review_needed`(Q8 (iv)). `devices` = 소자 이름순 `DeviceLayout`. `w_invariant_ok` = 행별 finger 합 = 소자 nf 이고 실효 허용오차를
    넘는 소자는 모두 W_request 가 있다. `revalidation` = 재검증 요청(Q4 (ii))."""

    review_needed: tuple
    devices: tuple
    coverage_ok: bool
    coverage_missing: tuple
    w_requests: tuple
    w_invariant_ok: bool
    revalidation: Revalidation
