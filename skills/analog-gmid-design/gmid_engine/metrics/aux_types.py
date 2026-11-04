"""U7 metric 결과·구조 입력의 값 형식 -- 데이터 선언 모듈 (설계 40 §3.8-8, 41 §2, §1.12.2).

공개 정의는 frozen dataclass 뿐이다. 모두 tuple·float·str 로만 이뤄져 graph 필드 값(불변·지문 가능)으로 쓴다.

**구조 입력**(S1v 를 metrics 가 쓰는 만큼만 한 번 풀어 놓은 읽기 전용 모형 -- `metric_structure` 가 만든다. metrics 계산이 graph 의 `S1v` 전체를
들고 다니지 않고 이름 없는 구조 사실만 받는다):
* `BlockStruct`: 블록 하나(키·종류·stage·입력 넷·출력 넷·노드 집합·멤버 소자).
* `FfStruct`: feedforward 묶음 하나(41 §1.12.2: 탭·merge·멤버·합류 블록·처음 우회한 블록).
* `ViewStruct`: 전달 뷰 하나(여기·감지·주경로 블록 사슬·FF 묶음·입력 셀·신호 경로 소자).
* `MetricStructure`: 뷰들의 묶음.

**결과 형식**(레지스트리 `RegisteredMetric.source_type`; 값 필드 + `undefined`(mna_types.Undefined tuple)):
* `OffsetAnalysis` -- `sigma_in_mv`·`excess`(+ 소자별 기여 표 `contrib`).
* `OffsetSystematic` -- `sys_mv`.  `MirrorRatio` -- `sigma_pct`.  `SwingIcmr` -- `swing_out_v`·`icmr_v`·`icm_margin_v`.
* `FfRatio` -- `ratio`.
* 보고 전용: `BlockGain`·`BlockResidual`·`FfContribution`·`NqsRatio`·`LsNode`·`LsFields`·`GateResult`·`CoupledResidual`.
* `MismatchSource` -- offset·미러비 σ 의 PDK mismatch 모델 입력, `SatDevice` -- 스윙·ICMR 경로 합의 MOS 하나.
* `NodalSystem` -- 필드 `graph.ss_nodal` 값(봉인점 노달 계: G·g_bound·인수분해), `IcmConfig` -- 필드 `graph.icm_config` 값(ICMR 측정 구성).
"""
import dataclasses

import numpy


@dataclasses.dataclass(frozen=True)
class MismatchSource:
    """소자 mismatch σ 의 PDK 입력 묶음. `models` = ((kind, core `PdkMismatchModel`), ...) kind 정렬, `sha256` = 그 PDK 선언 파일 sha256(지문용 출처).
    블록 입력 버전 지문은 (sha256, kind 목록) -- 모델 본문(bin 수백 개)을 매 평가마다 직렬화하지 않는다(`JunctionSource` 와 같은 방식)."""

    models: tuple
    sha256: str

    def __canonical__(self):
        return (self.sha256, tuple(kind for kind, _model in self.models))

    @classmethod
    def from_decl(cls, pdk_decl):
        return cls(tuple(pdk_decl.mismatch_models), pdk_decl.decl_sha256)


@dataclasses.dataclass(frozen=True)
class BlockStruct:
    """블록 하나의 구조 사실. `key` = 출력노드 정렬 tuple, `kind` ∈ {gain, buffer, composite}, `stage` = 정수, `inputs`·`outputs` = 넷 이름 tuple,
    `nodes` = 블록 노드 집합(입력 넷 포함, 교류접지 제외), `input_cells` = 역할이 input 인 MOS 이름 tuple. 블록 국소 모델의 스탬프 소자는 이 노드 집합에 단자가
    닿는 소자로 정한다(S1v `roles` 가 아니라 netlist 인접 -- 버퍼 블록도 같은 규칙)."""

    key: tuple
    kind: str
    stage: int
    inputs: tuple
    outputs: tuple
    nodes: tuple
    input_cells: tuple = ()


@dataclasses.dataclass(frozen=True)
class FfStruct:
    """feedforward 묶음 하나. `id` = `<탭>-><merge>`, `tap`·`merge` = 넷, `members` = 신호 셀 ∪ 바이어스 셀 ∪ 부하 셀 이름 정렬 tuple,
    `merge_block` = merge 노드를 출력으로 갖는 주경로 블록 키, `bypassed` = 처음 우회한 주경로 블록 키(B_b), `bypassed_input_cells` = 그 블록의 input 셀(gm_in 의 출처)."""

    id: str
    tap: str
    merge: str
    members: tuple
    merge_block: tuple
    bypassed: tuple
    bypassed_input_cells: tuple


