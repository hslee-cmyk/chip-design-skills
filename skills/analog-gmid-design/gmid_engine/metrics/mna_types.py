"""MOD5 수치 핵심의 결과 레코드 -- 데이터 선언 모듈 (설계 design_mod1_lut_mod5_mna 3.3·3.4, 7a design 2.4).

* `Undefined`: 값이 정의되지 않은 사유(값으로 담는다 -- MOD5 는 정의 불가로 예외를 던지지 않고, 판정 계층이 문맥
  (탐색 전 구조 판정 / 탐색 중 평가)에 따라 N3.14 분류로 옮긴다). `category` ∈ {definitional, numeric, structural}.
* `MnaSystem`: 조립 결과(ω 무관 실수 G·C, 여기 열 BG·BC, 관측 행들) -- 조립은 1회, 주파수마다 풀이만 한다.
* `Roots`: (G, −C) 일반화 고유값(극점)과 관측 행 × 열마다 전달함수 영점 -- 격자 배치·상단 괄호에만 쓴다.
* `DcLimit`: ω → 0 극한 해(용량 전용 노드는 전하 보존 식으로 대체).
* `SystemResponse`: 한 MnaSystem 의 공유 ω 격자 위 응답(축 = ω, 관측 행, 여기 열). ω = 0 이 첫 행. 정의 안 된 값은 NaN.
* `PointSolution`: ω 한 점의 풀이(관측 행 × 열마다 관측값과 사후 오차 추정).
* 루프 이득 인수 -- T = 인수들의 곱. 두 형식이 같은 규약을 따른다(`analyze_loop`·`find_crossing`·`phase_lag` 가 형식을
  구분하지 않고 읽는다): 속성 `response`(공유 격자의 출처), `samples`(격자 위 인수 값), `poles`·`zeros`(상단 괄호용 근),
  `undefined`(격자 표본의 정의 불가 사유). 격자 밖 한 점은 `PointSolution` → (복소값, 사후 오차, 사유)로 평가한다
  (`_helpers_product.product_at`).
  - `Factor`: 응답의 (관측 행, 열) 원소 하나.
  - `ProbeFactor`: 절단 회로 계의 Middlebrook 이중 주입 루프 이득 T = (Tv·Ti − 1)/(Tv + Ti + 2)(`probe_factor`).
* `CutCircuit`: 루프 절단 회로(`cut_circuit`) -- 절단 노드 쌍과 프로브 여기 열·관측.
* `Crossing`: |T| = level 교차 하나(없으면 omega None + `undefined`).
* `LoopAnalysis`: 한 인수 묶음에서 한 번 계산한 주파수 양(gain·UGF·GBW·위상 여유) -- metric 들이 공유한다.
* `OutputResistance`, `ResponseRatio`, `SupplyCurrents`, `AreaSearch`: 나머지 metric 의 값 묶음.
* `MetricResult`: 이름으로 읽은 metric 값 하나(값 또는 정의 불가 사유) + 분해능.
* 분해능(NFR-5 '격자 분해능', metrics CONTRACT 9절): `ParameterSet`(LUT 파라미터 불확실성), `ResponseSensitivity`(한 계·한 ω 의
  1차 민감도), `Resolution`(결과 필드 하나의 분해능).

numpy 배열 필드는 생성 때 쓰기 금지로 바꾼다(불변 스냅샷).
"""
import dataclasses

import numpy

UNDEFINED_CATEGORIES = ("definitional", "numeric", "structural")


def _freeze(record, *names):
    for name in names:
        array = numpy.array(getattr(record, name))
        array.setflags(write=False)
        object.__setattr__(record, name, array)


@dataclasses.dataclass(frozen=True)
class Undefined:
    """정의 불가 사유 하나. `quantity`: 정의 안 된 양(결과 묶음의 필드 이름 또는 "response"·"system"),
    `code`: 사유 키, `category`: `UNDEFINED_CATEGORIES` 원소, `detail`: (키, 값) 정렬 tuple."""

    quantity: str
    code: str
    category: str
    detail: tuple = ()

    def __post_init__(self):
        if self.category not in UNDEFINED_CATEGORIES:
            raise ValueError("Undefined.category %r 은 %r 밖이다" % (self.category, UNDEFINED_CATEGORIES))
        object.__setattr__(self, "detail", tuple(sorted(dict(self.detail).items())))


