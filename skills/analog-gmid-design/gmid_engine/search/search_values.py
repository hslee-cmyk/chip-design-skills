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
CON_WMIN = "w_min"                            # 설계 개정 S-18: W ≥ PDK min_finger_w_m


@dataclasses.dataclass(frozen=True)
class SearchSettings:
    """탐색 실행 선언(기본값 없음 -- 모두 부르는 쪽이 출처와 함께 넘긴다, WP-03).

    `front_budget_s`: front 전체 벽시계 예산 B(s) -- spec `search.front_budget_s`(PA-2·U-47 결정 대기). 벽시계는 바깥 정지
    (기록)로만 쓴다. `eval_budget`: 커널 평가 수 예산 E_B(정수) 또는 None -- None 이면 E_B = ⌊B / t_ref⌋(t_ref = 시작점 확인
    평가 시간 중앙값, 한 번 재서 기록)로 정한다. 탐색 안 모든 한도는 평가 수로 센다 -- 같은 E_B 면 결과가 결정론적이다.
    `resistance_bounds_ohm`: θ 저항(`resistance`·`ss_resistance`) 상자 (lo, hi) Ω 또는 None. `sources`: ((필드, 출처 문자열), ...).
    [r6] `capacitance_bounds_f`: θ `capacitance`(DEC-92 engine 커패시터) 상자 (lo, hi) F 또는 None.
    [r10] 두 상자는 **run 단위 명시 재정의**다 -- None 이 아니면 그 종류 모든 원소에 쓴다. None 이면 spec
    `search.theta_bounds` 의 원소별 상자(authoring `ThetaBound`)를 쓰고, 둘 다 없는 원소가 있으면 `search_domain` 이
    SchemaRejectedError(`theta_resistance_bounds_undeclared` / `theta_capacitance_bounds_undeclared`, 없는 원소만). PDK 선언에는
    수동소자 범위가 없어 유도하지 않는다(sizing O13).
    """

    front_budget_s: float
    eval_budget: object
    resistance_bounds_ohm: object
    sources: tuple
    capacitance_bounds_f: object = None


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
    (DEC-80 (i), 모델 오차 미측정이라 (ii) = (i) -- '추정'). [r12] `ties` = ((대표 성분, (묶인 성분, ...)), ...)(`negated` = 부호 −1 로 묶인 θ 전류 구성원, `zeros` = 구조적 0 으로 고정된 θ 전류 성분 -- 3.24) -- 같은 자기동형 궤도 원소의 같은 종류 θ 성분은 변수 하나(대표)로 묶는다(`variables`·`l_cells` 에서 묶인 쪽은 빠진다, 3.24). `current_box` = ((kind, (I_off, I_max)), ...) θ 전류 상자의
    근거(`current_box.py`; I_max 는 잠정 -- 단일 finger 최대 슬라이스, S-3b). 전력 분해능 b_P 는 점마다 다르다
    (`Objectives.power_resolution_w`). `w_min_m`·`grid_m` = PDK 선언 `min_finger_w_m`(difftap.2)·`manufacturing_grid_m`
    (W 하한 제약 S-18 과 b_A = grid_m × w_min_m). `area_budget_m2` = spec 면적 예산(`area_search_m2 <= 값`, 사용자 결정 11) 또는
    None -- 있으면 `current_box` 의 I_max 는 예산이 정하는 참 상한이다(S-3b 닫힘, `search_domain`)."""

    variables: tuple
    l_cells: tuple
    area_resolution_m2: float
    current_box: tuple
    w_min_m: float
    grid_m: float
    area_budget_m2: object = None
    ties: tuple = ()
    negated: tuple = ()
    zeros: tuple = ()


@dataclasses.dataclass(frozen=True)
class EvalKey:
    """평가 키(설계 7.1): (S0 지문, 스키마 지문, L 칸 벡터, 고정 W 지문, θ 값 `float.hex`). ε·출처는 넣지 않는다."""

    context_fp: str
    schema_fp: str
    cells: tuple
    w_fixed_fp: object
    theta_hex: tuple


@dataclasses.dataclass(frozen=True)
class RealizedGeometry:
    """레이아웃 뒤 실현 기하(MOD8 재검증 입력, 계획 N3.17 LY7·LY8, 설계 40 §3.9) -- `evaluate(geometry=)` 가 받는다.
    `w_request` = ((MOS, W(m)), ...) 소자 이름순 -- 실현 W(nf x finger_w) 고정 입력(`size_and_seal(w_request=)`),
    `w_keys` = ((kind, 폭 키), ...) kind 순, S1 MOS kind 전부 -- 실현 폭 슬라이스(커널의 `LutAccess.w_keys`),
    `diffusion` = ((MOS, metrics `DiffusionGeometry`), ...) 소자 이름순 -- 접합 용량의 실현 확산 기하(없는 소자는 LUT 생성 규칙). 지문(`fp_of`)이
    평가 키의 `w_fixed_fp` 다."""

    w_request: tuple
    w_keys: tuple
    diffusion: tuple = ()


@dataclasses.dataclass(frozen=True)
class Objectives:
    """목적 값. `power_w` = power_dc_w, `area_m2` = area_search_m2, `per_rail` = ((레일, I_k), ...),
    `kcl_residual_a`, `gate_area_m2`(graph 필드 `gate_area_m2`), `passive_area_undeclared`, `passive_value_undetermined`(값 미정 수동소자),
    `power_resolution_w` = graph 필드 `power_resolution_w`(writer `metrics_dc`: b_P = Σ_레일 |V_k|·tol_I,k, tol_I,k = 레일 k 에 채널이 닿는
    MOS 의 dc_tol_v·dc_gm 최댓값 -- 봉인 3 KCL 허용오차와 같은 식), 정의된 행이 없으면 None. 이 객체는 필드 읽기 결과다(값 정본은 graph)."""

    power_w: float
    area_m2: float
    per_rail: tuple
    kcl_residual_a: float
    gate_area_m2: float
    passive_area_undeclared: tuple
    passive_value_undetermined: tuple
    power_resolution_w: object = None


@dataclasses.dataclass(frozen=True)
class ConstraintRow:
    """정규화 부등식 c ≥ 0 하나(설계 5절). `active` = c ≤ 1(여유가 분해능 한 칸 이하)."""

    name: str
    c: float
    active: bool


@dataclasses.dataclass(frozen=True, eq=False)
class EvalResult:
    """커널 1회 결과(설계 2.3). `evaluation` = DcEvaluation 또는 None, `failure` = FailureRecord 또는 None,
    `constraints` = ConstraintRow tuple(ε 제약 제외 -- ε 는 키 밖이라 호출부가 붙인다), `cone` = 원뿔 제약 행,
    `unmeasured` = 이 점에서 재지 못한 spec 제약 ((metric, op, 사유), ...) -- 빠뜨리지 않고 '미측정'으로 남긴다(S-1).
    [CM] `warnings` = 판정에 영향 없는 평가 경고 ((코드, ((키, 값), ...)), ...) -- `ss_evaluate` 의 `MetricBundle.warnings`(예 `cm_loop_unconstrained`)."""

    key: EvalKey
    theta: tuple
    status: str
    evaluation: object
    objectives: object
    constraints: tuple
    cone: tuple
    failure: object
    seq: int
    unmeasured: tuple = ()
    warnings: tuple = ()


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
    `aborts` = 재시작을 부른 중단 사유 tuple(순서대로), `frozen` = FD 열이 양방향 실패해 고정한 변수 ((kind, key), ...)."""

    best: object
    eps: object
    minimize: str
    iterations: int
    restarts: int
    stop: str
    history: tuple
    aborts: tuple = ()
    frozen: tuple = ()


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
    `perf` = ((키, 값), ...), `notes` = 열린 항목·판정 보류 기록, `unmeasured_front` = 봉인됐지만 spec ss 제약 중 미측정이 있는
    점끼리의 비지배 점(최종 아님 -- 만족을 판정할 수 없다). `front` 는 봉인 + spec ss 제약 모두 측정·만족(c ≥ 0)인 점만."""

    run_id: str
    front: tuple
    pending_front: tuple
    failed_eps: tuple
    resolution: tuple
    perf: tuple
    notes: tuple
    unmeasured_front: tuple = ()


@dataclasses.dataclass(frozen=True)
class NodeRow:
    """`node_across_front` 한 줄: front 점마다 노드 전압·writer 티어·그 노드에 닿는 소자 op."""

    point_id: str
    status: str
    voltage: float
    tier: object
    devices: tuple