@dataclasses.dataclass(frozen=True)
class ViewStruct:
    """전달 뷰 하나의 구조 사실. `excite` = ((넷, 가중), ...), `sense` = 감지 넷 정렬 tuple, `blocks` = 주경로 블록(stage 순, 같은 stage 는 키순),
    `ff` = FfStruct tuple, `input_cells` = 첫 이득 블록(최소 stage)의 input 셀, `signal_devices` = 순방향 신호 셀 MOS 이름 정렬 tuple (nqs_ratio 입력),
    `pole_nets` = 극점 노드 넷 정렬 tuple, `directions` = ((넷, topology, charge ((소자, β|σ|κ), ...), discharge (...)), ...) -- ls_fields 입력(DEC-65)."""

    id: str
    excite: tuple
    sense: tuple
    blocks: tuple
    ff: tuple = ()
    input_cells: tuple = ()
    signal_devices: tuple = ()
    pole_nets: tuple = ()
    directions: tuple = ()


@dataclasses.dataclass(frozen=True)
class MetricStructure:
    """`ViewStruct` 모음 -- 전달 뷰 순서는 S1v 뷰 순서."""

    views: tuple = ()


@dataclasses.dataclass(frozen=True)
class SatDevice:
    """포화 경로 합의 MOS 하나(`ls_swing` 입력). `polarity` = +1(NMOS)/−1(PMOS), `d`·`g`·`s` = 넷, `vgs_v` = |VGS|(봉인 op, VSB 포함),
    `sat_v` = VDSAT + tol_vdsat(None 이면 LUT 열이 없거나 tol 미정), `sat_tol_v`·`vgs_tol_v` = 각 엣지 값의 허용오차(분해능 전파 -- 없으면 None),
    `linear` = 선형 영역 선언 소자(포화 판정 제외)."""

    label: str
    polarity: int
    d: str
    g: str
    s: str
    vgs_v: float
    sat_v: object
    sat_tol_v: object = None
    vgs_tol_v: object = None
    linear: bool = False


@dataclasses.dataclass(frozen=True)
class OffsetContribution:
    """소자 하나의 입력 환산 offset 분산 기여. `device`, `variance_v2` = (Z_i·gm_i·σ_i / A_dm)² (V²), `share` = 전체 분산 중 비율,
    `sigma_vgs_v` = 게이트 환산 σ, `z_ohm` = 소자 드레인 전류 -> 출력 전달 임피던스, `matching` = 그 소자가 든 matching 그룹 kind 쌍(없으면 빈 문자열)."""

    device: str
    variance_v2: float
    share: float
    sigma_vgs_v: float
    z_ohm: float
    matching: str = ""


