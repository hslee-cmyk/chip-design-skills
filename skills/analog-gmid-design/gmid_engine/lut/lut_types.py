"""MOD1 LUT 데이터 선언 모듈 -- 로드 입력 선언·불변 LUT 묶음·조회 결과 레코드 (설계 MOD1 2.2·2.3·2.5).

공개 정의는 frozen dataclass 뿐이다(데이터 선언 모듈, 구조 규칙 A 보충 (1)). 계산은 다른 파일이 한다.

* L 은 LUT 앵커이거나, 같은 PDK 모델 bin 안의 두 이웃 앵커 사이일 때만 그 둘로 선형 보간한다(사용자 결정 2026-10-07,
  bin 경계를 건너는 보간 금지). bin 지도(`LBinMap`)는 로드 때 슬라이스가 기록한 모델 파일에서 한 번 만든다.
* 축 순서는 `AXES` = (L, VGS, VDS, VS) 이고 슬라이스 배열 배치 `[L, VGS, VDS, VS]` 와 같다. VS 축은 source 기준
  body 전위 크기(vsb)다(슬라이스 생성기 sign_convention: source 접지, body = -VS(nfet) / +VS(pfet)).
* 슬라이스 배열 값은 그 폭 `w_m` 에서의 절댓값(정규화 안 함). 정규화(`ID·L/w_m`)는 조회 함수가 한다.
* 보간 방법은 축별이다(DEC-87, lut/CONTRACT.md 4.2): ln ID 는 VGS·VDS 축 2점 cubic-Hermite(기울기 = 저장 GM/ID·GDS/ID),
  VS·L 축 선형. gm/ID 는 그 다항식의 VGS 미분으로 정의한다. 로드 때 Hermite 칸마다 Fritsch–Carlson 단조 조건을 검사해 둔다.
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
    """manifest 의 슬라이스 한 줄과 그 파일에서 읽은 출처 값. `model_paths`: ((meta 상대 경로, 실제 경로), ...) --
    meta `model_files_sha256` 의 파일을 meta `pdk_root` 아래에서 찾아 sha256 을 대조한 것(정렬)."""

    kind: str
    device: str
    w_m: float
    w_key: int
    path: str
    sha256: str
    conditions: tuple
    model_files_sha256: tuple
    model_paths: tuple = ()


@dataclasses.dataclass(frozen=True)
class LBin:
    """PDK 모델 bin 하나(L 방향): `.model` 이름과 그 블록의 `lmin`·`lmax`(m)."""

    model: str
    lmin: float
    lmax: float


@dataclasses.dataclass(frozen=True)
class LBinMap:
    """슬라이스(또는 용량 표) 하나의 L bin 지도 -- 로드 때 한 번 계산해 표와 함께 보관한다.

    `model_files`: 읽은 모델 파일(슬라이스 meta 의 상대 경로) tuple, `w_bin`: 고른 W bin `(wmin, wmax)`,
    `bins`: 그 W bin 행의 L bin(`LBin`, lmin 오름차순), `anchor_bin`: L 앵커마다 그 앵커가 속한 `bins` index.
    bin 정보가 없으면(모델 파일 기록 없음·bin 블록 없음) 모두 빈 값 -- `bins == ()` 이 '지도 없음' 이다.
    """

    model_files: tuple
    w_bin: object
    bins: tuple
    anchor_bin: tuple


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
    `l_bins` = 그 폭의 L bin 지도(`LBinMap`, lut/CONTRACT.md 4.0).

    `floors`: ((배열 이름, 바닥값), ...), `nonpositive`: ((배열 이름, 0 이하 원소 수), ...).
    원시 GM·GDS 배열은 로그 배열과 on_mask 로 충분해 보관하지 않는다(메모리).

    Hermite 보조(로드 1회, lut/CONTRACT.md 1.4·4.2): `vds_slope_ok` = (ID > 0) & (GDS > 0) 격자점(VDS 기울기 GDS/ID 정의),
    `fc_ok_vgs`[L, VGS 칸, VDS, VS]·`fc_ok_vds`[L, VGS, VDS 칸, VS] = 그 칸의 Hermite 가 Fritsch–Carlson 단조 조건을
    만족하면 참(기울기가 정의되지 않아 선형으로 보간하는 칸도 참), `hermite_fc` = (("VDS", Hermite 칸 수, 위반 칸 수),
    ("VGS", ...)). 위반 칸은 조회에서 그 축 선형으로 보간한다(lut/CONTRACT.md 4.2).
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
    l_bins: LBinMap
    vds_slope_ok: object
    fc_ok_vgs: object
    fc_ok_vds: object
    hermite_fc: tuple

    def __canonical__(self):
        return (self.kind, self.w_key, self.sha256)


@dataclasses.dataclass(frozen=True, eq=False)
class CapTable:
    """기준 LUT 의 용량 열(한 kind). `CGS`·`CGB` 는 열이 없으면 None. `w_ref_m` = 이 배열이 잰 폭.
    `l_bins` = 채택 폭과 같은 슬라이스의 L bin 지도(같은 슬라이스가 없으면 빈 지도).

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
    l_bins: LBinMap

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
    """고정 (L, VDS, VS) 에서 VGS 격자 마디의 곡선. `id_vals` = 슬라이스 폭에서의 ID(A), `log_id_vals` = ln ID,
    `gm_id_vals` = gm/ID(1/V, 마디의 VGS 기울기 -- 기울기 자료가 정의되지 않은 마디는 NaN). 마디 사이는 VGS 칸마다
    (ln ID, gm/ID) 를 값·기울기로 쓰는 cubic-Hermite 다(op_point 와 같은 곡면, lut/CONTRACT.md 4.2).
    `cell_ok`[j] = VGS 칸 [j, j+1] 의 모서리(가중치 0 이 아닌 L·VDS·VS 격자 칸)가 모두 Fritsch–Carlson 단조 조건을
    만족(거짓이면 그 칸은 선형 -- 역산 함수가 그 칸의 근을 내지 않는다).

    배열은 읽기 전용 numpy 배열이다.
    """

    vgs_grid: object
    id_vals: object
    gm_id_vals: object
    log_id_vals: object
    cell_ok: object


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
    """tol_V 표 한 칸((kind, w_key, L 앵커, VDS)). 값은 보간 축 leave-one-out(운영 보간과 같은 방법)의 오차를 축마다
    Richardson 환산(÷ 2^p, p = 그 축·지표의 보간 차수, lut/CONTRACT.md 5절)한 셀 안 최댓값(V), 정의 안 되면 None.

    `gm_id_inverse_v`: |LOO 곡선에서 gm/ID 역산한 VGS - 참 VGS| / 2^p. `id_equivalent_v`: |ln ID_loo - ln ID| / (gm/ID) / 2^p.
    `n_targets`: gm/ID 역산 시도 수((목표, 축) 쌍), `n_inverse_failed`: 그중 LOO 곡선에 강반전 해가 없던 수(값에 넣지 않음).
    `gm_id_inverse_loo_v`·`id_equivalent_loo_v`: 환산 전 LOO 값(간격 2배 격자의 오차)의 셀 안 최댓값(진단·환산 검증용).
    """

    gm_id_inverse_v: object
    id_equivalent_v: object
    n_targets: int
    n_inverse_failed: int
    gm_id_inverse_loo_v: object = None
    id_equivalent_loo_v: object = None


