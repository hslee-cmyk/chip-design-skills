"""MOD5 수치 핵심의 입력 레코드 -- 데이터 선언 모듈 (설계 design_mod1_lut_mod5_mna 3.2·3.3·3.4).

graph·S2 를 모르는 불변 레코드다. 노드는 **정수 인덱스**(넷 이름이 아니다 -- 이름 리터럴·topology 종속 금지)이고,
교류접지·레일은 이름이 아니라 선언된 인덱스 집합으로 받는다. 값 검사(유한·부호)는 생성 때 한 번 한다.

* 소신호: `MosSmallSignal`(gm·gmb·gds·cgs·cgd·cgb·cdb·csb), `Resistor`, `Capacitor`, `Excitation`(여기 열 하나 --
  전압 구동·전류 주입·전하 주입), `Sense`(관측 하나), `SmallSignalCircuit`(소자 묶음 + 교류접지 노드), `StampSet`(스탬프 결과),
  `LoopCut`(루프 절단 하나: 수동소자 단자 하나를 새 노드로 옮긴다 -- 7a design 2.2).
* DC: `RailBias`, `ChannelCurrent`, `CurrentSource`, `DcOperatingPoint`.
* 면적: `GateArea`, `PassiveArea`.
"""
import dataclasses
import math


def _node(value, what):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s 는 정수 노드 인덱스여야 한다(넷 이름이 아니다): %r" % (what, value))
    return value