@dataclasses.dataclass(frozen=True)
class OffsetAnalysis:
    """`offset_in_sigma_mv`·`offset_excess` 값 묶음. `sigma_in_mv` = 입력 환산 랜덤 offset 1σ, `excess` = σ_in / 입력 셀 소자만의 같은 합(입력 셀이 없으면 None),
    `a_dm` = 부호 있는 DC 차동 이득, `contrib` = 기여 큰 순 `OffsetContribution`, `resolution_mv`·`excess_resolution` = 분해능, `solve_residual` = 풀이 상대 잔차."""

    sigma_in_mv: object
    excess: object
    a_dm: object
    contrib: tuple = ()
    resolution_mv: object = None
    excess_resolution: object = None
    solve_residual: object = None
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class OffsetSystematic:
    """`offset_sys_mv` 값 묶음. `output_error_v` = 입력 0 일 때 출력 오차(차동 = Vop − Vom, 단일 = V_out − 선언 기준 DC), `reference` = ('differential' | 넷 이름 tuple)."""

    sys_mv: object
    output_error_v: object = None
    a_dm: object = None
    resolution_mv: object = None
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class MirrorRatio:
    """`mirror_ratio_sigma_pct` 값 묶음. `sigma_pct` = 그룹·쌍 최댓값, `groups` = ((kind, 멤버 tuple, 기준 소자 또는 '', σ pct), ...)."""

    sigma_pct: object
    groups: tuple = ()
    resolution_pct: object = None
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class SwingIcmr:
    """`swing_out_v`·`icmr_v`·`icm_margin_v` 값 묶음(P N3.8 경로 합).

    `out_ranges` = ((출력 넷, V_lo, V_hi, V_dc), ...), `window` = (Vin,min, Vin,max)(레일로 자른 입력 창), `v_icm` = 판정에 쓴 입력 DC(선언값 또는 해의 y_icm),
    `required_input_cm_v` = (value, lo, hi) 또는 None(입력 DC 대기 SP-2 회로에서 보고), `input_dc` = 'declared' | 'pending'(대기 -- 해의 y_icm 으로 계산),
    `bounds` = ((넷, lo, hi), ...) 모든 넷의 경로 합 구간(`ls_fields` 의 신호 셀 VGS_max 입력)."""

    swing_out_v: object
    icmr_v: object
    icm_margin_v: object
    out_ranges: tuple = ()
    window: tuple = ()
    v_icm: object = None
    required_input_cm_v: object = None
    input_dc: str = ""
    swing_resolution: object = None
    icmr_resolution: object = None
    margin_resolution: object = None
    bounds: tuple = ()
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class FfRatio:
    """`ff_gm_ratio` 값 묶음. `ratio` = FF 묶음 r_ff 중 최댓값, `per_ff` = ((id, r_ff, G_ff, gm_in), ...)."""

    ratio: object
    per_ff: tuple = ()
    resolution: object = None
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class FfContribution:
    """FF 묶음 하나의 경로 기여(41 §1.12.2-4). `gain_db` = 20·log10|기여 전달비|, `sign` = 부호(+1/−1), `g_ff` = 탭 전압 -> merge 단락 전류 (S)."""

    id: str
    gain_db: object
    sign: int
    g_ff: object = None


@dataclasses.dataclass(frozen=True)
class BlockGain:
    """블록 국소 모델 결과(41 §2.1). `gain` = 부호 있는 V(out)/V(in)(차동은 차 / 차), `gain_db`, `zout_ohm` = 입력 접지·출력 단위 전류 응답,
    `contributions` = ((경로 이름, gain), ...)(복합 블록 경로별·FF 기여), `decomposed_only` = 되먹임 수동소자가 블록을 가로질러 값이 '분해값'뿐인가,
    `solve_residual` = 풀이 상대 잔차, `node_v` = ((넷, 국소 해 전압), ...) 넷순 -- 블록 노드와 국소 해가 푼 내부 넷의 전압(사슬의 다음 블록 입력).
    블록 국소 모델이 스탬프한 소자 `members`(이름 정렬)."""

    key: tuple
    gain: object
    gain_db: object
    zout_ohm: object
    contributions: tuple = ()
    decomposed_only: bool = False
    solve_residual: object = None
    node_v: tuple = ()
    members: tuple = ()
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class BlockResidual:
    """전달 뷰 하나의 분해 잔차(41 §2.2). `gain_residual_db` = gain_ss_db − 20·log10|A_decomp|(A_decomp = 주경로 블록 곱 + FF 기여),
    `blocks` = `BlockGain` tuple, `ff_contrib` = `FfContribution` tuple, `rout_residual_ohm` = 전회로 rout − 마지막 블록 Z_out(출력 포트 감지가 있을 때),
    `full_gain_db` = 전회로 DC 이득(본 모듈 노달 풀이), `solve_residual` = 풀이 상대 잔차 최댓값,
    `read_devices` = 분해가 읽는 소자(블록 국소 모델이 스탬프한 소자 ∪ FF 묶음 소자, 이름 정렬) -- 감도 게이트가 이 밖의 소자를 건드린다."""

    view: str
    gain_residual_db: object
    blocks: tuple = ()
    ff_contrib: tuple = ()
    rout_residual_ohm: object = None
    full_gain_db: object = None
    decomposed_gain_db: object = None
    solve_residual: object = None
    read_devices: tuple = ()
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class NqsRatio:
    """`nqs_ratio` = ugf_ss_hz / 신호 경로 소자 최소 f_T. `min_ft_hz`, `limiting_device`."""

    ratio: object
    min_ft_hz: object = None
    limiting_device: str = ""
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class LsNode:
    """극점 노드 하나의 대신호 필드. `c_slew_farad` = 슬루 등가 용량, `i_charge_a`·`i_discharge_a` = 방향별 최대 전류(공급 셀이 없거나 상한 미상 셀이 있으면 None),
    `slew_charge_v_per_s`·`slew_discharge_v_per_s` = 전류 / 용량, `sources` = ((방향 'charge'|'discharge', 소자, 셀 종류 β|σ|κ, 최대 전류 또는 None), ...),
    `i_charge_res_a`·`i_discharge_res_a` = 방향별 전류의 분해능(없으면 None)."""

    net: str
    c_slew_farad: object
    i_charge_a: object = None
    i_discharge_a: object = None
    slew_charge_v_per_s: object = None
    slew_discharge_v_per_s: object = None
    sources: tuple = ()
    i_charge_res_a: object = None
    i_discharge_res_a: object = None


