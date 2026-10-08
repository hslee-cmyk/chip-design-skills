"""잡음 metric 의 값 형식 -- 데이터 선언 모듈 (설계 41 §7.1·7.3, 단위 U8).

공개 정의는 dataclass 뿐이다.

* `NoiseDecl`: spec 에서 온 잡음 선언 -- `feedback`(spec feedback 소자 이름 tuple, 결정 대기·거부면 None), `sampling_caps`(테스트벤치 샘플링
  커패시터 이름), `input_cells`(((여기 넷 tuple, 감지 넷 tuple, 입력 셀 MOS 이름 tuple), ...) -- S1v 전달 뷰의 첫 이득 블록 input 셀, 41 §7.1).
  graph 필드 값이 아니라 `ss_evaluate` 가 받아 블록 추가 인자로 넘기는 불변 입력이다(지문 가능).
* `NoiseDevice`: MOS 하나의 LUT 잡음 값(기준 폭 값을 `w_m/W` 배한 것) -- `a`·`b`(S_vg(f) = a/f^ef + b, V²/Hz, `b` None = 미상),
  `tol_flicker`·`tol_thermal`(LUT 칸 상대 허용오차 -- 미정 None), `failure`(LUT 질의 실패 사유, 정상이면 None).
* `NoiseInput`: `metrics_ss` 의 잡음 추가 인자 -- 소자별 값, `f_lo`(LUT 가 실측한 가장 낮은 잡음 주파수 -- 적분·평탄값의 하한),
  `kt`(볼츠만 상수 × LUT 측정 온도, J), `decl`.
* `NoiseSources`: 한 소신호 회로의 잡음원 표(MOS 채널 전류 잡음 gm²·S_vg, 저항 4kT/R) -- 노드 인덱스 공간.
* `NoisePlan`: 한 회로·선언에서 정한 폐루프 모드 구조 -- 자유 입력 넷(되먹임 소자의 입력 포트 쪽 단자)·샘플링 커패시터 위치.
* `NoiseTransfer`: 한 계·ω 격자의 수반 풀이 결과(잡음원마다 출력까지의 전달 Z_k, 전달 뷰 H, 파라미터·ω 1차 미분).
* `NoiseSetup`: `noise_analysis` 한 호출의 입력 묶음(한 요청의 계·관측·잡음원 표).
* `NoiseAnalysis`: 레지스트리 결과 형식 -- 네 metric 값 중 요청한 하나만 채운다(나머지 None), `undefined` = 그 값의 정의 불가 사유,
  `resolution`·`contrib`·`detail` = 분해능·소자별 기여 표·보고 상세.
"""
import dataclasses


@dataclasses.dataclass(frozen=True)
class NoiseDecl:
    """잡음 선언. `feedback` 이 None 이면 결정 대기·미제공 -- 폐루프 모드를 정할 수 없다. 빈 tuple 이면 되먹임 없음."""

    feedback: object = None
    sampling_caps: tuple = ()
    input_cells: tuple = ()


@dataclasses.dataclass(frozen=True)
class NoiseDevice:
    """MOS 하나의 잡음 값. `a`/`b` 는 폭 W 소자의 값(V²/Hz), `b` None = 열잡음 평탄값 미상(`b_status` 가 사유)."""

    name: str
    a: object = None
    b: object = None
    ef: object = None
    b_status: object = None
    tol_flicker: object = None
    tol_thermal: object = None
    failure: object = None


@dataclasses.dataclass(frozen=True)
class NoiseInput:
    """`metrics_ss` 잡음 추가 인자. `devices` = NoiseDevice tuple(이름순), `f_lo` = 가장 낮은 LUT 잡음 주파수(Hz) 또는 None."""

    decl: NoiseDecl
    devices: tuple
    f_lo: object
    kt: float


@dataclasses.dataclass(frozen=True)
class NoiseSources:
    """잡음원 표(원소 N 개). `a`·`b` = 전류가 b 에서 a 로 흐르는 노드 쌍(노드 인덱스), `thermal`[N] = 열 성분 단측 PSD(A²/Hz, 미상 NaN),
    `flicker`[N] = flicker 계수 gm²·A(주파수 f 에서 PSD = flicker/f^ef, 저항은 0), `ef`[N], `tol_thermal`·`tol_flicker`[N] = 상대 허용오차(없음 0,
    미정 NaN), `gm`[N] = MOS gm(저항 0), `gm_param`[N] = ParameterSet 의 gm 파라미터 번호(없으면 -1), `labels`[N], `is_mos`[N],
    `problems` = ((코드, 소자 이름 tuple), ...) -- 열 성분 미상·LUT 질의 실패·잡음 값 없음."""

    labels: tuple
    is_mos: object
    a: object
    b: object
    thermal: object
    flicker: object
    ef: object
    tol_thermal: object
    tol_flicker: object
    gm: object
    gm_param: object
    problems: tuple = ()


@dataclasses.dataclass(frozen=True)
class NoisePlan:
    """폐루프 모드 구조. `mode` ∈ closed(되먹임 소자의 입력 포트 쪽 넷을 자유 노드로 둔 계) / open(되먹임 없음 -- 입력 고정) / undefined(`reason`).
    `free_nets` = 자유 입력 넷 이름 frozenset, `caps` = ((커패시터 이름, 회로 커패시터 순번), ...), `reason` = 정의 불가 코드 + `detail`."""

    mode: str
    free_nets: frozenset = frozenset()
    caps: tuple = ()
    reason: object = None
    detail: tuple = ()
    cap_problems: tuple = ()


@dataclasses.dataclass(frozen=True, eq=False)
class NoiseTransfer:
    """수반 풀이 결과(ω 격자 k 개, 잡음원 N 개, 파라미터 P 개). `z`[k, N] = 잡음원 단위 전류(b -> a)의 관측까지 전달, `h`[k] = 전달 뷰 H
    (뷰 열이 없으면 None), `dz`[k, P, N]·`dh`[k, P] = 파라미터 미분(파라미터 집합이 없으면 None), `dz_dw`[k, N]·`dh_dw`[k] = ω 미분(요청 시).
    `undefined` = 풀이 불가 사유."""

    omegas: object
    z: object = None
    h: object = None
    dz: object = None
    dh: object = None
    dz_dw: object = None
    dh_dw: object = None
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True, eq=False)
class NoiseSetup:
    """`noise_analysis` 입력. `system` = 이 요청의 `MnaSystem`, `row` = 관측 행, `column` = 전달 뷰 열(폐루프·열 없음 None),
    `sources` = NoiseSources, `parameters` = `ParameterSet`, `noise` = NoiseInput, `plan` = NoisePlan, `ss` = SsCircuit,
    `input_devices` = 입력 셀 MOS 이름 tuple 또는 None(미정), `poles` = 이 계의 유한 극점, `mode` = closed | open."""

    system: object
    row: int
    column: object
    sources: NoiseSources
    parameters: object
    noise: NoiseInput
    plan: NoisePlan
    ss: object
    input_devices: object
    poles: tuple
    mode: str


@dataclasses.dataclass(frozen=True)
class NoiseAnalysis:
    """레지스트리 결과 형식. 요청한 metric 의 필드만 채운다. `contrib` = ((소자 이름, ((키, 값), ...)), ...), `detail` = (키, 값) tuple,
    `resolution` = 값과 같은 단위의 분해능(미정 None)."""

    th_in_v2hz: object = None
    fc_in_hz: object = None
    excess_th: object = None
    out_int_vrms: object = None
    undefined: tuple = ()
    resolution: object = None
    contrib: tuple = ()
    detail: tuple = ()