def _finite(value, what, *, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("%s 는 실수여야 한다: %r" % (what, value))
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("%s 는 유한해야 한다: %r" % (what, value))
    if positive and not value > 0:
        raise ValueError("%s 는 양수여야 한다: %r" % (what, value))
    if nonnegative and value < 0:
        raise ValueError("%s 는 음수가 아니어야 한다: %r" % (what, value))
    return value


def _tuple_of(value, kind, what):
    if not isinstance(value, tuple):
        raise TypeError("%s 는 tuple 이어야 한다" % what)
    for item in value:
        if not isinstance(item, kind):
            raise TypeError("%s 원소는 %s 여야 한다: %r" % (what, kind.__name__, item))
    return value


def _node_amp_pairs(value, what):
    if not isinstance(value, tuple):
        raise TypeError("%s 는 (노드, 값) tuple 의 tuple 이어야 한다" % what)
    seen = set()
    for pair in value:
        if not isinstance(pair, tuple):
            raise TypeError("%s 원소는 (노드, 값) 쌍이어야 한다: %r" % (what, pair))
        try:
            node, amount = pair
        except ValueError as exc:
            raise TypeError("%s 원소는 (노드, 값) 쌍이어야 한다: %r" % (what, pair)) from exc
        _node(node, what)
        if node in seen:
            raise ValueError("%s 에 노드 %r 가 두 번 나온다" % (what, node))
        seen.add(node)
        _finite(amount, what)
    return value


@dataclasses.dataclass(frozen=True)
class MosSmallSignal:
    """MOS 소신호 모델 하나(NMOS·PMOS 공통 -- 소신호 식은 극성과 무관하다).

    채널 전류 `I(d→s) = gm·(vg − vs) + gmb·(vb − vs) + gds·(vd − vs)`. 용량은 단자 쌍마다 하나:
    cgs(g–s), cgd(g–d), cgb(g–b), cdb(d–b), csb(s–b). 값은 소자 전체(W 반영). gm·gmb·gds 는 크기(0 이상 -- LUT 는 BSIM op 값의
    크기를 저장한다). 용량 5개는 **부호 있는 유한 실수**(오케스트레이터 결정 2026-10-08 Q7): BSIM4 단자 용량(예 cgb = −∂Qg/∂Vb)은
    부호가 있고 SPICE 오라클도 부호 그대로 스탬프한다 -- 같은 정의(U-48·DEC-90). 부호 규약의 원천 = LUT v2 생성기 meta
    `sign_convention`(lut CONTRACT r6 1.2, `CapTable.sign_convention`). NaN·inf 만 거부한다.
    `label` 은 진단용 불투명 문자열(코드가 읽지 않는다)."""

    d: int
    g: int
    s: int
    b: int
    gm: float
    gmb: float
    gds: float
    cgs: float = 0.0
    cgd: float = 0.0
    cgb: float = 0.0
    cdb: float = 0.0
    csb: float = 0.0
    label: str = ""

    def __post_init__(self):
        for name in ("d", "g", "s", "b"):
            _node(getattr(self, name), "MosSmallSignal." + name)
        for name in ("gm", "gmb", "gds"):
            object.__setattr__(self, name, _finite(getattr(self, name), "MosSmallSignal." + name, nonnegative=True))
        for name in ("cgs", "cgd", "cgb", "cdb", "csb"):
            object.__setattr__(self, name, _finite(getattr(self, name), "MosSmallSignal." + name))


@dataclasses.dataclass(frozen=True)
class Resistor:
    """저항 하나. 값은 반드시 선언된 양수(기본값 없음 -- 옛 1e9 기본값 폐기)."""

    a: int
    b: int
    ohm: float
    label: str = ""

    def __post_init__(self):
        _node(self.a, "Resistor.a")
        _node(self.b, "Resistor.b")
        object.__setattr__(self, "ohm", _finite(self.ohm, "Resistor.ohm", positive=True))


@dataclasses.dataclass(frozen=True)
class Capacitor:
    """커패시터 하나. 값은 반드시 선언된 양수."""

    a: int
    b: int
    farad: float
    label: str = ""

    def __post_init__(self):
        _node(self.a, "Capacitor.a")
        _node(self.b, "Capacitor.b")
        object.__setattr__(self, "farad", _finite(self.farad, "Capacitor.farad", positive=True))


@dataclasses.dataclass(frozen=True)
class Excitation:
    """여기 열 하나. `voltages`: 전압 구동 노드와 진폭((노드, V) 쌍), `currents`: 전류 주입 노드와 진폭((노드, A) 쌍,
    노드로 들어가는 방향), `charges`: 전하 주입 노드와 크기((노드, C) 쌍, 노드로 들어가는 전하 = 전류 s·q -- 열의 `BC` 에만
    들어가고 `BG` 에는 0 이라 용량 전용 노드의 ω → 0 극한이 전하 보존 식으로 정의된다, 7a design 2.4).
    한 MnaSystem 의 모든 열에서 전압 구동 노드는 고정 노드가 되고, 그 열에 없는 구동 노드는 0 V 다."""

    name: str
    voltages: tuple = ()
    currents: tuple = ()
    charges: tuple = ()

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("Excitation.name 은 비어 있지 않은 문자열이어야 한다")
        _node_amp_pairs(self.voltages, "Excitation.voltages")
        _node_amp_pairs(self.currents, "Excitation.currents")
        _node_amp_pairs(self.charges, "Excitation.charges")
        if not self.voltages and not self.currents and not self.charges:
            raise ValueError("Excitation %r 에 여기원이 없다" % self.name)


@dataclasses.dataclass(frozen=True)
class Sense:
    """관측 = v(pos) − v(neg). `neg` 가 None 이면 단일 관측."""

    pos: int
    neg: object = None

    def __post_init__(self):
        _node(self.pos, "Sense.pos")
        if self.neg is not None:
            _node(self.neg, "Sense.neg")
            if self.neg == self.pos:
                raise ValueError("Sense.pos 와 Sense.neg 가 같다")


@dataclasses.dataclass(frozen=True)
class SmallSignalCircuit:
    """소신호 회로 하나. `ac_ground`: 교류접지 노드 인덱스(레일·바이어스 종속 넷 -- 뷰가 정한다)."""

    mos: tuple = ()
    resistors: tuple = ()
    capacitors: tuple = ()
    ac_ground: tuple = ()

    def __post_init__(self):
        _tuple_of(self.mos, MosSmallSignal, "SmallSignalCircuit.mos")
        _tuple_of(self.resistors, Resistor, "SmallSignalCircuit.resistors")
        _tuple_of(self.capacitors, Capacitor, "SmallSignalCircuit.capacitors")
        if not isinstance(self.ac_ground, tuple):
            raise TypeError("SmallSignalCircuit.ac_ground 는 tuple 이어야 한다")
        for node in self.ac_ground:
            _node(node, "SmallSignalCircuit.ac_ground")
        if len(set(self.ac_ground)) != len(self.ac_ground):
            raise ValueError("SmallSignalCircuit.ac_ground 에 중복 노드가 있다")


LOOP_CUT_KINDS = ("resistor", "capacitor")
LOOP_CUT_TERMINALS = ("a", "b")
LOOP_CUT_MOS = "mos"            # [CM] 출력 포트 절단: MOS 의 gate 단자(소비자 쪽)도 새 노드로 옮길 수 있다
LOOP_CUT_MOS_TERMINALS = ("d", "s", "g")


@dataclasses.dataclass(frozen=True)
class LoopCut:
    """루프 절단 하나: `SmallSignalCircuit` 의 `kind`(resistor | capacitor) 원소 `index` 번째의 단자 `terminal`(a | b)을
    새 노드로 옮긴다(`cut_circuit`). 어느 단자를 끊을지는 선언(spec `feedback` 소자의 입력 포트 넷 쪽 단자)이 정한다.
    [CM] kind `mos`(`LOOP_CUT_MOS`) 는 `mos` 튜플의 `index` 번째 MOS 의 단자(`terminal` ∈ `LOOP_CUT_MOS_TERMINALS` = d | s | g)를 옮긴다."""

    kind: str
    index: int
    terminal: str

    def __post_init__(self):
        if self.kind not in LOOP_CUT_KINDS + (LOOP_CUT_MOS,):
            raise ValueError("LoopCut.kind 는 %r 중 하나여야 한다: %r" % (LOOP_CUT_KINDS + (LOOP_CUT_MOS,), self.kind))
        if isinstance(self.index, bool) or not isinstance(self.index, int):
            raise TypeError("LoopCut.index 는 정수여야 한다: %r" % (self.index,))
        if self.index < 0:
            raise ValueError("LoopCut.index 는 0 이상이어야 한다: %r" % (self.index,))
        allowed = LOOP_CUT_MOS_TERMINALS if self.kind == LOOP_CUT_MOS else LOOP_CUT_TERMINALS
        if self.terminal not in allowed:
            raise ValueError("LoopCut.terminal 은 %r 중 하나여야 한다: %r" % (allowed, self.terminal))


@dataclasses.dataclass(frozen=True)
class StampSet:
    """스탬프 결과. `g`·`c`: (행 노드, 열 노드, 값) 의 tuple -- 노드 인덱스 공간(아직 미지수/고정 분할 전)."""

    g: tuple = ()
    c: tuple = ()


@dataclasses.dataclass(frozen=True)
class RailBias:
    """레일 하나: 노드 인덱스와 DC 전압(V)."""

    node: int
    volt: float

    def __post_init__(self):
        _node(self.node, "RailBias.node")
        object.__setattr__(self, "volt", _finite(self.volt, "RailBias.volt"))


@dataclasses.dataclass(frozen=True)
class ChannelCurrent:
    """MOS 채널 가지 전류: drain 단자에서 source 단자로 소자 안을 흐르는 DC 전류(A, 부호 있음)."""

    drain: int
    source: int
    amp: float

    def __post_init__(self):
        _node(self.drain, "ChannelCurrent.drain")
        _node(self.source, "ChannelCurrent.source")
        object.__setattr__(self, "amp", _finite(self.amp, "ChannelCurrent.amp"))


@dataclasses.dataclass(frozen=True)
class CurrentSource:
    """이상 전류원: `amp` 가 노드 `from_node` 에서 나와 소자를 지나 노드 `to_node` 로 들어간다(선언값 또는 θ 전류)."""

    from_node: int
    to_node: int
    amp: float

    def __post_init__(self):
        _node(self.from_node, "CurrentSource.from_node")
        _node(self.to_node, "CurrentSource.to_node")
        object.__setattr__(self, "amp", _finite(self.amp, "CurrentSource.amp"))


@dataclasses.dataclass(frozen=True)
class DcOperatingPoint:
    """레일 전류 계산 입력(봉인된 DC 점의 투영). `node_v`: (노드, V) 쌍 -- 저항 양끝 중 레일이 아닌 노드 전압."""

    rails: tuple
    node_v: tuple = ()
    channels: tuple = ()
    resistors: tuple = ()
    sources: tuple = ()

    def __post_init__(self):
        _tuple_of(self.rails, RailBias, "DcOperatingPoint.rails")
        if not self.rails:
            raise ValueError("DcOperatingPoint.rails 가 비었다")
        if len({r.node for r in self.rails}) != len(self.rails):
            raise ValueError("DcOperatingPoint.rails 에 같은 노드가 두 번 나온다")
        _node_amp_pairs(self.node_v, "DcOperatingPoint.node_v")
        _tuple_of(self.channels, ChannelCurrent, "DcOperatingPoint.channels")
        _tuple_of(self.resistors, Resistor, "DcOperatingPoint.resistors")
        _tuple_of(self.sources, CurrentSource, "DcOperatingPoint.sources")


@dataclasses.dataclass(frozen=True)
class GateArea:
    """소자 하나의 게이트 면적 항: 총 W(m, finger·병렬 포함)와 L(m)."""

    w_m: float
    l_m: float
    label: str = ""

    def __post_init__(self):
        object.__setattr__(self, "w_m", _finite(self.w_m, "GateArea.w_m", positive=True))
        object.__setattr__(self, "l_m", _finite(self.l_m, "GateArea.l_m", positive=True))


@dataclasses.dataclass(frozen=True)
class PassiveAreaDecl:
    """수동소자 면적 선언(사용자 결정 11): `unit_area` = ((수동소자 이름, m²/값 단위), ...) -- PDK 단위 면적이 선언된 소자만,
    `excluded` = 면적에서 빼는 소자 이름(측정 부하 -- spec `measurement_load`). 둘 다 이름순 tuple, 겹치지 않는다."""

    unit_area: tuple = ()
    excluded: tuple = ()

    def __post_init__(self):
        names = [n for n, _a in self.unit_area]
        if len(set(names)) != len(names) or set(names) & set(self.excluded):
            raise ValueError("PassiveAreaDecl: 이름이 겹친다")
        for _n, a in self.unit_area:
            _finite(a, "PassiveAreaDecl.unit_area", positive=True)


@dataclasses.dataclass(frozen=True)
class PassiveArea:
    """수동소자 하나의 면적 항: 값(F 또는 Ω)과 PDK 선언 단위 면적(m²/값 단위, U-36). 선언이 없으면 None."""

    label: str
    value: float
    area_per_unit_m2: object = None

    def __post_init__(self):
        object.__setattr__(self, "value", _finite(self.value, "PassiveArea.value", positive=True))
        if self.area_per_unit_m2 is not None:
            object.__setattr__(
                self, "area_per_unit_m2",
                _finite(self.area_per_unit_m2, "PassiveArea.area_per_unit_m2", positive=True),
            )
