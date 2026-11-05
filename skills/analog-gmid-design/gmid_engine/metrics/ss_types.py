"""ss_linearize 의 값 형식 -- 데이터 선언 모듈 (설계 design_mod1_lut_mod5_mna 3.2·3.4, 7a design 4.5 단계 5, metrics CONTRACT 7절).

공개 정의는 frozen dataclass 뿐이다. 모두 graph 필드 값(불변·지문 가능)이거나 그 묶음이다.

* `SsDevice`: MOS 하나의 봉인 op 소신호 선형화(소자 총 폭 W 기준 절댓값) -- `device.ss_dev` 값.
  `cap_model` = lut `Caps.model`, `gmb_model`·`junction_model` = 근사·미정 표시(값 자리에 0 을 둔 항목은 반드시 여기 적힌다).
* `OffOp`: `off` 선언 소자 하나의 동작점 (vgs, vds, vsb) 크기(LUT 부호 규약)와 LUT 폭 슬라이스 키 -- `device.off_op` 값. kind·W·L 칸은 없다(`device.kind`·`device.region_decl` 이 정본).
* `OffDelta`: 1차 ΔV -- `node_dv` = ((넷, ΔV), ...) 풀린 노드(넷 이름순), `sources` = ((소자, ΔI_off), ...) 소자 이름순 -- `graph.ss_off_delta` 값.
* `SsCircuit`: S2 열에서 만든 정수 인덱스 소신호 회로 -- 노드 이름 표·원소 이름 표·고정 넷 분류. 필드 `graph.ss_circuit` 의 값이다(writer = 블록 `ss_circuit`,
  조립 자리 하나 -- `metrics_ss`·`ss_nodal`·`metrics_aux` 가 READS 로 읽는다).
* `MetricRequest`: 평가할 (metric 이름, 뷰) 하나 -- spec 제약에서 뽑은 판정 대상(값·op 는 들지 않는다: 제약 임계를
  바꿔도 metric 블록 입력 버전이 바뀌지 않게).
* `MetricBundle`: 한 블록이 낸 metric 결과 묶음 -- `entries` = ((MetricRequest, MetricResult), ...) 요청 순서,
  `approximations` = ((측면, 모형), ...) 정렬(그 묶음 값이 기대는 근사·미정, metrics CONTRACT 6절 M6), `detail` = 키 정렬 쌍.
* `SsEvaluation`: `ss_evaluate` 결과 -- 블록 셋을 쓴 스냅샷과 두 묶음(`ss` = 소신호 제약 metric, `dc` = 전력·면적).
"""
import dataclasses


@dataclasses.dataclass(frozen=True)
class SsDevice:
    """MOS 소신호 값(S, F). gm = ID·(gm/ID), gds = (GDS/w_m)·W, gmb = 같은 보간면 VS 미분 × W/w_m, 용량 = lut `caps`(W 비례),
    cdb·csb = 접합 용량(DEC-91 -- 정본 계산 전이면 0 이고 `junction_model` 이 그 사실을 적는다).
    `lut_rel_tol` = LUT 파라미터(gm·gmb·gds·cgs·cgd·cgb)의 상대 불확실성 ε = (gm/ID)·tol_V(id_equivalent)(metrics CONTRACT 9.1,
    무차원) -- 그 소자의 tol_V 셀이 미정이면 None(분해능을 정하지 않는다)."""

    gm: float
    gmb: float
    gds: float
    cgg: float
    cgs: float
    cgd: float
    cgb: float
    cdb: float
    csb: float
    cap_model: str
    gmb_model: str
    junction_model: str
    lut_rel_tol: object = None


@dataclasses.dataclass(frozen=True)
class OffOp:
    """`off` 선언 소자의 동작점: vgs·vds·vsb(V, LUT 부호 규약 크기), `w_key`(LUT 폭 슬라이스 키)."""

    vgs: float
    vds: float
    vsb: float
    w_key: int


@dataclasses.dataclass(frozen=True)
class OffDelta:
    """off 소자 전류 효과의 1차 노드 전압 변화 ΔV = −G⁻¹·ΔI_off. `node_dv` = ((넷, ΔV), ...) 넷 이름순(풀린 노드), `sources` = ((소자, ΔI_off), ...) 소자 이름순."""

    node_dv: tuple
    sources: tuple


@dataclasses.dataclass(frozen=True)
class SsCircuit:
    """정수 인덱스 소신호 회로. `nodes` = 넷 이름(인덱스 = 위치), `circuit` = `SmallSignalCircuit`(ac_ground 비움 -- 뷰가
    정한다), `resistors`·`capacitors` = 그 회로 원소 순서의 소자 이름, `ground_nets` = 모든 뷰에서 교류접지인 넷(레일 ∪ gate
    전용 미구동 넷), `input_nets` = 입력 포트 넷, `missing` = 값이 없어 스탬프하지 못한 수동소자 이름(비어 있지 않으면 회로는
    불완전하다 -- metric 은 정의 불가)."""

    nodes: tuple
    circuit: object
    resistors: tuple
    capacitors: tuple
    ground_nets: tuple
    input_nets: tuple
    missing: tuple = ()


@dataclasses.dataclass(frozen=True)
class MetricRequest:
    """판정 대상 하나: `metric` = 레지스트리 이름, `view` = spec `ViewDecl`(뷰 없는 metric 은 None 또는 mode none)."""

    metric: str
    view: object = None


@dataclasses.dataclass(frozen=True)
class MetricBundle:
    """metric 결과 묶음. `entries` = ((MetricRequest, MetricResult), ...), `approximations` = ((측면, 모형), ...) 정렬,
    `detail` = (키, 값) 정렬 tuple. [CM] `reports` = 보고 전용 측정 ((이름, ((키, 값), ...)), ...) -- 차동 출력 포트 쌍이 있는 회로의 출력 CM 주입 루프
    T_cm(`cm_loop`: break_nets, dc_db, pm_deg, ugf_hz, undefined), spec 선언과 무관하게 항상(판정은 선언만). `warnings` = ((코드, ((키, 값), ...)), ...)
    -- 예: `cm_loop_unconstrained`(T_cm(0) > 1 인데 pm_cm_ss_deg 제약 미선언)."""

    entries: tuple
    approximations: tuple = ()
    detail: tuple = ()
    reports: tuple = ()
    warnings: tuple = ()


@dataclasses.dataclass(frozen=True)
class SsEvaluation:
    """`ss_evaluate` 결과. `snapshot` = ss·metric 필드까지 쓴 S2 스냅샷, `ss`·`dc` = 두 `MetricBundle`,
    `lineage` = 그 스냅샷을 담은 sizing `DcEvaluation`(봉인 보고 그대로) -- 다음 평가의 `size_and_seal(..., parent=lineage)`·
    `ss_evaluate(lineage.sealed, ...)` 에 넘기면 ss 블록 입력 버전이 같은 필드를 재사용한다(필드가 곧 캐시: 재사용은 그 필드가 든
    스냅샷 lineage 에서만 일어난다)."""

    snapshot: object
    ss: MetricBundle
    dc: MetricBundle
    lineage: object = None

    @property
    def warnings(self):
        """평가 경고(= `ss.warnings`) -- 판정에 영향 없는 보고."""
        return self.ss.warnings
