"""MOD6 탐색 값 형식·어휘 (데이터 선언 모듈, 설계 design_mod6_search_front 2.3·4.1·6.3·7·8절).

공개 정의는 frozen dataclass 와 어휘 상수뿐이다. 계산은 다른 파일이 한다.

* 평가 상태 어휘(`STATUS_*`): 커널 1회의 결과가 front 후보가 될 수 있는지. `STATUS_PENDING_SEAL7` 은 봉인 7 이 VDSAT
  접근자 부재로만 미정인 점이다(`seal7_pending.py` 가 유일한 판정 스위치) -- 탐색 경로는 따라가지만 최종 front 에 들지 않는다.
* 단계 어휘(`STAGE_*`): S3 evals 의 `origin.stage`(설계 8절).
"""
import dataclasses

# ---- 평가 상태
STATUS_SEALED = "sealed"                      # 봉인 8항목 pass -> SealedSnapshot, 최종 front 후보
STATUS_PENDING_SEAL7 = "pending_seal_7"       # 봉인 7 만 VDSAT 접근자 부재로 미정 -- front 후보 아님(대기)
STATUS_UNDEFINED = "seal_undefined"           # 봉인 7 밖 항목이 미정(tol_V 셀 없음 등) -- front 후보 아님
STATUS_FAILED = "failed"                      # 후보 실패(CANDIDATE_FAILURE_CLASSES) -- FailureRecord
STATUS_OUTSIDE_DOMAIN = "outside_domain"      # θ 전류 원뿔 밖 -- 커널을 부르지 않는다(정의역 밖, 실패 아님)
ACCEPTED_STATUSES = (STATUS_SEALED, STATUS_PENDING_SEAL7)   # 탐색 경로가 따라가는 상태(제약 값이 있다)

# ---- 단계(origin.stage)
STAGE_START = "start"
STAGE_SLSQP = "slsqp"
STAGE_FD = "fd"
STAGE_L_SEARCH = "l_search"

# ---- 목적 축(설계 6.3, DEC-77): 전력 = power_dc_w(오케스트레이터 지시, metrics 3.13), 면적 = 탐색 축 area_search_m2
AXIS_POWER = "power_dc_w"
AXIS_AREA = "area_search_m2"
AXES = (AXIS_POWER, AXIS_AREA)

# ---- ε 방향
EPS_NONE = "none"

# ---- 제약 이름 접두(정규화 margin, 설계 5절)
CON_SEAL6 = "seal6_bulk"
CON_INVERSION = "inversion_floor"
CON_CONE = "current_cone"
CON_EPS = "eps"


@dataclasses.dataclass(frozen=True)
class SearchSettings:
    """탐색 실행 선언(기본값 없음 -- 모두 부르는 쪽이 출처와 함께 넘긴다, WP-03).

    `front_budget_s`: front 전체 벽시계 예산(s) -- spec `search.front_budget_s`(PA-2·U-47 결정 대기).
    `power_resolution_w`: 전력 축 분해능 b_P(W) -- 설계 5절 'max(전력 격자 분해능, 모델 오차)'의 격자 분해능 정의가
    없어(열린 항목 S-2) 선언으로만 받는다. `current_bounds_a`: θ 전류 기저 상자 (lo, hi) A -- GB4 상한표 미구현(S-3).
    `resistance_bounds_ohm`: θ 저항 상자 (lo, hi) Ω 또는 None(θ 저항이 없는 회로). `sources`: ((필드, 출처 문자열), ...).
    """

    front_budget_s: float
    power_resolution_w: float
    current_bounds_a: tuple
    resistance_bounds_ohm: object
    sources: tuple


@dataclasses.dataclass(frozen=True)
class Variable:
    """연속 탐색 변수 하나. `component` = θ 키 (kind, key), `log` = θ 값의 ln 좌표인가(전류·저항), `lo`·`hi` = 변수 좌표 bounds."""

    component: tuple
    log: bool
    lo: float
    hi: float


@dataclasses.dataclass(frozen=True)
class SearchDomain:
    """S0·고정 W 집합마다 1개(설계 4.1). `variables` = 연속 변수(θ 성분 순), `l_cells` = ((MOS, ((lo, hi), ...)), ...)
    L 칸(PDK 모델 bin 안 LUT L 점 구간; 앵커 하나뿐인 칸은 lo == hi). `area_resolution_m2` = b_A = 제조 격자 × 최소 finger 폭
    (DEC-80 (i), 모델 오차 미측정이라 (ii) = (i) -- '추정'), `power_resolution_w` = b_P(선언)."""

    variables: tuple
    l_cells: tuple
    area_resolution_m2: float
    power_resolution_w: float


