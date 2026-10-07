"""MOD5 수치 핵심의 결과 레코드 -- 데이터 선언 모듈 (설계 design_mod1_lut_mod5_mna 3.3·3.4).

* `MnaSystem`: 조립 결과(ω 무관 실수 G·C, 여기 열 BG·BC, 관측 행) -- 조립은 1회, 주파수마다 풀이만 한다.
* `Roots`: (G, −C) 일반화 고유값(극점)과 열마다 관측 전달함수 영점 -- 격자 배치·상단 괄호에만 쓴다.
* `SystemResponse`: 한 MnaSystem 의 공유 ω 격자 위 응답(행 = ω, 열 = 여기 열). ω = 0 이 첫 행.
* `PointSolution`: ω 한 점의 풀이(열마다 관측값과 사후 오차 추정).
* `Factor`: 루프 이득 인수 하나 = (응답, 열 번호). 루프 이득 T = 인수들의 곱.
* `Crossing`: |T| = level 교차 하나(없으면 omega None + 사유).
* `LoopAnalysis`: 한 인수 묶음에서 한 번 계산한 주파수 metric 값(gain·UGF·GBW·PM) -- 같은 응답을 metric 이 공유한다.
* `OutputResistance`, `SupplyCurrents`, `AreaSearch`: 나머지 metric 의 값 묶음.

numpy 배열 필드는 생성 때 쓰기 금지로 바꾼다(불변 스냅샷).
"""
import dataclasses

import numpy


def _freeze(record, *names):
    for name in names:
        array = numpy.array(getattr(record, name))
        array.setflags(write=False)
        object.__setattr__(record, name, array)


@dataclasses.dataclass(frozen=True)
class MnaSystem:
    """조립된 소신호 계. 미지수 n 개, 여기 열 m 개.

    * `nodes`: 미지수 노드 인덱스(정렬). `fixed_nodes`: 고정 노드(교류접지 ∪ 전압 구동, 정렬).
    * `G`, `C`: (n, n) 실수. `BG`, `BC`: (n, m) 실수 -- 열 j 의 우변은 `BG[:, j] + jω·BC[:, j]`.
    * `sense_row`: (n,) 관측 행, `sense_direct`: (m,) 고정 노드에서 바로 오는 관측 성분.
    * `excitations`: 열 순서의 `Excitation` 레코드, `sense`: `Sense` 레코드.
    * `dc_floating`: 미지수 블록 G 의 행 또는 열이 0 인 노드(DC 경로 없음, 용량으로만 연결) -- DC 풀이가 거부한다.
    """

    nodes: tuple
    fixed_nodes: tuple
    G: object
    C: object
    BG: object
    BC: object
    sense_row: object
    sense_direct: object
    excitations: tuple
    sense: object
    dc_floating: tuple = ()

    def __post_init__(self):
        _freeze(self, "G", "C", "BG", "BC", "sense_row", "sense_direct")

    @property
    def columns(self):
        """여기 열 이름(열 순서)."""
        return tuple(e.name for e in self.excitations)


@dataclasses.dataclass(frozen=True)
class Roots:
    """`poles`: 유한 극점(복소 tuple, 정렬). `zeros`: 열마다 유한 영점 tuple."""

    poles: tuple
    zeros: tuple


@dataclasses.dataclass(frozen=True)
class SystemResponse:
    """`omegas`: (k,) rad/s, 첫 원소 0. `values`: (k, m) 복소 관측값. `dc`: (m,) 실수 = values[0]."""

    system: MnaSystem
    roots: Roots
    omegas: object
    values: object

    def __post_init__(self):
        _freeze(self, "omegas", "values")

    @property
    def dc(self):
        """ω = 0 관측값(실수 해)."""
        return self.values[0].real


@dataclasses.dataclass(frozen=True)
class PointSolution:
    """ω 한 점: `values` (m,) 복소 관측값, `errors` (m,) 사후 오차 추정(반복 개선 1회 보정량의 관측 크기)."""

    omega: float
    values: object
    errors: object

    def __post_init__(self):
        _freeze(self, "values", "errors")


@dataclasses.dataclass(frozen=True)
class Factor:
    """루프 이득 인수 하나: `response` 의 `column` 번째 열."""

    response: SystemResponse
    column: int


@dataclasses.dataclass(frozen=True)
class Crossing:
    """|T(jω)| = `level` 교차. 없으면 `omega` 가 None 이고 `reason` 이 사유.

    `value` = 교차점 T, `lo`·`hi` = 마지막 괄호, `steps` = 이분 횟수, `resolution` = 정지 시 |T| 사후 오차."""

    level: float
    omega: object = None
    value: object = None
    lo: object = None
    hi: object = None
    steps: int = 0
    resolution: object = None
    reason: object = None


@dataclasses.dataclass(frozen=True)
class LoopAnalysis:
    """인수 묶음 하나의 주파수 metric. 값이 정의되지 않으면 None 이고 `undefined` 에 (metric 이름, 사유) 가 있다.

    * `dc_value`: T(0)(실수). `gain_ss_db` = 20·log10|T(0)|.
    * `ugf`: |T| = 1 교차, `ugf_ss_hz` = ω/2π.
    * `f3db`: |T| = |T(0)|/√2 교차, `gbw_ss_hz` = |T(0)|·f_3dB, `gbw_ugf_gap_hz` = gbw − ugf(단일 극점 가정 진단).
    * `phase_lag_rad`: T(0) 대비 UGF 까지 누적 위상 지연, `pm_ss_deg` = 180° − 지연.
    """

    dc_value: float
    gain_ss_db: object
    ugf: Crossing
    f3db: Crossing
    ugf_ss_hz: object
    gbw_ss_hz: object
    gbw_ugf_gap_hz: object
    phase_lag_rad: object
    pm_ss_deg: object
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class OutputResistance:
    """출력 포트 단위 전류 주입 열의 ω = 0 응답 / 주입 전류(부호 그대로)."""

    column: int
    rout_ss_ohm: float
    undefined: tuple = ()


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