@dataclasses.dataclass(frozen=True)
class MnaSystem:
    """조립된 소신호 계. 미지수 n 개, 여기 열 m 개, 관측 r 개.

    * `nodes`: 미지수 노드 인덱스(정렬). `fixed_nodes`: 고정 노드(교류접지 ∪ 전압 구동, 정렬).
    * `G`, `C`: (n, n) 실수. `BG`, `BC`: (n, m) 실수 -- 열 j 의 우변은 `BG[:, j] + jω·BC[:, j]`(전하 주입은 `BC` 에만).
    * `sense_rows`: (r, n) 관측 행, `sense_direct`: (r, m) 고정 노드에서 바로 오는 관측 성분.
    * `excitations`: 열 순서의 `Excitation` 레코드, `senses`: 행 순서의 `Sense` 레코드.
    * `charge_nodes`: 컨덕턴스가 하나도 닿지 않는 미지수 노드(전체 G 행이 0 -- 용량으로만 연결)의 미지수 번호(0 기준).
      DC 극한에서 그 행의 KCL 을 전하 보존 식으로 바꾼다(`solve_dc_limit`).
    * `defects`: 값에 따라 생기는 구조 결함(`Undefined`, quantity "system") -- 있으면 응답 전체가 정의되지 않는다.
    """

    nodes: tuple
    fixed_nodes: tuple
    G: object
    C: object
    BG: object
    BC: object
    sense_rows: object
    sense_direct: object
    excitations: tuple
    senses: tuple
    charge_nodes: tuple = ()
    defects: tuple = ()

    def __post_init__(self):
        _freeze(self, "G", "C", "BG", "BC", "sense_rows", "sense_direct")

    @property
    def columns(self):
        """여기 열 이름(열 순서)."""
        return tuple(e.name for e in self.excitations)


@dataclasses.dataclass(frozen=True)
class Roots:
    """`poles`: 유한 극점(복소 tuple, 정렬). `zeros[r][j]`: 관측 행 r · 열 j 전달함수의 유한 영점 tuple(순수 전하 열은
    빈 tuple -- 영점 = 같은 노드 전류 열 영점 ∪ {0} 이라 계산하지 않는다, `Factor` 로 쓰지 않는다)."""

    poles: tuple
    zeros: tuple


@dataclasses.dataclass(frozen=True)
class DcLimit:
    """ω → 0 극한 관측값 `values` (r, m) 실수(정의 안 된 열은 NaN)와 사유 `undefined`."""

    values: object
    undefined: tuple = ()

    def __post_init__(self):
        _freeze(self, "values")


@dataclasses.dataclass(frozen=True)
class SystemResponse:
    """`omegas`: (k,) rad/s, 첫 원소 0. `values`: (k, r, m) 복소 관측값(정의 안 된 값은 NaN). `undefined`: 사유."""

    system: MnaSystem
    roots: Roots
    omegas: object
    values: object
    undefined: tuple = ()

    def __post_init__(self):
        _freeze(self, "omegas", "values")

    @property
    def dc(self):
        """ω = 0 관측값 (r, m) 실수(극한 해)."""
        return self.values[0].real


@dataclasses.dataclass(frozen=True)
class PointSolution:
    """ω 한 점: `values` (r, m) 복소 관측값, `errors` (r, m) 사후 오차 추정(반복 개선 1회 보정량의 관측 크기).
    특이면 값·오차가 NaN 이고 `undefined` 에 사유."""

    omega: float
    values: object
    errors: object
    undefined: tuple = ()

    def __post_init__(self):
        _freeze(self, "values", "errors")


@dataclasses.dataclass(frozen=True)
class Factor:
    """루프 이득 인수 하나: `response` 의 관측 행 `row`, 열 `column` 원소(관측이 하나인 계는 row 0)."""

    response: SystemResponse
    column: int
    row: int = 0

    @property
    def samples(self):
        """공유 격자 위 인수 값 (k,) 복소."""
        return self.response.values[:, self.row, self.column]

    @property
    def poles(self):
        """상단 괄호용 극점(계의 극점)."""
        return self.response.roots.poles

    @property
    def zeros(self):
        """상단 괄호용 영점(그 관측 행·열의 영점)."""
        return self.response.roots.zeros[self.row][self.column]

    @property
    def undefined(self):
        """격자 표본의 정의 불가 사유(열을 적은 사유는 이 열 것만)."""
        return tuple(u for u in self.response.undefined if dict(u.detail).get("column", self.column) == self.column)


