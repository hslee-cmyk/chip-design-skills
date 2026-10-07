"""MOD7 레이아웃 출력 계약과 graph 필드 값 레코드 (계획 N3.17 출력 계약, design_mod7_layout.md 3절 끝·4절).

데이터 선언 모듈(공개 정의 = frozen dataclass 뿐). 모든 값은 불변(tuple·스칼라·frozen dataclass)이라 graph 필드 값과
지문(core `fp_of`)에 그대로 쓰인다. 길이·폭 m, 면적 m^2. 폭 키 = finger_w / 제조 격자(정수).

필드 값: `FingerCandidate`(device `ly_fw_cand`), `GroupLayout`(graph `ly_groups`), `DeviceFinger`(device `ly_finger`),
`RowsLayout`(graph `ly_rows`), `FloorplanSummary`(graph `ly_floorplan`). 최종 결과: `LayoutResult`.
"""
import dataclasses


@dataclasses.dataclass(frozen=True)
class FingerCandidate:
    """finger_w 후보 하나(LY1·LY2): 폭 키, finger 수, 실현 총 W, 상대 오차, 실현 하한 grid/(2 fw), 상한 tol_V x gm/ID.
    `ok` = 오차 <= 상한 이고 하한 <= 상한."""

    finger_w_key: int
    finger_w_m: float
    n_fingers: int
    W_realized_m: float
    err_rel: float
    lower: float
    upper: float
    ok: bool


@dataclasses.dataclass(frozen=True)
class WRequest:
    """MOD8 에 돌려주는 W 변경 요청(LY3). 레이아웃은 W 를 적용하지 않는다."""

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
    응답 대기(배치는 `provisional`). `relaxed` = 차동쌍이 interdigitation 으로 완화됨(LY5 (iii))."""

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
    relaxed: bool
    pending: bool
    provisional: bool
    reason: str
    attempts: tuple
    w_requests: tuple


@dataclasses.dataclass(frozen=True)
class DeviceFinger:
    """소자별 finger 확정(행별 finger_w, LY2·L6). `origin` = "group" | "row". `w_request` 는 상한을 못 지킬 때만."""

    name: str
    finger_w_key: int
    finger_w_m: float
    n_fingers: int
    W_realized_m: float
    err_rel: float
    lower: float
    upper: float
    ok: bool
    origin: str
    group: object
    w_request: object


@dataclasses.dataclass(frozen=True)
class RowLayout:
    """물리 행 하나. `devices` = ((이름, finger 수), ...), 폭 = sum(nf x (L + PDK 여유)), 높이 = finger_w.
    `method`: "pattern:<방법>" | "euler" | "mirror" | "crossover". `n_components` = diffusion 섬 수."""

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


@dataclasses.dataclass(frozen=True)
class BoxVerdict:
    """행 폭 비(max/min) 판정과 길이 비. `folds` = ((행 id, 접은 행 수), ...)."""

    ok: bool
    width_ratio: float
    max_row_ratio: float
    elongation: float
    total_width_m: float
    total_height_m: float
    widest_row: str
    narrowest_row: str
    folds: tuple


@dataclasses.dataclass(frozen=True)
class RowsLayout:
    """graph `ly_rows` 값: 물리 행 전부(행 id 정렬)와 box 판정."""

    rows: tuple
    box: BoxVerdict


@dataclasses.dataclass(frozen=True)
class FloorplanSummary:
    """floorplan 결과. `outline_area_m2` = 외곽(bbox) 면적(판정 축 면적, 사용자 확정 12번 (나)),
    `area_tie_m2` = 격자 한 칸 면적(재필터 동률 해상도). `placements` = ((행 id, x, y, 폭, 높이), ...) m."""

    bbox_width_m: float
    bbox_height_m: float
    outline_area_m2: float
    area_tie_m2: float
    aspect_ratio: float
    packing_density: float
    placements: tuple


@dataclasses.dataclass(frozen=True)
class DeviceLayout:
    """소자별 최종: finger_w·nf·행별 finger 수, 실현 W·오차·허용 하한·상한."""

    name: str
    finger_w_m: float
    n_fingers: int
    rows: tuple
    W_m: float
    W_realized_m: float
    W_err_rel: float
    W_tol_lower: float
    W_tol_upper: float
    origin: str


@dataclasses.dataclass(frozen=True)
class LayoutResult:
    """`run_layout` 반환. `w_invariant_ok` = 상한을 넘는 소자는 모두 W_request 가 있다(design 3절 끝 불변식).
    `computed_blocks` = 이번 호출에서 다시 계산한 블록 writer 이름(나머지는 graph 필드 재사용).
    `snapshot` = 결과 필드를 담은 core GraphSnapshot(다음 호출의 `previous` -- 필드 = 캐시)."""

    devices: tuple
    groups: tuple
    rows: tuple
    box: BoxVerdict
    floorplan: FloorplanSummary
    coverage_ok: bool
    coverage_missing: tuple
    w_requests: tuple
    w_invariant_ok: bool
    computed_blocks: tuple
    snapshot: object = dataclasses.field(default=None, compare=False, repr=False)
