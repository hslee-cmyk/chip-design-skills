"""topology 로드 결과의 불변 데이터 형식 -- 데이터 선언 모듈 (설계 design_mod3_s1_graph 2.1 `topology_model.py`).

공개 정의는 frozen dataclass 뿐이다(규칙 A 데이터 선언 모듈):

* `SchemaHit` -- 로드 게이트 위반 하나. `load_topology` 가 전부 모아 `SchemaRejectedError` 한 번에 담는다.
* `DeviceDecl`·`PassiveDecl`·`SourceDecl`·`PortDecl`·`RailDeclaration` -- 검증을 통과한 선언의 투영.
* `DcEdge` -- 가지치기 전 DC 전도 엣지 하나(정의는 `dc_edges.py` 한 곳).
* `TopologyDoc` -- 검증을 통과한 topology 전체 투영. 태그 키(device_roles·symmetry·sizing_roles·compensation)는
  들어가지 않는다(IC4). `connectivity_fp` 는 정규화한 연결 투영의 내용 지문(core `fp_of`)이고, `_` 주석 키·태그
  키·원소 순서와 무관하다(NFR-2). 파일 sha256 은 출처 기록으로만 따로 든다.
  `bias_inputs` = 선언한 외부 바이어스 gate 전용 넷 이름의 정렬 tuple(Q6, `bias_inputs.py`). connectivity 가 아니라
  지문에 넣지 않는다(선언을 더해도 `connectivity_fp` 불변). 오라클 입력의 `bias_voltages` 넷 집합과 맞춘다.

2단자 원소(수동소자·이상원)의 단자 이름은 `TWO_TERMINAL_NAMES` 이다(S1 단자 표기 t0|t1, 설계 3절).
"""
import dataclasses

from gmid_engine.core import fp_of, require_immutable, sorted_items

TWO_TERMINAL_NAMES = ("t0", "t1")


@dataclasses.dataclass(frozen=True)
class SchemaHit:
    """로드 게이트 위반 하나. `rule` = 위반 종류 키(CONTRACT.md 표), `where` = 문서 안 위치(예: `netlist[3].gate`),
    `message` = 사람이 읽는 설명, `elements` = 관련 원소·넷 이름의 정렬 tuple."""

    rule: str
    where: str
    message: str
    elements: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, "elements", sorted_items(frozenset(self.elements)))


@dataclasses.dataclass(frozen=True)
class DeviceDecl:
    """netlist MOS 소자 하나. `bulk` 는 선언했을 때만 넷 이름, 아니면 None(기본 규칙은 graph 몫, DEC-61)."""

    name: str
    kind: str
    d: str
    g: str
    s: str
    bulk: object = None


@dataclasses.dataclass(frozen=True)
class PassiveDecl:
    """수동소자 하나. `terminals` = (t0 넷, t1 넷). `value_key` = 값 필드 이름(없으면 None), `value` = 수 또는 None(미선언)."""

    name: str
    kind: str
    terminals: tuple
    value_key: object = None
    value: object = None


@dataclasses.dataclass(frozen=True)
class SourceDecl:
    """이상원 하나. 필드 뜻은 `PassiveDecl` 과 같다. kind 판정은 graph 가 한다(기록만)."""

    name: str
    kind: str
    terminals: tuple
    value_key: object = None
    value: object = None


@dataclasses.dataclass(frozen=True)
class PortDecl:
    """포트 하나: 넷, 방향(input|output), 역할 문자열."""

    net: str
    direction: str
    role: str


@dataclasses.dataclass(frozen=True)
class RailDeclaration:
    """`supply_nets` 가 선언한 레일 넷 집합(B26-1). 레일 여부는 이 집합의 원소인가로만 정한다(DEC-60)."""

    nets: frozenset


@dataclasses.dataclass(frozen=True)
class DcEdge:
    """가지치기 전 DC 전도 엣지 하나: 원소 이름, 원소 kind, 양 끝 넷(정렬 tuple)."""

    element: str
    element_kind: str
    nets: tuple


@dataclasses.dataclass(frozen=True)
class TopologyDoc:
    """검증을 통과한 topology 투영. 원소 tuple 은 이름순(포트는 넷순), `rails` 는 frozenset.
    직접 만들지 말고 `TopologyDoc.from_declarations` 로 만든다(`connectivity_fp` 를 계산한다)."""

    name: str
    devices: tuple
    passives: tuple
    sources: tuple
    rails: frozenset
    ports: tuple
    connectivity_fp: str
    file_sha256: str
    bias_inputs: tuple = ()

    def __post_init__(self):
        require_immutable(self)

    @classmethod
    def from_declarations(cls, name, devices, passives, sources, rails, ports, file_sha256, bias_inputs=()):
        devices = sorted_items(devices, key=lambda x: x.name)
        passives = sorted_items(passives, key=lambda x: x.name)
        sources = sorted_items(sources, key=lambda x: x.name)
        ports = sorted_items(ports, key=lambda x: x.net)
        rails = frozenset(rails)
        return cls(name, devices, passives, sources, rails, ports,
                   _connectivity_fp(devices, passives, sources, rails, ports), file_sha256,
                   sorted_items(bias_inputs))


def _connectivity_fp(devices, passives, sources, rails, ports):
    # 연결 투영만 plain tuple 로 지문한다(모듈·클래스 이름이 지문에 들어가지 않게).
    projection = (
        ("devices", tuple((x.name, x.kind, x.d, x.g, x.s, x.bulk) for x in devices)),
        ("passives", tuple((x.name, x.kind, x.terminals, x.value_key, x.value) for x in passives)),
        ("sources", tuple((x.name, x.kind, x.terminals, x.value_key, x.value) for x in sources)),
        ("rails", sorted_items(rails)),
        ("ports", tuple((x.net, x.direction, x.role) for x in ports)),
    )
    return fp_of(projection)