@dataclasses.dataclass(frozen=True)
class EvalKey:
    """평가 키(설계 7.1): (S0 지문, 스키마 지문, L 칸 벡터, 고정 W 지문, θ 값 `float.hex`). ε·출처는 넣지 않는다."""

    context_fp: str
    schema_fp: str
    cells: tuple
    w_fixed_fp: object
    theta_hex: tuple


@dataclasses.dataclass(frozen=True)
class Objectives:
    """목적 값. `power_w` = power_dc_w, `area_m2` = area_search_m2, `per_rail` = ((레일, I_k), ...),
    `kcl_residual_a`, `gate_area_m2`, `passive_area_undeclared`, `passive_value_undetermined`(값 미정 수동소자)."""

    power_w: float
    area_m2: float
    per_rail: tuple
    kcl_residual_a: float
    gate_area_m2: float
    passive_area_undeclared: tuple
    passive_value_undetermined: tuple


@dataclasses.dataclass(frozen=True)
class ConstraintRow:
    """정규화 부등식 c ≥ 0 하나(설계 5절). `active` = c ≤ 1(여유가 분해능 한 칸 이하)."""

    name: str
    c: float
    active: bool


@dataclasses.dataclass(frozen=True, eq=False)
class EvalResult:
    """커널 1회 결과(설계 2.3). `evaluation` = DcEvaluation 또는 None, `failure` = FailureRecord 또는 None,
    `constraints` = ConstraintRow tuple(ε 제약 제외 -- ε 는 키 밖이라 호출부가 붙인다), `cone` = 원뿔 제약 행."""

    key: EvalKey
    theta: tuple
    status: str
    evaluation: object
    objectives: object
    constraints: tuple
    cone: tuple
    failure: object
    seq: int


@dataclasses.dataclass(frozen=True)
class StartPoint:
    """시작점(설계 6.1). `theta` = ((kind, key), 값) 정렬, `cells` = L 칸 index 벡터, `source` ∈ {"given", "s3"}."""

    start_id: str
    theta: tuple
    cells: tuple
    source: str


@dataclasses.dataclass(frozen=True, eq=False)
class SolveResult:
    """ε 풀이 하나(설계 6.2). `best` = 받아들인 최선 EvalResult 또는 None, `eps` = (축, 값) 또는 None,
    `minimize` = 최소화 축, `iterations`·`restarts`, `stop` = 종료 사유, `history` = 수락 반복 EvalResult tuple,
    `aborts` = 재시작을 부른 중단 사유 tuple(순서대로)."""

    best: object
    eps: object
    minimize: str
    iterations: int
    restarts: int
    stop: str
    history: tuple
    aborts: tuple = ()


@dataclasses.dataclass(frozen=True, eq=False)
class FrontPoint:
    """front 점. `point_id`, `result` = EvalResult, `origin` = 출처(끝점·ε·L-b), `dominated_by` = 지배한 점 id 또는 None."""

    point_id: str
    result: object
    origin: tuple
    dominated_by: object = None


@dataclasses.dataclass(frozen=True)
class ParetoResult:
    """비지배 필터 결과. `kept` = 남은 index(입력 순서 아님 -- 남기는 순서 규칙 순), `folded` = ((접힌 index, 대표 index), ...),
    `dominated` = ((지배당한 index, 지배한 index), ...)."""

    kept: tuple
    folded: tuple
    dominated: tuple


@dataclasses.dataclass(frozen=True, eq=False)
class SearchFront:
    """탐색 축 front(설계 6.3 6). `front` = 봉인된(STATUS_SEALED) 비지배 점만 -- 최종 front. `pending_front` = 봉인 7 대기
    점끼리의 비지배 점(최종 아님, '추정'·대기 표기). `failed_eps` = 풀이 실패 ε, `resolution` = ((키, 값), ...),
    `perf` = ((키, 값), ...), `notes` = 열린 항목·판정 보류 기록."""

    run_id: str
    front: tuple
    pending_front: tuple
    failed_eps: tuple
    resolution: tuple
    perf: tuple
    notes: tuple


@dataclasses.dataclass(frozen=True)
class NodeRow:
    """`node_across_front` 한 줄: front 점마다 노드 전압·writer 티어·그 노드에 닿는 소자 op."""

    point_id: str
    status: str
    voltage: float
    tier: object
    devices: tuple
