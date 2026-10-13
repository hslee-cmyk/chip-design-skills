"""GB4 달성가능성 값 형식·어휘 -- 데이터 선언 모듈 (설계 41 §4, 40 §3.4, D-GB4a~f).

공개 정의는 frozen dataclass 와 상수뿐이다(규칙 A 데이터 선언 모듈). 계산은 `curve_checks`·`block_gain_model`·`block_gain_rows`·`block_gain_bound`·
`area_lower_bound`·`headroom_bound`·`dof_report`·`achievability` 가 한다. 모든 값은 tuple·frozen dataclass 라 `fp_of` 로 지문한다.

* 상태 어휘: 인증(`certified`) = 격자 전수(또는 인증된 하한·상한)로 정한 값, 미상(`unknown`) = 계산할 수 없어 판정에 쓰지 않는 값(41 §4.2, §0 '미측정 값의 처리').
* `verdict` 어휘는 값마다 뜻이 다르다: 아래 `VERDICT_*` 상수 주석.
"""
import dataclasses

# ---- 상태
STATUS_CERTIFIED = "certified"
STATUS_UNKNOWN = "unknown"
# ---- 판정(`GainCheck.verdict`·`AreaBound.verdict`·`HeadroomRow.verdict`·`graph/ach: verdict`)
VERDICT_INFEASIBLE = "infeasible"            # 인증된 상한/하한이 목표를 넘지 못한다 -> INFEASIBLE_TARGET(exit 3)
VERDICT_NOT_EXCLUDED = "not_excluded"        # 인증된 값이 목표를 막지 않는다(달성이 보증된다는 뜻이 아니다)
VERDICT_UNDETERMINED = "undetermined"        # 미상이라 판정하지 않고 보고만 한다
VERDICT_NO_TARGET = "no_target"              # 판정할 선언 제약이 없다(보고만)
VERDICT_OK = "ok"
# ---- 블록 상한의 미상 사유(`BlockBound.reason`)
REASON_OVER_BUDGET = "grid_product_over_budget"          # 격자 곱 Π > N_S (41 §4.2 예산 게이트)
REASON_MULTI_INPUT = "block_input_pattern_unsupported"   # 구동 입력이 둘을 넘음
REASON_NO_OUTPUT = "block_output_missing"
REASON_AXIS_RANGE = "axis_range_empty"                   # LUT 격자 위 유효 행이 없다
REASON_NON_CONVERGED = "continuous_axis_not_refined"     # 비단조 축 세분이 상한 안에 끝나지 않았다(41 §4.2 '비단조 축 처리')
REASON_MEMBER_UNKNOWN = "member_bound_unknown"           # 합성 성분(FF 의 입력→탭 상한 등)이 미상
REASON_NO_CURRENT_BOX = "current_box_missing"
# ---- 역할
ROLE_MAIN = "main"
ROLE_FF = "ff"
# ---- 헤드룸 창 종류(41 §4.6)
WINDOW_OUTPUT = "output"
WINDOW_INPUT = "input"
WINDOW_BUFFER = "buffer"
# ---- 경고·정지 사유 코드
WARN_SHORT_L_BIN = "icmr_window_short_l_bin"
REASON_HEADROOM = "headroom_unattainable"
REASON_AREA = "area_budget_below_lower_bound"
REASON_GAIN = "gain_target_above_upper_bound"
REASON_DOF = "overconstrained"
# ---- 곡선 칸 해법(41 §4.1)
METHOD_INVERSE = "inverse"          # 단조 Hermite 칸: 역산 허용(`vgs_for_gm_id`, `vgs_for_current_density`)
METHOD_GRID_ONLY = "grid_only"      # 비단조·Fritsch–Carlson 위반·기울기 미정의: 격자 전수만, 역산은 `lut_hermite_nonmonotone_cell` 로 실패
CELL_HERMITE = "hermite"
CELL_FC_VIOLATION = "fc_violation"
CELL_SLOPE_UNDEFINED = "slope_undefined"
AXIS_VGS = "VGS"
AXIS_VDS = "VDS"
AXIS_VS = "VS"
# ---- 격자 축 종류(`BlockBound.axes` 의 이름)
AXIS_KIND_VGS = "vgs"            # 같은 VGS 묶음(소자 그룹)의 VGS 격자 마디 = gm/ID 축
AXIS_KIND_L = "L"                # L 동치류의 L 앵커
AXIS_KIND_VDS = "vds"            # 소자 그룹의 VDS 격자
AXIS_KIND_VSB = "vsb"            # 소자 그룹의 VS(=VSB) 격자 (소스가 bulk 가 아닌 그룹만)
AXIS_KIND_CURRENT = "current"    # θ 전류 성분(자기동형 궤도당 하나) 배율
AXIS_KIND_RESISTOR = "resistor"  # DC 에 걸리는 저항의 컨덕턴스


