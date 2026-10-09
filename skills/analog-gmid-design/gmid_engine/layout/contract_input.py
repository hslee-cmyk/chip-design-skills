"""MOD7 레이아웃 입력 계약 -- sizing(봉인 스냅샷) -> layout (계획 N3.17 '레이아웃 입력·출력 계약', design_mod7_layout.md 3절,
사용자 결정 2026-10-07 Q4·Q8).

데이터 선언 모듈(공개 정의 = frozen dataclass 뿐). 계산은 다른 파일이 한다. 엔진 안 숫자 0 -- 값은 전부 부르는 쪽이
근거 원천(sizing 결과·LUT·PDK 선언·MOD3 구조 유도)에서 채운다.

* `LayoutDevice`: 소자별 보존량 (ID, gm/ID, L)과 동작점(VDS, VSB) -- LY1 보존 대상(Q4 (i)). `W_m` 은 sizing 이 기준
  슬라이스에서 낸 **참고 W** 이고 보존 대상이 아니다: 실현 W 의 기준 = 그 finger_w 슬라이스에서 계산한
  `W_need(fw) = ID / J_slice(fw)`(`slice_density`). diode 여부(재평가 때 ID 재보정 불필요 표시, Q4 (iii)),
  MOD8 이 W 를 바꿀 수 있는지(`W_adjustable`).
* `MatchingGroup`: matching 그룹 레코드(MOD3 구조 유도 출력이 올 자리 -- 선언 태그를 읽지 않는다, L8). role 은 `ROLES` 중 하나:
  레이아웃 matching 대상 `LAYOUT_ROLES`(diff_pair·mirror·branch_symmetric)와, 레이아웃 matching 에서 빼고 근거를 기록하는
  `EXCLUDED_ROLES`(bias_distribution·feedback_shared, Q8 (iii)).
* `RowGroup`: 행 그룹 {kind, body 넷, 멤버}(LR8). 소자는 정확히 한 행 그룹에 속한다.
* `LayoutPdk`: 제조 격자(tlef MANUFACTURINGGRID), kind 별 finger_w 후보 = PDK 특성화 폭 키(LUT `widths`, LY2·E5),
  finger 당 L 밖 폭 여유·행 간격·행 끝 dummy 폭·tap 폭·well 간격(PDK 규칙 선언, 규칙 번호 `rule_ids` 필수, Q8 (vii)).
  `from_lut` 이 LUT 묶음에서 격자·폭 키를 읽는다.
* `LayoutPassive`: 판정 축 면적에 넣는 수동소자(MIM 커패시터·poly 저항) 하나의 배치 면적. 면적 식은 탐색 축과 같은 정본
  (`metrics.PassiveArea.area_m2` = 값 x PDK 선언 단위 면적 + 머리 면적)이고 `passives.passives_from_decl` 이 그 식으로 채운다(U12).
* `LayoutInput`: 위 묶음 + MOD8 이 거부한 W_request 소자 이름(LY5) + 수동소자 면적. box 행 폭 비 허용치는 없다(Q8 (vi) --
  하드 box 게이트 없음, 판정 축 = floorplan 외곽 면적).
"""
import dataclasses
import math

from gmid_engine.lut import widths

KINDS = ("nmos", "pmos")
ROLE_DIFF_PAIR = "diff_pair"
ROLE_MIRROR = "mirror"
ROLE_BRANCH_SYMMETRIC = "branch_symmetric"
ROLE_BIAS_DISTRIBUTION = "bias_distribution"
ROLE_FEEDBACK_SHARED = "feedback_shared"
LAYOUT_ROLES = (ROLE_DIFF_PAIR, ROLE_MIRROR, ROLE_BRANCH_SYMMETRIC)
EXCLUDED_ROLES = (ROLE_BIAS_DISTRIBUTION, ROLE_FEEDBACK_SHARED)
ROLES = LAYOUT_ROLES + EXCLUDED_ROLES
# common-centroid 를 반드시 허용해야 하는 role(LY5 차동쌍, Q8 (ii) branch_symmetric = 행 swap common-centroid 만).
CC_REQUIRED_ROLES = (ROLE_DIFF_PAIR, ROLE_BRANCH_SYMMETRIC)
PATTERN_COMMON_CENTROID = "common_centroid"
PATTERN_INTERDIGITATION = "interdigitation"
PATTERNS = (PATTERN_COMMON_CENTROID, PATTERN_INTERDIGITATION)
# PDK 규칙 선언 길이(m) -- `LayoutPdk.rule_ids` 가 모두 덮어야 한다.
PDK_RULE_QUANTITIES = ("finger_pitch_overhead_m", "row_gap_m", "dummy_w_m", "tap_w_m", "well_spacing_m")
# PDK 선언(core `read_pdk_decl`)의 제조 격자 이름 -- LUT 격자와 같아야 한다(core CONTRACT 9.5).
GRID_QUANTITY = "manufacturing_grid_m"


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _names(values, what):
    _require(isinstance(values, tuple), what + " 은 tuple 이어야 한다")
    _require(len(set(values)) == len(values), what + " 에 중복: " + repr(values))
    return values