@dataclasses.dataclass(frozen=True)
class CutCircuit:
    """루프 절단 회로(`cut_circuit`, 7a design 2.2 L3).

    * `circuit`: 절단 단자를 새 노드로 옮긴 `SmallSignalCircuit`(교류접지는 원래 그대로).
    * `cuts`: 적용한 `LoopCut` tuple(입력 순서).
    * `pairs`: (원래 노드 n_k, 새 노드 x_k) tuple, n 오름차순. x_k = 원래 회로 최대 노드 인덱스 뒤에 n 순서로 붙는다.
    * `excitations`: 프로브 여기 열 4k 개 -- 단위 전류 I(n_1..n_k), I(x_1..x_k), 단위 전하 Q(n_1..n_k), Q(x_1..x_k).
    * `senses`: 관측 2k 개 -- V(n_1..n_k), V(x_1..x_k). `build_mna(circuit, excitations, senses)` 로 조립 1회.
    """

    circuit: object
    cuts: tuple
    pairs: tuple
    excitations: tuple
    senses: tuple


@dataclasses.dataclass(frozen=True)
class ProbeFactor:
    """절단 회로 계의 Middlebrook 루프 이득 인수(`probe_factor`, 7a design 2.4).

    * `response`: 절단 회로 계의 `SystemResponse`(공유 격자). `pairs`: (n_k, x_k) 노드 쌍, `weights`: 쌍마다 가중 w_k.
    * `rows`: V(n_1..n_k), V(x_1..x_k) 관측 행 번호. `current_columns`·`charge_columns`: 같은 노드 순서의 전류·전하 주입 열
      번호, `current_scales`·`charge_scales`: 그 열의 주입 크기(Z = 관측 / 크기).
    * `samples`: 격자 위 T (k,) 복소(정의 안 된 점은 NaN). `poles`·`zeros`: T 의 유한 극점·영점(상단 괄호용,
      1/(1 + T) = 1/(1 + Tv) + 1/(1 + Ti) 가 한 계의 전달함수라는 항등식에서 증강 pencil 로 구한다).
    * `undefined`: 격자 표본의 정의 불가 사유(`loop_cut_mixed_charge`, `loop_probe_singular`, `den_zero`, 응답 사유).
    """

    response: SystemResponse
    pairs: tuple
    weights: tuple
    rows: tuple
    current_columns: tuple
    charge_columns: tuple
    current_scales: tuple
    charge_scales: tuple
    samples: object = ()
    poles: tuple = ()
    zeros: tuple = ()
    undefined: tuple = ()

    def __post_init__(self):
        _freeze(self, "samples")


@dataclasses.dataclass(frozen=True)
class Crossing:
    """|T(jω)| = `level` 교차. 없으면 `omega` 가 None 이고 `undefined` 가 사유(`Undefined`).

    `value` = 교차점 T, `lo`·`hi` = 마지막 괄호, `steps` = 이분 횟수, `resolution` = 정지 시 |T| 사후 오차."""

    level: float
    omega: object = None
    value: object = None
    lo: object = None
    hi: object = None
    steps: int = 0
    resolution: object = None
    undefined: object = None


@dataclasses.dataclass(frozen=True)
class LoopAnalysis:
    """인수 묶음 하나의 주파수 양. 정의되지 않으면 None 이고 `undefined` 에 사유(quantity = 필드 이름).

    * `dc_value`: T(0)(실수 극한). `gain_db` = 20·log10|T(0)|.
    * `ugf`: |T| = 1 교차, `ugf_hz` = ω/2π.
    * `f3db`: |T| = |T(0)|/√2 교차, `gbw_hz` = |T(0)|·f_3dB, `gbw_ugf_gap_hz` = gbw − ugf(단일 극점 가정 진단).
    * `phase_lag_rad`: T(0) 대비 UGF 까지 누적 위상 지연, `phase_margin_deg` = 180° − 지연.
    """

    dc_value: object
    gain_db: object
    ugf: object
    f3db: object
    ugf_hz: object
    gbw_hz: object
    gbw_ugf_gap_hz: object
    phase_lag_rad: object
    phase_margin_deg: object
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class OutputResistance:
    """출력 포트 전류 주입 열 `column`(관측 행 `row`)의 ω = 0 응답 / 주입 전류. 음수(양되먹임)는 값이 아니라 정의 불가
    `negative_output_resistance`(오케스트레이터 결정 2026-10-07, 7a design Q3) -- `<=` 제약이 음수로 통과하지 않는다."""

    column: int
    rout_ohm: object
    undefined: tuple = ()
    row: int = 0