@dataclasses.dataclass(frozen=True)
class CurveCheck:
    """곡선 칸 하나의 분류와 해법. `axis` ∈ {VGS, VDS, VS}(그 축을 따라 칸 `cell` = 격자 index `cell` 과 `cell + 1` 사이), (L, vds, vs) = 그 칸이 든 곡선의 나머지 좌표(m, V, V),
    `reason` ∈ {fc_violation, slope_undefined}, `method` = `METHOD_GRID_ONLY`(단조 Hermite 칸은 행으로 내지 않는다 -- 개수만 `SliceCurveCheck`)."""

    kind: str
    w_key: int
    L: float
    vds: float
    vs: float
    axis: str
    cell: int
    reason: str
    method: str


@dataclasses.dataclass(frozen=True)
class SliceCurveCheck:
    """(kind, w_key, 축) 의 칸 분류 개수. `n_cells` = 그 축 전체 칸 수, `n_hermite` = 끝 기울기가 둘 다 정의된 Hermite 칸 수(그 중 `n_violation` 이 Fritsch–Carlson 위반),
    `n_slope_undefined` = 선형으로 보간하는 칸 수. 위반·미정의 칸은 `CurveChecks.grid_only` 행으로도 나온다."""

    kind: str
    w_key: int
    axis: str
    n_cells: int
    n_hermite: int
    n_violation: int
    n_slope_undefined: int


@dataclasses.dataclass(frozen=True)
class CurveChecks:
    """LUT 곡선 검사 → 해법 매핑 결과(41 §4.1). `slices` = `SliceCurveCheck` tuple((kind, w_key, 축) 정렬), `grid_only` = 격자 전용 칸 `CurveCheck` tuple,
    `n_unit_mismatch` = 단위 불일치로 로드를 거부한 슬라이스 수(로드된 LUT 면 늘 0 -- 거부는 `load_lut_set` 의 `lut_unit_mismatch`), `lut_fp` = LUT 지문."""

    slices: tuple
    grid_only: tuple
    n_unit_mismatch: int
    lut_fp: str


@dataclasses.dataclass(frozen=True)
class BlockBound:
    """블록(또는 feedforward 묶음) 하나의 gain 상한 A_i,max (41 §4.2).

    `key` = 블록 키(출력노드 정렬 tuple) 또는 FF 묶음 id 를 담은 1-tuple, `role` ∈ {main, ff}, `status` ∈ {certified, unknown}, `a_max_db`·`b_db` = 인증 때만(dB),
    `pi` = 격자 곱 Π(int, 항상), `axes` = ((축 종류, 크기), ...) 정렬 안 한 정의 순서, `row_condition` = 최대 행의 축별 값((이름, 값), ...) , `reason` = 미상 사유 또는 None,
    `found_db` = 격자 일부(좌표 상승)로 찾은 최대 gain(dB) -- **상한이 아니라 하한 추정**이며 판정에 쓰지 않고 보고만 한다(없으면 None), `members` = 국소 모델의 MOS 이름,
    `n_rows` = 평가한 행 수."""

    key: tuple
    role: str
    status: str
    a_max_db: object
    b_db: object
    pi: int
    axes: tuple
    row_condition: tuple
    reason: object
    found_db: object
    members: tuple
    n_rows: int


@dataclasses.dataclass(frozen=True)
class GainCheck:
    """Σ gain 판정(41 §4.3). `blocks` = 주경로 `BlockBound` tuple(stage 순), `ff` = FF 묶음별 `BlockBound`(role ff), `sum_db` = 인증이면 상한 합(주경로 합, FF 가 있으면
    20·log10(Π A_i,max + Σ A_ff,max) 의 dB) 아니면 None, `b_db` = 주경로 b 의 합, `target_db` = `gain_ss_db >= G` 의 G(없으면 None), `verdict`, `n_unknown`,
    `found_sum_db` = 블록별 `found_db` 합(하한 추정, 보고만), `view` = 뷰 id."""

    view: str
    blocks: tuple
    ff: tuple
    sum_db: object
    b_db: object
    target_db: object
    verdict: str
    n_unknown: int
    found_sum_db: object


@dataclasses.dataclass(frozen=True)
class AreaBound:
    """인증된 면적 하한 A_lb (41 §4.4). `terms` = ((이름, 항 값 m²), ...)(MOS 전류원 항과 커패시터 항), `a_lb_m2`, `budget_m2` = `area_search_m2 <= B` 의 B(없으면 None),
    `b_a_m2` = 면적 분해능(PDK 두 값의 곱), `verdict`, `not_certified` = 하한에 넣지 못한 항 이름((이름, 사유), ...)."""

    a_lb_m2: float
    terms: tuple
    budget_m2: object
    b_a_m2: object
    verdict: str
    not_certified: tuple