@dataclasses.dataclass(frozen=True)
class LayoutDevice:
    """소자 하나. 길이·폭 m, 전류 A, 전압 V. 보존량 = (`ID_A`, `gm_id`, `L_m`), `W_m` = sizing 참고 W."""

    name: str
    kind: str
    drain: str
    gate: str
    source: str
    body: str
    W_m: float
    L_m: float
    ID_A: float
    gm_id: float
    vds_V: float
    vsb_V: float
    diode: bool
    W_adjustable: bool

    def __post_init__(self):
        _require(self.kind in KINDS, self.name + ": kind " + repr(self.kind) + " (허용 " + repr(KINDS) + ")")
        for what in ("W_m", "L_m", "ID_A", "gm_id"):
            value = getattr(self, what)
            _require(isinstance(value, float) and value > 0, self.name + ": " + what + " 는 양의 float 이어야 한다")


@dataclasses.dataclass(frozen=True)
class MatchingGroup:
    """matching 그룹. `hub_net`: 멤버가 공유하는 source/drain 넷(없으면 None -- branch_symmetric 은 hub 없는 쌍이라 읽지 않는다).
    `allowed_patterns`: `PATTERNS` 의 부분 tuple."""

    gid: str
    members: tuple
    role: str
    hub_net: object
    allowed_patterns: tuple

    def __post_init__(self):
        _names(self.members, self.gid + ".members")
        _require(len(self.members) > 1, self.gid + ": 멤버가 둘 이상이어야 한다")
        _require(self.role in ROLES, self.gid + ": role " + repr(self.role) + " (허용 " + repr(ROLES) + ")")
        _require(bool(self.allowed_patterns) and set(self.allowed_patterns) <= set(PATTERNS),
                 self.gid + ": allowed_patterns " + repr(self.allowed_patterns))
        if self.role in CC_REQUIRED_ROLES:
            _require(PATTERN_COMMON_CENTROID in self.allowed_patterns,
                     self.gid + ": " + self.role + " 은 common-centroid 를 허용해야 한다")


@dataclasses.dataclass(frozen=True)
class RowGroup:
    """행 그룹(같은 kind·body 넷의 diffusion 묶음)."""

    rid: str
    kind: str
    body_net: str
    members: tuple

    def __post_init__(self):
        _names(self.members, self.rid + ".members")
        _require(self.kind in KINDS, self.rid + ": kind " + repr(self.kind))


@dataclasses.dataclass(frozen=True)
class LayoutPdk:
    """`slice_width_keys` = ((kind, (폭 키 오름차순, ...)), ...), 폭 키 x `manufacturing_grid_m` = finger_w(m).
    `dummy_w_m` = 행 끝 dummy 하나의 폭(행마다 양끝 둘), `tap_w_m` = 행 그룹 경계 body tap 폭(LY10: 행마다가 아니라 그룹마다 하나), `well_spacing_m` = body 넷이 다른
    묶음 사이 간격. `rule_ids` = ((`PDK_RULE_QUANTITIES` 이름, PDK 규칙 번호 문자열), ...) -- 다섯 길이 모두."""

    manufacturing_grid_m: float
    slice_width_keys: tuple
    finger_pitch_overhead_m: float
    row_gap_m: float
    dummy_w_m: float
    tap_w_m: float
    well_spacing_m: float
    rule_ids: tuple
    source_fp: str

    def __post_init__(self):
        _require(self.manufacturing_grid_m > 0, "manufacturing_grid_m 는 양수")
        for what in PDK_RULE_QUANTITIES:
            _require(getattr(self, what) >= 0, "PDK " + what + " 는 0 이상")
        declared = dict(self.rule_ids)
        _require(len(declared) == len(self.rule_ids), "rule_ids 이름 중복")
        missing = [q for q in PDK_RULE_QUANTITIES if not declared.get(q)]
        _require(not missing, "PDK 규칙 번호 없음: " + repr(missing))

    @classmethod
    def from_lut(cls, lut, finger_pitch_overhead_m, row_gap_m, dummy_w_m, tap_w_m, well_spacing_m, rule_ids):
        """LUT 묶음(`gmid_engine.lut.LutSet`)에서 격자(`spec.manufacturing_grid_m`)와 kind 별 특성화 폭 키(`widths`)를 읽는다.
        길이 값은 float 로 바꾼다."""
        kinds = tuple(sorted({kind for kind, _ in lut.slice_map}))
        keys = tuple((kind, widths(lut, kind)) for kind in kinds)
        return cls(float(lut.spec.manufacturing_grid_m), keys, float(finger_pitch_overhead_m), float(row_gap_m),
                   float(dummy_w_m), float(tap_w_m), float(well_spacing_m), tuple(rule_ids), lut.fp)

    @classmethod
    def from_decl(cls, lut, decl):
        """정본 생성 경로: PDK 선언(`core.read_pdk_decl` 결과 `PdkDecl`)의 다섯 길이·규칙 식 + LUT 폭 키(core CONTRACT 9.5).
        LUT 격자(`lut.spec.manufacturing_grid_m`)가 선언 `manufacturing_grid_m` 과 1 ulp 넘게 다르면 `ValueError`
        (LUT 를 만드는 쪽이 `LutSpec(decl.value("manufacturing_grid_m"), ...)` 로 같은 선언값을 써야 한다)."""
        grid = float(decl.value(GRID_QUANTITY))
        _require(abs(float(lut.spec.manufacturing_grid_m) - grid) <= math.ulp(grid),
                 "LUT 격자 " + repr(lut.spec.manufacturing_grid_m) + " != PDK 선언 " + GRID_QUANTITY + " " + repr(grid))
        return cls.from_lut(lut, *decl.values(PDK_RULE_QUANTITIES), decl.rule_ids(PDK_RULE_QUANTITIES))


