"""MOD1 LUT 데이터 선언 모듈 -- 로드 입력 선언·불변 LUT 묶음·조회 결과 레코드 (설계 MOD1 2.2·2.3·2.5).

공개 정의는 frozen dataclass 뿐이다(데이터 선언 모듈, 구조 규칙 A 보충 (1)). 계산은 다른 파일이 한다.

* L 은 LUT 앵커이거나, 같은 PDK 모델 bin 안의 두 이웃 앵커 사이일 때만 그 둘로 선형 보간한다(사용자 결정 2026-10-07,
  bin 경계를 건너는 보간 금지). bin 지도(`LBinMap`)는 로드 때 슬라이스가 기록한 모델 파일에서 한 번 만든다.
* 축 순서는 `AXES` = (L, VGS, VDS, VS) 이고 슬라이스 배열 배치 `[L, VGS, VDS, VS]` 와 같다. VS 축은 source 기준
  body 전위 크기(vsb)다(슬라이스 생성기 sign_convention: source 접지, body = -VS(nfet) / +VS(pfet)).
* 슬라이스 배열 값은 그 폭 `w_m` 에서의 절댓값(정규화 안 함). 정규화(`ID·L/w_m`)는 조회 함수가 한다.
* 보간 방법은 축별이다(DEC-87, lut/CONTRACT.md 4.2): ln ID 는 VGS·VDS 축 2점 cubic-Hermite(기울기 = 저장 GM/ID·GDS/ID),
  [r7] VS 축도 GMBS 열이 있는 슬라이스에서 Hermite(기울기 = −GMBS/ID), L 축 선형. gm/ID 는 그 다항식의 VGS 미분으로 정의한다.
  로드 때 Hermite 칸마다 Fritsch–Carlson 단조 조건을 검사해 둔다.
* numpy 배열 필드는 읽기 전용(`writeable=False`)으로 만든다. 그래서 내용 지문은 `__canonical__` 이 파일 sha256
  등 출처 값으로 대신 말한다(배열 바이트를 매번 해시하지 않는다 -- DF-13 의 '내용 해시는 비싸다'를 로드 1회로 해소).
* [r6] 열은 그 열을 **저장한 표**에서만 읽는다(폭을 건너 옮기지 않는다): 슬라이스 선택 열(`DcSlice.columns`) 또는 그 폭이
  기준 LUT 폭(`CapTable.w_key`)과 같을 때의 기준 LUT 선택 열(`CapTable.columns`). 용량 열은 생성기 규약대로 부호를 보존한다.
"""
import dataclasses
import types

AXES = ("L", "VGS", "VDS", "VS")
TOL_V_METRICS = ("id_equivalent",)
TOL_VDSAT_METRICS = ("vdsat",)
# 기준 LUT 선택 열(LUT v2 생성기 meta `units` 의 키) -- 있으면 읽고, 없으면 그 열을 쓰는 조회가 `lut_column_unavailable`.
CAP_TABLE_COLUMNS = ("CDD", "CSS", "GDS", "GM", "GMBS", "ID", "SVG2_1HZ", "SVG2_HF", "VDSAT", "VTH")
# 폭 슬라이스 선택 열 -- 지금 슬라이스 생성기는 쓰지 않는다(쓰게 되면 그 폭에서 바로 쓰인다, lut/CONTRACT.md 1.2).
SLICE_OPTIONAL_COLUMNS = ("GMBS", "VDSAT")
# 로드 때 한 번 만드는 파생 열: GMBS_PER_ID = GMBS/ID(ID > 0 인 점, 아니면 NaN) -- GMBS·ID 가 같은 표에 있을 때만.
DERIVED_COLUMNS = ("GMBS_PER_ID",)
# 열 출처 이름(`ColumnSource.origin`)
COLUMN_ORIGINS = ("cap_table", "slice")
# [r7] gm/ID 축 곡선 양(`GmIdAxisCurve.quantity`)
CURVE_QUANTITIES = ("ft_hz", "idu_a", "intrinsic_gain", "vdsat_v")      # 이름이 단위를 적는다(Hz·A·무차원·V)
# [r7] 잡음 B(열잡음 평탄값) 상태: 점의 판정 결과. "known" 이 아니면 B 는 미상(None)이고 A 는 S_vg(1 Hz) 그대로다.
CLASS_HERMITE = "hermite"                          # `Curve.cell_class` 값: Hermite 칸(역산 허용). 그 밖은 REASON_* 사유 글자
NOISE_B_STATUS = ("known", "no_feedthrough_free_point", "nonpositive")
TOL_NOISE_METRICS = ("flicker", "thermal")           # flicker: ln S_vg(f_lo) 면 LOO(상대), thermal: ln B 면 LOO(상대)