@dataclasses.dataclass(frozen=True)
class HeadroomRow:
    """헤드룸 창 하나의 상한(41 §4.6). `path` = 경로 엣지((소자, 엣지 종류 vgs|vds, 아랫 넷, 윗 넷, 비용 V), ...), `window_kind` ∈ {output, input, buffer}, `net` = 창이 걸린 넷,
    `upper_bound_v` = 창 폭 상한(V), `lo_edge_v`·`hi_edge_v` = 창 경계의 바깥 한계(V), `binding_devices`, `best_row` = VGS 비용을 낸 행, `status`, `verdict`,
    `constraint` = 대응 선언 제약((metric, op, 값) 또는 None), `derivation` = ((엣지, 최솟값, 출처 L bin) ...) 유도 기록."""

    window_kind: str
    net: str
    path: tuple
    upper_bound_v: float
    lo_edge_v: float
    hi_edge_v: float
    binding_devices: tuple
    best_row: tuple
    status: str
    verdict: str
    constraint: object
    derivation: tuple


@dataclasses.dataclass(frozen=True)
class DofReport:
    """DOF 보고(41 §4.5). `status` ∈ {overconstrained, free_dof, square}, `structural_rank` = 이분 매칭 크기, `n_variables`·`n_equations`, `unmatched_equations` = 매칭 안 된 등식 이름,
    `free_variables` = 매칭 안 된 변수(탐색이 고르는 자유도) 이름, `numeric_ranks` = 수치 rank((표본 수, rank), ...) -- 단계 B2 몫이라 이 단계는 빈 tuple,
    `competing_pairs` = 같은 변수를 두고 겨루는 등식 쌍((등식, 등식), ...)(매칭에서 같은 변수 뿌리를 갖는 것만)."""

    status: str
    structural_rank: int
    n_variables: int
    n_equations: int
    unmatched_equations: tuple
    free_variables: tuple
    numeric_ranks: tuple
    competing_pairs: tuple


@dataclasses.dataclass(frozen=True)
class LocalInputs:
    """블록 국소 모델 조립에 필요한 회로 전체 표 -- S0 수준 필드 `graph/ach: local_inputs`(writer `achievability`, 설계 40 §2.4.8 v1.9.1 D9; 출발 구간이 같은 필드를 읽는다).
    필드 값이라 모든 칸이 불변 tuple 이다(이름순 (이름, 값) 쌍; S0 수준 스냅샷 코덱이 직렬화). LUT memo 는 칸이 아니다(LUT 손잡이는 부르는 쪽이 따로 준다, §2.4.6).
    사전 질의는 `view`(`LocalView`, 부르는 블록 안에서 한 번 만들고 버리는 작업 값)로 한다.

    `kind`·`pins`·`cls` = 원소별 kind·핀(((단자, 넷), ...) {d,g,s} 또는 {t0,t1})·element_class, `bulk` = MOS 별 bulk 넷(None 이면 교류접지로 둔다), `rails` = 레일 넷 frozenset,
    `orbit` = MOS 별 자기동형 궤도 id(graph `orbits.devices`, 묶지 않을 원소는 자기 고유 값으로 이미 바꿔 둔다), `l_label` = MOS 별 L 동치류 id(모든 derived·ratified 동치류 멤버, 없으면 행 없음),
    `basis_rows` = MOS(및 수동소자) 전류 = ((원천 원소, 계수), ...) (`CurrentBasis.rows`), `free` = θ 전류 원소(기저), `fixed` = (값 선언 이상 전류원, A),
    `cur_rep` = (θ 전류 원소, (대표 원소, 부호 ±1) 또는 (None, 0)=구조적 0)(자기동형 묶음 -- 탐색 변수와 같은 묶음, 없는 원소는 자기 자신 +1),
    `current_box` = (대표 θ 전류 원소, (하한 A, 상한 A)), `element_value` = (수동소자, 선언값 또는 None), `resistor_box` = (θ 저항, (하한 Ω, 상한 Ω)),
    `w_keys` = (kind, 레이아웃 전 폭 슬라이스 키), `grids` = (L, VGS, VDS, VS) LUT 격자 float tuple 넷(모든 슬라이스 공통, lut 불변식),
    `attach` = (넷, 전체 회로에서 그 넷에 닿는 DC 전도 소자 단자 수(MOS drain·source, 저항 단자))(블록 밖 넷이 다른 DC 가지를 가지는지 -- 아니면 DC 에 뜬 막다른 넷),
    `node_colour`·`device_colour` = (이름, 구조 색 순위)(`dc_colour` -- 정점마다 유일하고 이름이 정하지 않는다; 순회·합산 순서를 이름이 아니라 이 순위로 정해 이름 치환에 결과가 비트 단위로 같게 한다)."""

    kind: tuple
    pins: tuple
    cls: tuple
    bulk: tuple
    rails: frozenset
    orbit: tuple
    l_label: tuple
    basis_rows: tuple
    free: tuple
    fixed: tuple
    cur_rep: tuple
    current_box: tuple
    element_value: tuple
    resistor_box: tuple
    w_keys: tuple
    grids: tuple
    node_colour: tuple
    device_colour: tuple
    attach: tuple

    @property
    def view(self):
        """사전 질의용 `LocalView`(읽을 때마다 새로 만든다 -- 부르는 블록이 호출 안에서 한 번 읽어 넘긴다)."""
        return LocalView(dict(self.kind), {n: dict(p) for n, p in self.pins}, dict(self.cls), dict(self.bulk), self.rails, dict(self.orbit),
                         dict(self.l_label), dict(self.basis_rows), self.free, dict(self.fixed), dict(self.cur_rep), dict(self.current_box),
                         dict(self.element_value), dict(self.resistor_box), dict(self.w_keys), self.grids, dict(self.node_colour),
                         dict(self.device_colour), dict(self.attach))