@dataclasses.dataclass(frozen=True)
class LayoutPassive:
    """판정 축 면적에 들어가는 수동소자 하나(MIM 커패시터·poly 저항): 이름, 배치 면적 `area_m2`(> 0, m^2).
    측정 부하(`measurement_load`)·단위 면적 미선언 소자는 만들지 않는다(탐색 축과 같은 제외, 결정 11)."""

    name: str
    area_m2: float

    def __post_init__(self):
        _require(isinstance(self.name, str) and self.name, "LayoutPassive.name 은 비지 않은 문자열")
        _require(not isinstance(self.area_m2, bool) and isinstance(self.area_m2, (int, float))
                 and math.isfinite(self.area_m2) and self.area_m2 > 0, self.name + ": area_m2 는 양의 유한 수")


@dataclasses.dataclass(frozen=True)
class LayoutInput:
    """레이아웃 입력 계약 전체. `rejected_requests` = MOD8 이 제약 위반으로 거부한 W_request 의 소자 이름(기록 -- LY5 는 거부를
    받아도 즉시 완화하지 않고 판정을 MOD8 에 맡긴다). `passives` = 판정 축 면적의 수동소자 블록(`LayoutPassive`, 이름 중복 없음).
    `EXCLUDED_ROLES` 그룹은 '한 행 그룹 안' 제약을 받지 않는다(블록을 넘는 바이어스 분배·루프 gate 공유가 정상이다)."""

    devices: tuple
    matching_groups: tuple
    row_groups: tuple
    pdk: LayoutPdk
    rejected_requests: tuple = ()
    passives: tuple = ()

    def __post_init__(self):
        by_name = {d.name: d for d in self.devices}
        _require(len(by_name) == len(self.devices), "소자 이름 중복")
        _names(tuple(g.gid for g in self.matching_groups), "matching_groups gid")
        _names(tuple(r.rid for r in self.row_groups), "row_groups rid")
        pdk_kinds = {kind for kind, _ in self.pdk.slice_width_keys}
        row_of = {}
        for rg in self.row_groups:
            for name in rg.members:
                _require(name in by_name, rg.rid + ": 없는 소자 " + name)
                _require(name not in row_of, name + ": 두 행 그룹에 속함")
                _require(by_name[name].kind == rg.kind and by_name[name].body == rg.body_net,
                         name + ": 행 그룹 " + rg.rid + " 의 (kind, body) 와 다름")
                row_of[name] = rg.rid
        _require(set(row_of) == set(by_name), "행 그룹에 없는 소자: " + repr(sorted(set(by_name) - set(row_of))))
        for d in self.devices:
            _require(d.kind in pdk_kinds, d.name + ": PDK 폭 키에 kind " + d.kind + " 없음")
        for g in self.matching_groups:
            for name in g.members:
                _require(name in by_name, g.gid + ": 없는 소자 " + name)
            if g.role in LAYOUT_ROLES:
                _require(len({row_of[name] for name in g.members}) == 1, g.gid + ": 멤버가 한 행 그룹에 있어야 한다")
        _names(self.rejected_requests, "rejected_requests")
        for p in self.passives:
            _require(isinstance(p, LayoutPassive), "passives 원소는 LayoutPassive: " + repr(p))
        _names(tuple(p.name for p in self.passives), "passives 이름")
