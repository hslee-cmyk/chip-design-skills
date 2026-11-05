"""MOD8 convergence 값 레코드 -- 데이터 선언 모듈 (계획 N3.17 LY3·LY5·LY7·LY8, DEC-79·84·89, 설계 40 §3.9, 계약 CONTRACT.md).

공개 정의는 frozen dataclass 와 상태 이름 상수뿐이다. 계산은 다른 파일이 한다.

* 점 하나의 상태 `ConvergedPoint.status`: `STATUS_CONVERGED`(레이아웃 결과의 실현 기하로 평가한 점이 다음 레이아웃과 같은 기하를 낳는다 -- 고정점),
  `STATUS_NONCONVERGENT`(반복이 K_max 에 닿음, FailureRecord NONCONVERGENT), `STATUS_INFEASIBLE`(실현 기하의 재평가가 봉인·제약을 어긴다 --
  거부할 W_request 도 남지 않음), `STATUS_UNPLACEABLE`(레이아웃이 어떤 폭 슬라이스로도 못 놓는 소자가 있거나 입력을 만들 수 없다).
* 앞 겹 버린 점 `DroppedPoint.reason`: `DROP_DOMINATED`(판정 축 재필터에서 지배당함), `DROP_FOLDED`(모든 축이 동률 폭 안 -- 먼저 남은 점이 대표),
  `DROP_NONCONVERGED`(수렴하지 못해 판정 축 값을 정할 수 없음).
"""
import dataclasses

STATUS_CONVERGED = "converged"
STATUS_NONCONVERGENT = "nonconvergent"
STATUS_INFEASIBLE = "infeasible_after_layout"
STATUS_UNPLACEABLE = "unplaceable"
STATUSES = (STATUS_CONVERGED, STATUS_NONCONVERGENT, STATUS_INFEASIBLE, STATUS_UNPLACEABLE)

DROP_DOMINATED = "dominated_on_layout_axis"
DROP_FOLDED = "folded_within_tie"
DROP_NONCONVERGED = "not_converged"

# Relaxation.outcome
RELAX_PLACED = "interdigitation_placed"                # 완화한 배치가 놓였다(맨 앞 review_needed, dx·dy 기록)
RELAX_NOT_PLACED = "interdigitation_not_placed"        # 완화를 시도했으나 배치되지 못했다
RELAX_NOT_AVAILABLE = "not_relaxable"                  # 완화할 패턴 경로가 없다(hub 없는 branch_symmetric) -- 배치되지 못한 채 review_needed


@dataclasses.dataclass(frozen=True)
class Relaxation:
    """LY5 완화 판정 하나(MOD8 몫, 조용한 완화 금지). `role` = 입력 role(완화 전), `reason` = 레이아웃이 배치하지 못한 사유, `attempts` = 그 그룹의
    시도 기록(`GroupAttempt` tuple, 완화 전), `outcome` ∈ RELAX_*, `pattern`·`dx`·`dy`·`ok` = 완화 뒤 최종 배치(없으면 None)."""

    gid: str
    role: str
    members: tuple
    reason: str
    attempts: tuple
    outcome: str
    pattern: object
    dx: object
    dy: object
    ok: bool


@dataclasses.dataclass(frozen=True)
class Placement:
    """레이아웃 결과에서 읽은 소자 하나의 실효 배치(MOD8 재검증 입력). `key` = 폭 키, `finger_w_m` = key x 격자, `n_fingers`, `W_m` = nf x finger_w(레이아웃이
    쓰는 식 그대로 -- 다음 레이아웃과 비트가 같다), `pending` = 이 소자가 W_request(그룹 cc_nf) 응답 대기 -- 놓인 곳이 아니라 요청한 (키, nf) 다,
    `tol_effective` = 레이아웃 실효 W 허용오차(LY1, 상대)."""

    name: str
    key: int
    finger_w_m: float
    n_fingers: int
    W_m: float
    pending: bool
    tol_effective: float


@dataclasses.dataclass(frozen=True, eq=False)
class PlacedLayout:
    """`place_layout` 결과(평가 커널 호출 없이 얻은 레이아웃). `layout` = 마지막 `run_layout` 결과(설계점 스냅샷 -- 그 입력도 `ly_*` 입력 필드), `undelivered` = 넘기지 못한 matching 그룹,
    `placements`·`unplaced` = `effective_placement`, `pdk` = 이 호출의 `LayoutPdk`, `relaxed` = 완화 입력으로 바꾼
    gid 집합(frozenset), `first_seen` = {gid: 완화 판정 시점의 `GroupLayout`}, `layout_calls` = 이 호출의 `run_layout` 횟수."""

    layout: object
    undelivered: tuple
    placements: tuple
    unplaced: tuple
    pdk: object
    relaxed: frozenset
    first_seen: dict
    layout_calls: int


