"""MOD1 LUT 데이터 선언 모듈 -- 로드 입력 선언·불변 LUT 묶음·조회 결과 레코드 (설계 MOD1 2.2·2.3·2.5).

공개 정의는 frozen dataclass 뿐이다(데이터 선언 모듈, 구조 규칙 A 보충 (1)). 계산은 다른 파일이 한다.

* 축 순서는 `AXES` = (L, VGS, VDS, VS) 이고 슬라이스 배열 배치 `[L, VGS, VDS, VS]` 와 같다. VS 축은 source 기준
  body 전위 크기(vsb)다(슬라이스 생성기 sign_convention: source 접지, body = -VS(nfet) / +VS(pfet)).
* 슬라이스 배열 값은 그 폭 `w_m` 에서의 절댓값(정규화 안 함). 정규화(`ID·L/w_m`)는 조회 함수가 한다.
* numpy 배열 필드는 읽기 전용(`writeable=False`)으로 만든다. 그래서 내용 지문은 `__canonical__` 이 파일 sha256
  등 출처 값으로 대신 말한다(배열 바이트를 매번 해시하지 않는다 -- DF-13 의 '내용 해시는 비싸다'를 로드 1회로 해소).
"""
import dataclasses

AXES = ("L", "VGS", "VDS", "VS")
TOL_V_METRICS = ("gm_id_inverse", "id_equivalent")


@dataclasses.dataclass(frozen=True)
class LutSpec:
    """로드에 필요한 PDK·파일 형식 선언(부르는 쪽이 PDK 선언에서 채운다 -- 엔진은 숫자를 박지 않는다).

    `manufacturing_grid_m`: PDK 제조 격자(m, tlef MANUFACTURINGGRID). 폭 키 = round(w_m / 이 값).
    `min_finger_w_m`: ((kind, 최소 finger 폭 m), ...) -- `widths()` 의 하한(PDK difftap 규칙).
    `device_kinds`: ((manifest device 이름, kind), ...) -- 슬라이스 소자 이름을 엔진 kind 로.
    `cap_column_suffix`: ((kind, 기준 LUT 열 접미사), ...) -- 기준 LUT npz 의 `CGG<접미사>` 등 열 이름.
    """

    manufacturing_grid_m: float
    min_finger_w_m: tuple
    device_kinds: tuple
    cap_column_suffix: tuple


@dataclasses.dataclass(frozen=True)
class SliceSource:
    """manifest 의 슬라이스 한 줄과 그 파일에서 읽은 출처 값."""

    kind: str
    device: str
    w_m: float
    w_key: int
    path: str
    sha256: str
    conditions: tuple
    model_files_sha256: tuple


@dataclasses.dataclass(frozen=True)
class LutProvenance:
    """LUT 묶음의 출처: manifest·슬라이스·기준 LUT 파일 sha256, 측정 조건(corner·temp_c·recorded)."""

    manifest_path: str
    manifest_sha256: str
    generator_sha256: str
    slices: tuple
    cap_path: str
    cap_sha256: str
    cap_conditions: tuple


@dataclasses.dataclass(frozen=True, eq=False)
class DcSlice:
    """DC 폭 슬라이스 하나(소자 kind·폭 키 하나). 로그 배열은 그 배열의 최소 양수값을 바닥으로 만든다
    (데이터를 자르지 않음 -- 옛 상수 바닥 1e-18·1e-30 대체). `on_mask` = (ID > 0) & (GM > 0) 격자점.

    `floors`: ((배열 이름, 바닥값), ...), `nonpositive`: ((배열 이름, 0 이하 원소 수), ...).
    원시 GM·GDS 배열은 로그 배열과 on_mask 로 충분해 보관하지 않는다(메모리).
    """

    kind: str
    w_key: int
    w_m: float
    sha256: str
    grids: tuple
    grids_list: tuple
    VGS_grid: object
    ID: object
    VTH: object
    on_mask: object
    log_ID: object
    log_GM: object
    log_GDS: object
    floors: tuple
    nonpositive: tuple

    def __canonical__(self):
        return (self.kind, self.w_key, self.sha256)