@dataclasses.dataclass(frozen=True, eq=False)
class LocalView:
    """`LocalInputs.view` -- 같은 칸을 이름 → 값 사전으로 편 작업 값(필드 값이 아니다; 블록 국소 모델 조립·헤드룸 경로가 읽는다). 칸 뜻은 `LocalInputs` 와 같다."""

    kind: dict
    pins: dict
    cls: dict
    bulk: dict
    rails: frozenset
    orbit: dict
    l_label: dict
    basis_rows: dict
    free: tuple
    fixed: dict
    cur_rep: dict
    current_box: dict
    element_value: dict
    resistor_box: dict
    w_keys: dict
    grids: tuple
    node_colour: dict
    device_colour: dict
    attach: dict


@dataclasses.dataclass(frozen=True)
class BlockSpec:
    """국소 모델 하나의 대상: `key`, `role`, `members` = MOS 이름(정렬), `passives` = 수동소자 이름(정렬), `inputs`·`outputs` = 넷, `ground` = 교류접지 넷,
    `excite` = ((넷, 가중), ...) 뷰 여기, `nodes` = 블록 노드 집합(교류접지 포함 가능), `drive` = 여기를 줄 넷 tuple 을 직접 정할 때(None 이면 `inputs` 에서 교류접지를 뺀 것)."""

    key: tuple
    role: str
    members: tuple
    passives: tuple
    inputs: tuple
    outputs: tuple
    ground: frozenset
    excite: tuple
    nodes: tuple
    drive: object = None


@dataclasses.dataclass(frozen=True, eq=False)
class AxisSpec:
    """격자 축 하나. `kind` ∈ AXIS_KIND_*, `label` = 축을 가리키는 이름 tuple(그룹 멤버 또는 원소), `size` = 격자 점 수, `values` = 축 값 배열(vgs·L·vds·vsb 는 LUT 격자 값,
    current·resistor 는 A·S 의 로그 격자), `continuous` = 비단조 축 세분 대상(current·resistor)."""

    kind: str
    label: tuple
    size: int
    values: object
    continuous: bool


@dataclasses.dataclass(frozen=True)
class MosLocal:
    """국소 모델의 MOS 하나. `*_axis` = `BlockModel.axes` index(-1 = 해당 없음: `vds_axis` -1 은 diode 로 VDS = VGS 마디, `vsb_axis` -1 은 VSB = 0 격자 마디),
    `current` = 전류 = Σ (축 index 또는 -1(상수), 계수 또는 A) tuple."""

    name: str
    kind: str
    d: str
    g: str
    s: str
    bulk: object
    vgs_axis: int
    l_axis: int
    vds_axis: int
    vsb_axis: int
    current: tuple


@dataclasses.dataclass(frozen=True)
class ResLocal:
    """국소 모델의 저항 하나. `axis` -1 이면 고정 컨덕턴스 `g_fixed`(S)."""

    name: str
    a: str
    b: str
    axis: int
    g_fixed: object


@dataclasses.dataclass(frozen=True, eq=False)
class BlockModel:
    """블록 국소 소신호 모델(ω → 0, 커패시터 열림). `nodes` = 미지 넷, `driven` = 구동 넷, `patterns` = 여기 패턴 tuple(각 ((넷, 가중), ...)),
    `outputs` = ((넷, 부호), ...) (gain = max_패턴 |Σ 부호·V|), `axes`, `pi` = 격자 곱, `normalized_axis` = 공통 전류 배율로 뺀 축의 이름 또는 None."""

    key: tuple
    role: str
    nodes: tuple
    driven: tuple
    patterns: tuple
    outputs: tuple
    mos: tuple
    res: tuple
    axes: tuple
    pi: int
    normalized: tuple