@dataclasses.dataclass(frozen=True)
class Iteration:
    """W_request 루프 반복 하나. `index` = 1 부터(재평가 순서), `geometry_devices` = ((소자, 폭 키, finger 수), ...) 이름순, `requested` = W_request 로
    고정한 소자(그룹 요청 cc_nf), `rejected` = 이 반복에서 거부로 돌린 소자, `status` ∈ {"sealed", "rejected", "failed"}, `kernel_calls` = 이 반복이 쓴 커널 호출 수,
    `layout_area_m2` = 이 반복이 쓴 레이아웃의 판정 축 외곽 면적, `max_dlnw` = 사이징 W 대비 소자 W 의 최대 |ln 비|, `margin` = 실패 margin(성공이면 None),
    `excluded` = ((kind, 폭 키), ...) 이 반복의 재검증이 거절돼 레이아웃의 폭 키 후보에서 뺀 키(`status` == "excluded")."""

    index: int
    geometry_devices: tuple
    requested: tuple
    rejected: tuple
    status: str
    kernel_calls: int
    layout_area_m2: float
    max_dlnw: float
    margin: object
    excluded: tuple = ()


@dataclasses.dataclass(frozen=True)
class JunctionChange:
    """소자 하나의 접합 용량 변화 (F, 소자 전체): 레이아웃 전(LUT 생성 규칙 확산 기하) -> 레이아웃 뒤(MOD7 `ly.diffusion`, DEC-91 (2))."""

    device: str
    cdb_before: float
    csb_before: float
    cdb_after: float
    csb_after: float


@dataclasses.dataclass(frozen=True, eq=False)
class ConvergedPoint:
    """front 점 하나의 MOD8 결과. `result` = 실현 기하로 재검증한 `search.EvalResult`(수렴하지 못하면 마지막 성공 재검증, 없으면 None),
    `layout` = 마지막 `LayoutResult`(레이아웃 필드를 쓴 설계점 스냅샷), `geometry` = 마지막 재검증 `RealizedGeometry`, `search_area_m2` = 탐색 축 면적(사이징 W 기준 -- 재검증 전 점),
    `layout_area_m2` = 판정 축 외곽 면적(수동소자 블록 포함, 수렴 레이아웃), `power_w`·`power_resolution_w` = 재검증 점의 전력 축 값, `k_max` = 반복 상한(첫 레이아웃에서 한 번 계산,
    None 이면 레이아웃 전에 끝남), `iterations` = 재평가 기록, `relaxations` = 완화 판정, `rejected` = 거부한 W_request 소자, `narrowed` = ((kind, 폭 키), ...) 커널이 한 kind 에
    슬라이스 하나만 쓰므로 PDK 폭 키를 좁힌 결과, `excluded` = ((kind, 폭 키), ...) 재검증이 거절돼 후보에서 뺀 키, `junction` = 소자별 접합 용량 변화, `unmatched` = 배치되지 못한 matching 그룹 ((gid, role, reason), ...),
    `undelivered` = 레이아웃에 넘기지 못한 matching 그룹 ((gid, 사유), ...), `kernel_calls`·`layout_calls` = 이 점이 쓴 커널·레이아웃 호출 수,
    `failure` = FailureRecord 또는 None, `notes` = 기록 ((키, 값), ...)."""

    point_id: str
    status: str
    search_point: object
    result: object
    layout: object
    geometry: object
    search_area_m2: float
    layout_area_m2: object
    power_w: object
    power_resolution_w: object
    k_max: object
    iterations: tuple
    relaxations: tuple
    rejected: tuple
    narrowed: tuple
    excluded: tuple
    junction: tuple
    unmatched: tuple
    undelivered: tuple
    kernel_calls: int
    layout_calls: int
    failure: object
    notes: tuple


@dataclasses.dataclass(frozen=True)
class DroppedPoint:
    """판정 축 재필터가 뺀 점: `by` = 지배·대표 점 id 또는 None(수렴 못 한 점)."""

    point_id: str
    reason: str
    by: object


@dataclasses.dataclass(frozen=True, eq=False)
class ConvergedFront:
    """`converge` 결과. `front` = 판정 축 재필터를 통과한 `ConvergedPoint`(남기는 순서: 전력 오름차순 -> slack 큰 쪽 -> id), `dropped` = 뺀 점과 사유,
    `nonconverged` = 수렴하지 못한 점(상태별), `points` = 수렴을 시도한 모든 `ConvergedPoint`(처리 순서 -- 재필터가 뺀 점의 판정 축 값도 여기 있다), `rounds` = 재필터와 MOD8 재실행 교대 횟수, `k_alt` = 교대 상한(첫 재필터 뒤에 한 번 계산, None 이면 계산 전),
    `admitted` = 교대에서 새로 레이아웃한 후보 점 id, `perf` = ((키, 값), ...), `notes` = 기록(판정 축 포함 항목·면적 모델 오차 미선언 등)."""

    front: tuple
    dropped: tuple
    nonconverged: tuple
    points: tuple
    rounds: int
    k_alt: object
    admitted: tuple
    perf: tuple
    notes: tuple