@dataclasses.dataclass(frozen=True)
class CurveRow:
    """곡선 검사 한 줄((kind, w_key, L 앵커)). 격자점 값만 쓴다(보간 없음).

    `n_curves`: 검사한 (VDS, VS) 곡선 수(건너뛴 곡선 제외), `n_skipped`: ID 또는 GM 에 0 이하 격자점이 있어 뺀 곡선 수,
    `n_branch_nonmonotonic`: 정점 오른쪽(강반전 분지)에서 gm/ID 가 한 번이라도 오른 곡선 수,
    `max_branch_rise`: 그 상승의 최대 상대 크기(오른 양 / 정점 값), `gm_id_max`: 곡선 정점의 최댓값,
    `gm_gds_max`: 격자 전체 GM/GDS 최댓값(GB4 입력), `n_hermite_nonmonotone`: 그 L 앵커의 Hermite 칸(VGS·VDS 축) 중
    Fritsch–Carlson 단조 조건 위반 칸 수(로드 기록 `DcSlice.fc_ok_vgs`·`fc_ok_vds` 에서 셈, 계획 N3.7).
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
    n_hermite_nonmonotone: int


@dataclasses.dataclass(frozen=True)
class CurveReport:
    """LUT 곡선 검사 보고(`rows` = CurveRow tuple, (kind, w_key, L) 정렬)."""

    lut_fp: str
    rows: tuple