@dataclasses.dataclass(frozen=True)
class LutSpec:
    """로드에 필요한 PDK·파일 형식 선언(부르는 쪽이 PDK 선언에서 채운다 -- 엔진은 숫자를 박지 않는다).

    `manufacturing_grid_m`: PDK 제조 격자(m, tlef MANUFACTURINGGRID). 폭 키 = round(w_m / 이 값).
    `min_finger_w_m`: ((kind, 최소 finger 폭 m), ...) -- `widths()` 의 하한(PDK difftap 규칙).
    `device_kinds`: ((manifest device 이름, kind), ...) -- 슬라이스 소자 이름을 엔진 kind 로.
    `cap_column_suffix`: ((kind, 기준 LUT 열 접미사), ...) -- 기준 LUT npz 의 `CGG<접미사>` 등 열 이름.
    [r7] `noise_ef`: ((kind, 1/f 지수 EF), ...) -- 잡음 파일(`noise_npz`)을 읽을 때만 필요. PDK 선언 양 `noise_ef_<kind>`
    (core `read_pdk_decl`, 모델 카드 `ef` 키 원본)에서 부르는 쪽이 채운다.
    """

    manufacturing_grid_m: float
    min_finger_w_m: tuple
    device_kinds: tuple
    cap_column_suffix: tuple
    noise_ef: tuple = ()


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
    """LUT 묶음의 출처: manifest·슬라이스·기준 LUT 파일 sha256, 측정 조건(corner·temp_c·recorded).

    [LM-1e] `midpoint_sources`: bin 검증 중점 파일(선택, `load_lut_set(verify_midpoints=)`, 파일마다 짝 슬라이스 하나)의 출처 `SliceSource`
    tuple((kind, w_key) 오름차순; `sha256` = 파일 raw 바이트). 없으면 (). `midpoints_sha256` = 그 sha256 의 정렬 tuple(property -- 사본 칸 아님, 없으면 None).
    [r7] `noise_*`·`mismatch_*`: 잡음 r1 파일·mismatch 감도 r1 파일(선택)의 경로와 sha256(없으면 None).
    [WB-1 범위 0] `bin_rule`·`bin_rule_sha256`: 적용한 bin 규칙 선언의 `rule`("lower"·"upper")과 LF 환산 sha256(필수, 키워드 전용).
    `bin_rule_machine_dependent`: 줄바꿈 때문에 기록 sha256 이 raw 바이트 값인 ((세트, 모델 파일 상대 경로), ...) 정렬 tuple(지문에 넣지 않는다).
    """

    manifest_path: str
    manifest_sha256: str
    generator_sha256: str
    slices: tuple
    cap_path: str
    cap_sha256: str
    cap_conditions: tuple
    midpoint_sources: tuple = ()
    noise_path: object = None
    noise_sha256: object = None
    mismatch_path: object = None
    mismatch_sha256: object = None
    bin_rule: str = dataclasses.field(kw_only=True)
    bin_rule_sha256: str = dataclasses.field(kw_only=True)
    bin_rule_machine_dependent: tuple = dataclasses.field(kw_only=True)

    @property
    def midpoints_sha256(self):
        """중점 파일 raw sha256 의 정렬 tuple, 중점 파일이 없으면 None(지문·자료 id 가 읽는다)."""
        return tuple(sorted(s.sha256 for s in self.midpoint_sources)) if self.midpoint_sources else None


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

    [r6] `columns`: 슬라이스 npz 에 있는 선택 열(`SLICE_OPTIONAL_COLUMNS`) + 파생 열(`DERIVED_COLUMNS`) {이름: 읽기 전용 배열}
    (지금 슬라이스 생성기는 선택 열을 쓰지 않는다 -> 빈 매핑).

    [r7] VS 축 Hermite(DEC-87): `vs_slope_ok` = (ID > 0) & (GMBS > 0) 격자점(VS 기울기 d ln ID/d VS = −GMBS/ID 정의; GMBS 열이
    없으면 전부 거짓), `fc_ok_vs`[L, VGS, VDS, VS 칸] = 그 칸 단조 조건(Hermite 칸이 아니면 참), `hermite_fc` 에 ("VS", ...) 항.
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
    columns: object = types.MappingProxyType({})
    vs_slope_ok: object = None
    fc_ok_vs: object = None

    def __canonical__(self):
        return (self.kind, self.w_key, self.sha256)