@dataclasses.dataclass(frozen=True)
class LsFields:
    """`ls` 필드 묶음: 노드별 `LsNode`, `driving` 선언이 있으면 출력 포트의 부하 피크 전류 대비 값."""

    nodes: tuple = ()
    load_peak_margin_a: object = None
    undefined: tuple = ()


@dataclasses.dataclass(frozen=True)
class GateResult:
    """감도 게이트 결과(40 §3.8-2). `ok` = 오류 없음, `checks` = ((섭동 이름, 분해 변화, MNA 변화, ε, 오류 여부), ...), `errors` = 오류 섭동 이름 tuple."""

    ok: bool
    checks: tuple = ()
    errors: tuple = ()
    epsilon: object = None


@dataclasses.dataclass(frozen=True)
class CoupledResidual:
    """결합 잔차 측정 요약(41 §2.4). `median_db` = r̂(중앙값), `spread_db` = r̂_spread(최대 − 최소), `count` = 잔차를 잰 봉인 표본 수. 표본이 없으면 값은 None."""

    median_db: object
    spread_db: object
    count: int


@dataclasses.dataclass(frozen=True, eq=False)       # ndarray 칸이라 값 비교(==)는 `fp_of`(내용 지문)로 한다 -- 필드 단위 == 는 모호한 진리값 오류
class NodalSystem:
    """봉인점 소신호 DC 극한(용량 개방)의 노달 계 -- 필드 `graph.ss_nodal` 값(writer `ss_nodal`, 계획 N3.8 '봉인점 DC 야코비안').
    `nodes` = 노드 이름 tuple(인덱스 = 위치, `ss_circuit.nodes`), `fixed` = 고정 노드 색인 frozenset(교류접지 ∪ 입력 넷), `g` = 컨덕턴스 행렬 G(S),
    `g_bound` = G 조립 오차의 항목별 상계 E(S, `conductance_matrix(bound=True)`), `factor` = `nodal_factor(g, fixed)` 튜플.
    ndarray 는 모두 읽기 전용(`writeable=False`)이다 -- 생성할 때 건 배열을 잠근다(소유권을 이 값에 넘긴다). 지문(`__canonical__`)은 (nodes, fixed, g, g_bound) 바이트 --
    `factor` 는 (g, fixed) 의 결정적 파생이라 따로 싣지 않는다."""

    nodes: tuple
    fixed: frozenset
    g: object
    g_bound: object
    factor: tuple

    def __post_init__(self):
        for array in (self.g, self.g_bound) + tuple(part for part in self.factor if isinstance(part, numpy.ndarray)):
            array.flags.writeable = False

    def __canonical__(self):
        return (self.nodes, tuple(sorted(self.fixed)), self.g.shape, self.g.tobytes(), self.g_bound.shape, self.g_bound.tobytes())


@dataclasses.dataclass(frozen=True)
class IcmConfig:
    """ICMR 측정 구성 결과 -- 필드 `graph.icm_config` 값(writer `icm_config`, 계획 N3.8 'ICMR 측정 구성').
    `config` ∈ {"servo", "as_is_single_input"} 또는 None(정의 불능). `pivot_a_e` = 여기 방향 → 감지의 봉인점 DC 극한 전달(V/V), `pivot_resolution` = 그 판정 분해능
    δA_num(V/V) -- 두 칸은 출력 전용(결과 JSON). `vcm0`·`vcm_lo`·`vcm_hi` = V_cm 칸(입력 포트 전압 평균의 봉인점·두 끝 상태 값, V; 한 포트라도 측정 실패면 끝은 None).
    `undefined` = `Undefined` tuple(구성이 None 이면 원소 하나, quantity `"icm_config"`)."""

    config: object
    pivot_a_e: object
    pivot_resolution: object
    vcm0: object
    vcm_lo: object
    vcm_hi: object
    undefined: tuple = ()