@dataclasses.dataclass(frozen=True, eq=False)
class CapTable:
    """기준 LUT 의 용량 열(한 kind). `CGS`·`CGB` 는 열이 없으면 None. `w_ref_m` = 이 배열이 잰 폭.

    `basis`: w_ref_m 채택 근거 ((키, 값), ...) -- 메타 기록인지, 어느 슬라이스와 ID 가 맞았는지.
    """

    kind: str
    sha256: str
    grids: tuple
    grids_list: tuple
    CGG: object
    CGD: object
    CGS: object
    CGB: object
    w_ref_m: float
    basis: tuple

    def __canonical__(self):
        return (self.kind, self.sha256, self.w_ref_m, self.basis)


@dataclasses.dataclass(frozen=True, eq=False)
class LutSet:
    """불변 LUT 묶음. `slice_map`: {(kind, w_key): DcSlice}, `cap_map`: {kind: CapTable} (읽기 전용 매핑).

    `fp` = `lut_fingerprint(provenance, cap 채택 근거)` -- memo 키와 S0 입력에 쓴다.
    """

    spec: LutSpec
    provenance: LutProvenance
    slice_map: object
    cap_map: object
    fp: str

    def __canonical__(self):
        return self.fp


@dataclasses.dataclass(frozen=True)
class OpPoint:
    """한 동작점 조회 결과(슬라이스 폭 w_m 기준).

    `IDu` = ID·L/w_m(A, W/L=1 기준 전류), `gm_over_id`(1/V), `gm_gds`(무차원), `gds_per_w` = GDS/w_m(S/m), `vth`(V).
    """

    IDu: float
    gm_over_id: float
    gm_gds: float
    gds_per_w: float
    vth: float


@dataclasses.dataclass(frozen=True, eq=False)
class Curve:
    """고정 (L, VDS, VS) 에서 VGS 격자 위 곡선. `id_vals` = 슬라이스 폭에서의 ID(A), `gm_id_vals` = gm/ID(1/V).

    배열은 읽기 전용 numpy 배열이다.
    """

    vgs_grid: object
    id_vals: object
    gm_id_vals: object


@dataclasses.dataclass(frozen=True)
class TargetSolution:
    """목표(gm 또는 ID)를 만드는 강반전 분지 위 동작점. `id_a`·`gm_s` 는 소자 총 폭 W 기준 값."""

    vgs: float
    gm_id: float
    id_a: float
    gm_s: float


@dataclasses.dataclass(frozen=True)
class Caps:
    """소자 총 폭 W 의 용량(F). `model`: "lut_cgs_cgb"(열 있음) 또는 "cgg_minus_cgd_at_gs"(cgs = cgg - cgd, cgb = 0)."""

    cgg: float
    cgd: float
    cgs: float
    cgb: float
    model: str


@dataclasses.dataclass(frozen=True)
class TolVCell:
    """tol_V 표 한 칸((kind, w_key, L 앵커, VDS)). 값은 VS·목표 전체의 최댓값(V), 정의 안 되면 None.

    `gm_id_inverse_v`: |LOO 곡선에서 gm/ID 역산한 VGS - 참 VGS|. `id_equivalent_v`: |ln ID_loo - ln ID| / (gm/ID).
    `n_targets`: 목표 수, `n_inverse_failed`: LOO 곡선에 강반전 해가 없어 역산이 실패한 목표 수(값에 넣지 않음).
    """

    gm_id_inverse_v: object
    id_equivalent_v: object
    n_targets: int
    n_inverse_failed: int


@dataclasses.dataclass(frozen=True)
class CurveRow:
    """곡선 검사 한 줄((kind, w_key, L 앵커)). 격자점 값만 쓴다(보간 없음).

    `n_curves`: 검사한 (VDS, VS) 곡선 수, `n_skipped`: ID 또는 GM 에 0 이하 격자점이 있어 뺀 곡선 수,
    `n_branch_nonmonotonic`: 정점 오른쪽(강반전 분지)에서 gm/ID 가 한 번이라도 오른 곡선 수,
    `max_branch_rise`: 그 상승의 최대 상대 크기(오른 양 / 정점 값), `gm_id_max`: 곡선 정점의 최댓값,
    `gm_gds_max`: 격자 전체 GM/GDS 최댓값(GB4 입력).
    """

    kind: str
    w_key: int
    L: float
    n_curves: int
    n_skipped: int
    n_branch_nonmonotonic: int
    max_branch_rise: float
    gm_id_max: float
    gm_gds_max: float


@dataclasses.dataclass(frozen=True)
class CurveReport:
    """LUT 곡선 검사 보고(`rows` = CurveRow tuple, (kind, w_key, L) 정렬)."""

    lut_fp: str
    rows: tuple
