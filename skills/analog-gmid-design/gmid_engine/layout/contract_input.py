"""MOD7 레이아웃 입력 계약 -- sizing(봉인 스냅샷) -> layout (계획 N3.17 '레이아웃 입력·출력 계약', design_mod7_layout.md 3절).

데이터 선언 모듈(공개 정의 = frozen dataclass 뿐). 계산은 다른 파일이 한다. 엔진 안 숫자 0 -- 값은 전부 부르는 쪽이
근거 원천(sizing 결과·LUT·PDK 선언·사람 선언)에서 채운다.

* `LayoutDevice`: 소자별 총 W(계약값 -- 레이아웃은 바꾸지 않는다, LY1·LY3), L, ID, gm/ID, 동작점, W 허용오차 원천 tol_V
  (LUT `tol_v_table` 의 `id_equivalent` 셀 값, N3.6), diode 여부, MOD8 이 W 를 바꿀 수 있는지(`W_adjustable`).
* `MatchingGroup`: matching 그룹 레코드(MOD3 구조 유도 출력이 올 자리 -- 선언 태그를 읽지 않는다, L8).
  `role == ROLE_DIFF_PAIR` 이면 LY5 순서(common-centroid 우선 -> 같은 총 W 에서 nf 조정 -> W_request -> 완화).
* `RowGroup`: 행 그룹 {kind, body 넷, 멤버}(LR8). 소자는 정확히 한 행 그룹에 속한다.
* `LayoutPdk`: 제조 격자(tlef MANUFACTURINGGRID), kind 별 finger_w 후보 = PDK 특성화 폭 키(LUT `widths`, LY2·E5),
  finger 당 L 밖 폭 여유와 행 간격(PDK 규칙 선언). `from_lut` 이 LUT 묶음에서 격자·폭 키를 읽는다.
* `LayoutInput`: 위 묶음 + box 행 폭 비 허용치(사람 선언) + MOD8 이 거부한 W_request 소자 이름(LY5 (iii)).
"""
import dataclasses

from gmid_engine.lut import widths

KINDS = ("nmos", "pmos")
ROLE_DIFF_PAIR = "diff_pair"
PATTERN_COMMON_CENTROID = "common_centroid"
PATTERN_INTERDIGITATION = "interdigitation"
PATTERNS = (PATTERN_COMMON_CENTROID, PATTERN_INTERDIGITATION)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _names(values, what):
    _require(isinstance(values, tuple), what + " 은 tuple 이어야 한다")
    _require(len(set(values)) == len(values), what + " 에 중복: " + repr(values))
    return values


@dataclasses.dataclass(frozen=True)
class LayoutDevice:
    """소자 하나. 길이·폭 m, 전류 A, 전압 V. `tol_v_V` = 이 소자 동작점(L 앵커·VDS)의 LUT tol_V(ID 환산 지표) 셀 값."""

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
    tol_v_V: float
    diode: bool
    W_adjustable: bool

    def __post_init__(self):
        _require(self.kind in KINDS, self.name + ": kind " + repr(self.kind) + " (허용 " + repr(KINDS) + ")")
        for what in ("W_m", "L_m", "gm_id", "tol_v_V"):
            value = getattr(self, what)
            _require(isinstance(value, float) and value > 0, self.name + ": " + what + " 는 양의 float 이어야 한다")


@dataclasses.dataclass(frozen=True)
class MatchingGroup:
    """matching 그룹. `hub_net`: 멤버가 공유하는 source/drain 넷(없으면 None -- 패턴 함수 적용 불가로 기록).
    `allowed_patterns`: `PATTERNS` 의 부분 tuple."""

    gid: str
    members: tuple
    role: str
    hub_net: object
    allowed_patterns: tuple

    def __post_init__(self):
        _names(self.members, self.gid + ".members")
        _require(len(self.members) > 1, self.gid + ": 멤버가 둘 이상이어야 한다")
        _require(bool(self.allowed_patterns) and set(self.allowed_patterns) <= set(PATTERNS),
                 self.gid + ": allowed_patterns " + repr(self.allowed_patterns))
        if self.role == ROLE_DIFF_PAIR:
            _require(PATTERN_COMMON_CENTROID in self.allowed_patterns, self.gid + ": 차동쌍은 common-centroid 를 허용해야 한다")


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
    """`slice_width_keys` = ((kind, (폭 키 오름차순, ...)), ...), 폭 키 x `manufacturing_grid_m` = finger_w(m)."""

    manufacturing_grid_m: float
    slice_width_keys: tuple
    finger_pitch_overhead_m: float
    row_gap_m: float
    source_fp: str

    def __post_init__(self):
        _require(self.manufacturing_grid_m > 0, "manufacturing_grid_m 는 양수")
        _require(self.finger_pitch_overhead_m >= 0 and self.row_gap_m >= 0, "PDK 여유·간격은 0 이상")

    @classmethod
    def from_lut(cls, lut, finger_pitch_overhead_m, row_gap_m):
        """LUT 묶음(`gmid_engine.lut.LutSet`)에서 격자(`spec.manufacturing_grid_m`)와 kind 별 특성화 폭 키(`widths`)를 읽는다."""
        kinds = tuple(sorted({kind for kind, _ in lut.slice_map}))
        keys = tuple((kind, widths(lut, kind)) for kind in kinds)
        return cls(float(lut.spec.manufacturing_grid_m), keys, float(finger_pitch_overhead_m), float(row_gap_m), lut.fp)


@dataclasses.dataclass(frozen=True)
class LayoutInput:
    """레이아웃 입력 계약 전체. `box_max_row_ratio` = 행 폭 비(max/min) 허용치(사람 선언, 기본값 없음).
    `rejected_requests` = MOD8 이 제약 위반으로 거부한 W_request 의 소자 이름(LY5 (iii) 완화 조건)."""

    devices: tuple
    matching_groups: tuple
    row_groups: tuple
    pdk: LayoutPdk
    box_max_row_ratio: float
    rejected_requests: tuple = ()

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
            _require(len({row_of[name] for name in g.members}) == 1, g.gid + ": 멤버가 한 행 그룹에 있어야 한다")
        _names(self.rejected_requests, "rejected_requests")
        _require(self.box_max_row_ratio >= 1, "box_max_row_ratio 는 1 이상")