@dataclasses.dataclass(frozen=True)
class ResponseRatio:
    """같은 MnaSystem 두 여기 열의 ω = 0 응답 크기비(dB) -- CMRR·PSRR 일반형. `row` = 관측 행(분해능 계산이 읽는다)."""

    num_column: int
    den_column: int
    ratio_db: object
    undefined: tuple = ()
    row: int = 0


@dataclasses.dataclass(frozen=True)
class SupplyCurrents:
    """레일별 DC 전류(레일에서 회로로 들어가는 방향).

    * `per_rail`: (레일 노드, I_k) 정렬 tuple. `counted_rails`: 합에 넣는 선언 레일.
    * `supply_current_dc` = Σ_{k∈counted} I_k (DEC-78 목적 축). `power_dc_w` = Σ_k V_k·I_k.
    * `kcl_residual_amp` = Σ_k I_k (0 이어야 한다 -- 레일 원점 이동 불변성의 오차 크기).
    """

    per_rail: tuple
    counted_rails: tuple
    supply_current_dc: float
    power_dc_w: float
    kcl_residual_amp: float
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class AreaSearch:
    """DEC-79 (a) 탐색 축 면적. `passive_area_undeclared`: 단위 면적 선언이 없어 0 으로 둔 수동소자 label(매 실행 보고)."""

    area_search_m2: float
    gate_area_m2: float
    passive_area_m2: float
    passive_area_undeclared: tuple = ()
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class ParameterSet:
    """LUT 에서 온 MOS 소신호 파라미터와 그 불확실성(`lut_parameters`, metrics CONTRACT 9절).

    * `params`: ((MOS 순번, 파라미터 이름), ...) -- 값이 0 이 아닌 LUT 파라미터만, MOS 순번·`LUT_PARAMETERS` 순서.
    * `delta`: (P,) Δp = ε_d·|p|(ε_d = 그 MOS 의 LUT 상대 불확실성 `rel_tol[d]`). `rel_tol`: MOS 순번 순서의 ε_d(None = 미정).
    * 단위 스탬프 항목(파라미터 p 를 1, 나머지를 0 으로 둔 `mos_stamps` 항목을 모은 것 -- 노드 인덱스 공간):
      `rows`·`cols`·`values` (E,), `capacitive` (E,) bool(C 항목이면 참), `owner` (E,) 그 항목의 파라미터 번호.
    * `undetermined`: ε 가 None 인 MOS 순번(비어 있지 않으면 분해능을 정하지 않는다 -- 미정을 0 으로 두지 않는다)."""

    params: tuple
    delta: object
    rel_tol: tuple
    rows: object
    cols: object
    values: object
    capacitive: object
    owner: object
    undetermined: tuple = ()

    def __post_init__(self):
        _freeze(self, "delta", "rows", "cols", "values", "capacitive", "owner")


@dataclasses.dataclass(frozen=True)
class ResponseSensitivity:
    """한 계·한 ω 의 관측값과 1차 민감도(`response_sensitivity`, metrics CONTRACT 9절).

    * `values`: (r, m) 관측값(ω = 0 은 `solve_dc_limit` 과 같은 전하 보존 극한 식), `errors`: (r, m) 같은 분해로 반복 개선
      1회 한 보정량의 관측 크기(`solve_point` 와 같은 사후 오차).
    * `d_param`: (P, r, m) ∂V/∂p(`ParameterSet.params` 순서), `d_omega`: (r, m) ∂V/∂ω(ω = 0 이면 None).
    * 정의되지 않으면(구조 결함·특이) 배열 필드가 None 이고 `undefined` 에 사유."""

    omega: float
    values: object = None
    errors: object = None
    d_param: object = None
    d_omega: object = None
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class Resolution:
    """결과 묶음 필드 하나의 분해능(그 필드와 같은 단위, `metric_resolutions`, metrics CONTRACT 9절).
    `lut` = LUT 조회 불확실성의 1차 최악 전파 Σ|∂q/∂p|·Δp, `numeric` = MNA 풀이 사후 오차의 1차 전파,
    `value` = max(lut, numeric) -- 하나라도 정하지 못하면(None) None."""

    quantity: str
    value: object
    lut: object = None
    numeric: object = None


@dataclasses.dataclass(frozen=True)
class MetricResult:
    """metric 하나: 값(float) 또는 None + 사유(`Undefined` tuple). 판정 계층이 사유를 N3.14 분류로 옮긴다.
    `resolution` = 값의 분해능(metric 과 같은 단위, CONTRACT 9절 -- NFR-5 '격자 분해능'). 값이 None 이거나 정하지 못하면 None."""

    name: str
    value: object
    undefined: tuple = ()
    resolution: object = None