@dataclasses.dataclass(frozen=True, eq=False)
class CapTable:
    """기준 LUT 의 용량 열(한 kind). `CGS`·`CGB` 는 열이 없으면 None. `w_ref_m` = 이 배열이 잰 폭.
    `l_bins` = 채택 폭과 같은 슬라이스의 L bin 지도(같은 슬라이스가 없으면 빈 지도).

    `basis`: w_ref_m 채택 근거 ((키, 값), ...) -- 메타 기록인지, 어느 슬라이스와 ID 가 맞았는지.

    [r6] `w_key`: w_ref_m 의 폭 키(슬라이스와 같은 2 ulp 규칙, 슬라이스 폭 키와 비교하는 값), `columns`: 기준 LUT 에 있는
    선택 열(`CAP_TABLE_COLUMNS`) {이름: 읽기 전용 배열} + 파생 열(`DERIVED_COLUMNS`), `on_mask`: (ID > 0) & (GM > 0)(두 열이
    있을 때, 아니면 None), `sign_convention`: 생성기 meta 의 부호 규약 문장(meta 없음 = None -- 옛 생성기는 용량 크기(mag)),
    `l_source`: meta `L_source`(키 정렬 쌍 tuple, 없으면 ()).
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
    w_key: object = None
    columns: object = types.MappingProxyType({})
    on_mask: object = None
    sign_convention: object = None
    l_source: tuple = ()

    def __canonical__(self):
        return (self.kind, self.sha256, self.w_ref_m, self.basis)


@dataclasses.dataclass(frozen=True, eq=False)
class MidpointTable:
    """[LM-1e] bin 검증 중점 파일 하나 = 짝 슬라이스 (kind, w_key) 하나의 중점 표(lut/CONTRACT.md 1.7). LUT 축이 아닌 L 점 `L_points`(m, 파일 `L`
    순서)에서 같은 (VGS, VDS, VS) 축(`grids` 세 개 -- 슬라이스 축과 float 단위로 같음)으로 잰 값. 폭 = `w_m`(파일 `W`), 폭 키 `w_key`.
    `sha256` = 그 파일 raw 바이트의 sha256.

    `log_ID` = ln ID(ID > 0 인 점, 아니면 NaN), `gm_id` = GM/ID(같은 점, 아니면 NaN), `on_mask` = (ID > 0) & (GM > 0),
    `VDSAT` = 열이 있으면 읽기 전용 배열(없으면 None). 배열 모양 [len(L_points), VGS, VDS, VS].
    """

    kind: str
    sha256: str
    w_m: float
    w_key: int
    L_points: tuple
    grids: tuple
    log_ID: object
    gm_id: object
    on_mask: object
    VDSAT: object

    def __canonical__(self):
        return (self.kind, self.sha256)


@dataclasses.dataclass(frozen=True, eq=False)
class LutSet:
    """불변 LUT 묶음. `slice_map`: {(kind, w_key): DcSlice}, `cap_map`: {kind: CapTable} (읽기 전용 매핑).

    `fp` = `lut_fingerprint(provenance, cap 채택 근거)` -- memo 키와 S0 입력에 쓴다.
    [LM-1e] `midpoints`: {(kind, w_key): MidpointTable}(검증 중점 파일을 주지 않았으면 빈 매핑).
    [r7] `noise`: {kind: NoiseTable}(잡음 r1 파일), `mismatch`: {kind: MismatchTable}(mismatch 감도 r1 파일) -- 파일을 주지 않았으면 빈 매핑.
    """

    spec: LutSpec
    provenance: LutProvenance
    slice_map: object
    cap_map: object
    fp: str
    midpoints: object = types.MappingProxyType({})
    noise: object = types.MappingProxyType({})
    mismatch: object = types.MappingProxyType({})

    def __canonical__(self):
        return self.fp

    @property
    def bin_rule(self):
        """적용한 bin 규칙("lower"·"upper") -- `provenance.bin_rule` 을 읽는다(사본 칸 아님)."""
        return self.provenance.bin_rule


@dataclasses.dataclass(frozen=True, eq=False)
class ColumnSource:
    """[r6] (kind, w_key) 에서 열 하나를 읽을 표(lut/CONTRACT.md 4.3). `origin` ∈ `COLUMN_ORIGINS`, `grids` = 그 표의 축 네 개,
    `array` = 그 열(읽기 전용), `l_bins` = 그 표의 L bin 지도, `on_mask` = 그 표의 (ID > 0) & (GM > 0)(없으면 None),
    `table_w_m` = 그 표가 잰 폭(m)."""

    origin: str
    column: str
    kind: str
    w_key: int
    table_w_m: float
    grids: tuple
    array: object
    l_bins: LBinMap
    on_mask: object


@dataclasses.dataclass(frozen=True)
class OpPoint:
    """한 동작점 조회 결과(슬라이스 폭 w_m 기준).

    `IDu` = ID·L/w_m(A, W/L=1 기준 전류), `gm_over_id`(1/V), `gm_gds`(무차원), `gds_per_w` = GDS/w_m(S/m), `vth`(V).
    [r7] `fallbacks` = Hermite 가 가능한 칸인데 선형으로 보간한 축의 ((축, 사유), ...) 정렬 tuple(없으면 ()) -- 사유
    "slope_undefined"·"fc_violation"(DEC-87 FC 정책: 선형 폴백을 허용하되 사유를 기록한다, 41 §4.1).
    """

    IDu: float
    gm_over_id: float
    gm_gds: float
    gds_per_w: float
    vth: float
    fallbacks: tuple = ()


@dataclasses.dataclass(frozen=True, eq=False)
class Curve:
    """고정 (L, VDS, VS) 에서 VGS 격자 마디의 곡선. `id_vals` = 슬라이스 폭에서의 ID(A), `log_id_vals` = ln ID,
    `gm_id_vals` = gm/ID(1/V, 마디의 VGS 기울기 -- 기울기 자료가 정의되지 않은 마디는 NaN). 마디 사이는 VGS 칸마다
    (ln ID, gm/ID) 를 값·기울기로 쓰는 cubic-Hermite 다(op_point 와 같은 곡면, lut/CONTRACT.md 4.2).
    `cell_ok`[j] = VGS 칸 [j, j+1] 의 모서리(가중치 0 이 아닌 L·VDS·VS 격자 칸)가 모두 Fritsch–Carlson 단조 조건을
    만족(거짓이면 그 칸은 선형 -- 역산 함수가 그 칸의 근을 내지 않는다).
    [r7] `cell_class`[j] = VGS 칸 j 의 분류(41 §4.1): "hermite"(단조 -- 역산 허용), "fc_violation"(Fritsch–Carlson 위반 -- 격자
    전수만), "slope_undefined"(끝 기울기 자료 없음 -- 선형 칸).

    배열은 읽기 전용 numpy 배열이다.
    """

    vgs_grid: object
    id_vals: object
    gm_id_vals: object
    log_id_vals: object
    cell_ok: object
    cell_class: tuple = ()


@dataclasses.dataclass(frozen=True)
class TargetSolution:
    """목표(gm 또는 ID)를 만드는 강반전 분지 위 동작점. `id_a`·`gm_s` 는 소자 총 폭 W 기준 값."""

    vgs: float
    gm_id: float
    id_a: float
    gm_s: float


@dataclasses.dataclass(frozen=True)
class Caps:
    """소자 총 폭 W 의 용량(F). `model`: "lut_cgs_cgb"(열 있음) 또는 "cgg_minus_cgd_at_gs"(cgs = cgg - cgd, cgb = 0).

    [r6] `cdd`·`css`: 드레인·소스 자기 용량(기준 LUT CDD·CSS 열, 접합 포함 -- 열이 없으면 None). 값은 기준 LUT 의 부호 그대로
    (LUT v2 는 부호 보존 -- CGB·CGS·CSS 등이 음수일 수 있다, `CapTable.sign_convention`).
    """

    cgg: float
    cgd: float
    cgs: float
    cgb: float
    model: str
    cdd: object = None
    css: object = None
    cgs_measured: object = None     # [JC-1, A-169] 기준 LUT CGS 열 값(CGB 열 유무와 무관, 열이 없으면 None). 소비자 = metrics `junction_at_vgs_min` 하나


@dataclasses.dataclass(frozen=True)
class TolVCell:
    """tol_V 표 한 칸((kind, w_key, L 앵커, VDS)). 값은 보간 축 leave-one-out(운영 보간과 같은 방법)의 오차를 축마다
    Richardson 환산(÷ 2^p, p = 그 축·지표의 보간 차수, lut/CONTRACT.md 5절)한 셀 안 최댓값(V), 정의 안 되면 None.

    `id_equivalent_v`: |ln ID_loo - ln ID| / (gm/ID) / 2^p. `id_equivalent_loo_v`: 환산 전 LOO 값(간격 2배 격자의 오차)의 셀 안 최댓값(진단·환산 검증용).
    """

    id_equivalent_v: object
    id_equivalent_loo_v: object = None


@dataclasses.dataclass(frozen=True)
class TolVdsatCell:
    """[r6] VDsat 허용오차 표 한 칸((kind, w_key, L 앵커, VDS)): `vdsat_v` = VDSAT 열 leave-one-out(운영 보간과 같은 방법 --
    모든 축 선형) 오차를 Richardson 환산(÷ 2^2)한 셀 안 최댓값(V)과 외부 bin 값의 최댓값, `vdsat_loo_v` = 환산 전 최댓값.
    정의 안 되면 None."""

    vdsat_v: object
    vdsat_loo_v: object


@dataclasses.dataclass(frozen=True)
class MidpointRow:
    """[r6] 검증 중점이 잰 앵커 2개 bin 하나의 L 보간 오차(V, lut/CONTRACT.md 5.1). `model` = 그 bin `.model` 이름,
    `L_points` = 그 bin 에 든 중점들(m, 오름차순), 세 값 = VDS 격자점마다의 tuple(길이 = VDS 격자 수) -- 그 VDS 의 점·목표와
    그 중점들 전체의 최댓값(정의된 점이 없으면 그 원소 None).
    """

    model: str
    L_points: tuple
    id_equivalent_v: object
    vdsat_v: object


@dataclasses.dataclass(frozen=True)
class MidpointChecks:
    """[r6] (kind, w_key) 의 중점 검증 결과: `rows` = MidpointRow tuple(model 정렬), `skipped` = ((L, 사유, model 또는 None), ...)
    -- 쓰지 않은 중점과 이유(lut/CONTRACT.md 5.1 표). `midpoints_sha256` = 중점 파일 sha256(없으면 None)."""

    kind: str
    w_key: int
    rows: tuple
    skipped: tuple
    midpoints_sha256: object


@dataclasses.dataclass(frozen=True)
class LutLocation:
    """[r6] 설정 파일로 정한 LUT 데이터 위치(lut/CONTRACT.md 1.8). 경로는 절대 경로, 파일 sha256 은 설정 기록과 대조됨.
    [LM-1e] `midpoints_paths`: 설정 `files.verify_midpoints`(`{path, sha256}` 배열)의 절대 경로 tuple(`path` 오름차순), 없으면 (). `pdk_root` 는 설정에 없으면 None. `sources` = ((항목, "env:<이름>" 또는 "config_default"), ...).
    [r7] `noise_path`·`mismatch_path`: 잡음 r1·mismatch 감도 r1 파일(설정 `files.noise`·`files.mismatch`, 없으면 None).
    [WB-1 범위 0] `bin_rule_path`: bin 규칙 선언 파일의 절대 경로(설정 최상위 `bin_rule`, LF 환산 sha256 대조 통과; 끝 칸 기본 None)."""

    config_path: str
    root: str
    manifest_path: str
    cap_npz_path: str
    midpoints_paths: tuple
    pdk_root: object
    sources: tuple
    noise_path: object = None
    mismatch_path: object = None
    bin_rule_path: object = None


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


@dataclasses.dataclass(frozen=True, eq=False)
class GmIdAxisCurve:
    """[r7] gm/ID 축 곡선 표(lut/CONTRACT.md 4.5): 고정 (L, VDS, VS) 의 강반전 분지(VGS ≥ 곡선 정점) VGS 격자 마디에서 `quantity`
    (`CURVE_QUANTITIES`) 의 값. 배열은 VGS 오름차순(gm/ID 는 분지에서 내려간다), 읽기 전용.

    `gm_id` = 마디 gm/ID(1/V), `values` = 마디 값, `vgs` = 마디 VGS, `cell_ok`[j] = 마디 j·j+1 사이 VGS 칸이 Hermite 칸(역산 허용),
    `monotone` = `gm_id` 가 분지에서 엄격히 감소(역산 가능 -- 아니면 소비자는 격자 전수로 쓴다, 41 §4.1). `L` = 조회 L(앵커 값 또는 보간 L).
    """

    quantity: str
    kind: str
    w_key: int
    L: float
    vds: float
    vsb: float
    gm_id: object
    values: object
    vgs: object
    cell_ok: object
    monotone: bool

    def __canonical__(self):
        return (self.quantity, self.kind, self.w_key, self.L, self.vds, self.vsb)


@dataclasses.dataclass(frozen=True, eq=False)
class NoiseTable:
    """[r7] 잡음 r1 파일의 한 kind(lut/CONTRACT.md 9.1). `freqs` = 주파수 점(Hz, 오름차순; 기준 LUT 의 `SVG2_1HZ`·`SVG2_HF` 두 점
    + r1 파일의 로그 이분 점), `S`[f, L, VGS, VDS, VS] = 게이트 환산 S_vg(f)(V²/Hz, 기준 폭 `w_ref_m`), `ef` = PDK 1/f 지수.
    축·`l_bins`·`w_key` 는 기준 LUT(`CapTable`)와 같다. `cap_sha256` = 이 파일이 묶인 기준 LUT sha256(로드 때 대조)."""

    kind: str
    sha256: str
    cap_sha256: str
    grids: tuple
    freqs: tuple
    S: object
    ef: float
    w_ref_m: float
    w_key: object
    l_bins: LBinMap

    def __canonical__(self):
        return (self.kind, self.sha256)


@dataclasses.dataclass(frozen=True, eq=False)
class NoisePlanes:
    """[r7] 잡음 분해 면(파생 표, lut/CONTRACT.md 9.2): S_vg(f) = A/f^EF + B. `ln_a`·`ln_b`[L, VGS, VDS, VS] = ln A, ln B(미상 NaN),
    `status`[...] = 점마다 `NOISE_B_STATUS` index, `tol_a`[L, VDS] = 피드스루 판정 허용오차(셀 값; ln S_vg(f_lo) 면 LOO 상대오차의
    Richardson 환산, 정의 안 되면 NaN). 조회용 보조 면(점마다 한 번 계산해 `linear_point` 가 모서리만 읽게 한다): `ln_b_filled` = ln B(미상 0),
    `flag_no_point`·`flag_nonpositive` = 상태가 그 값이면 1.0, 아니면 0.0. `tol_point`[L, VGS, VDS, VS] = B 를 고른 점의 실효 허용오차
    (= min(그 점의 LOO 오차, 그 셀의 `tol_a`), 점의 LOO 가 정의 안 되면 `tol_a`)."""

    kind: str
    ln_a: object
    ln_b: object
    status: object
    tol_a: object
    ln_b_filled: object
    flag_no_point: object
    flag_nonpositive: object
    tol_point: object

    def __canonical__(self):
        return (self.kind,)


@dataclasses.dataclass(frozen=True)
class NoiseParams:
    """[r7] 게이트 환산 잡음 계수(기준 폭 `w_m` 의 소자): S_vg(f) = `A`/f^`ef` + `B` (V²/Hz). `B` 가 미상(`b_status` != "known")이면
    None 이고 `A` 는 S_vg(1 Hz) 그대로. 폭 W 소자는 두 값 모두 `w_m`/W 배."""

    A: float
    B: object
    ef: float
    b_status: str
    w_m: float


@dataclasses.dataclass(frozen=True)
class TolNoiseCell:
    """[r7] 잡음 허용오차 표 한 칸((kind, L 앵커, VDS)): `flicker` = ln S_vg(f_lo) 면, `thermal` = ln B 면의 leave-one-out(선형) 상대오차를
    Richardson 환산(÷ 2^2)한 셀 안 최댓값, 정의 안 되면 None."""

    flicker: object
    thermal: object


@dataclasses.dataclass(frozen=True, eq=False)
class MismatchTable:
    """[r7] mismatch 감도 r1 파일의 한 kind(lut/CONTRACT.md 10.1). `dvgs`[param] = DVGS_param[L, VGS, VDS, VS](V; 변수 param 의 1σ 섭동에서
    기준 곡선 ID 의 |VGS| 차, 정의 안 되면 NaN), `slope_ref`[i] = L 앵커 i 의 ((param, slope 이름 또는 None, slope 값 또는 None), ...),
    `sigma_unit` = 섭동 1σ 의 `*_slope_spectre` 값(.option scale)."""

    kind: str
    sha256: str
    cap_sha256: str
    grids: tuple
    params: tuple
    dvgs: object
    slope_ref: tuple
    sigma_unit: float
    w_ref_m: float
    w_key: object
    l_bins: LBinMap

    def __canonical__(self):
        return (self.kind, self.sha256)


@dataclasses.dataclass(frozen=True)
class MismatchSens:
    """[r7] 기준 폭 `w_m`, 조회점의 mismatch 감도: `dvgs`{param: V}(1σ 섭동 DVGS_k), `slope_ref`{param: 기준 bin 의 slope 값}(그 bin 이
    변수를 안 쓰면 0.0). 소자 σ 합성은 `mismatch_sigma_vgs`."""

    dvgs: object
    slope_ref: object
    w_m: float


@dataclasses.dataclass(frozen=True)
class TolMismatchCell:
    """[r7] mismatch 허용오차 표 한 칸((kind, L 앵커, VDS)): `params` = ((변수, 값 V 또는 None), ...) -- DVGS_param 면 leave-one-out(선형)
    오차의 Richardson 환산(÷ 2^2) 셀 안 최댓값."""

    params: tuple


@dataclasses.dataclass(frozen=True)
class MismatchSigma:
    """[r7] 소자 하나의 게이트 환산 mismatch σ(`mismatch_sigma_vgs`): `sigma_v`(V) = √Σ 기여², `parts` = ((변수, 기여 V), ...) 변수 선언 순서,
    `model` = 소자 (W, L) 이 든 PDK `.model` 블록 이름."""

    sigma_v: float
    parts: tuple
    model: str


@dataclasses.dataclass(frozen=True)
class EdgeCost:
    """kind 하나의 헤드룸 경로 엣지 비용 최솟값(41 §4.6). `vgs_min_v` = 전도 봉인(9)을 지키는 격자 행의 |VGS| 최솟값, `vgs_min_by_bin` = ((L bin 번호, 그 bin 의 최솟값), ...),
    `vds_min_v` = 포화 가능 격자점(전도·분지 마디이고 VDS ≥ VDSAT)의 VDSAT 최솟값(tol 합 없음, 열 없음 = 0.0), `best_row` = ((키, 값), ...) VGS 최솟값을 낸 행(gm/ID·L·VSB)."""

    kind: str
    w_key: int
    vgs_min_v: float
    vgs_min_by_bin: tuple
    vds_min_v: float
    best_row: tuple
