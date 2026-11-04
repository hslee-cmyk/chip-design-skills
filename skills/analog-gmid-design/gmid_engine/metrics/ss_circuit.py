"""S2 열 -> 정수 인덱스 소신호 회로 (7a design 4.5 단계 5 '소자 이름 -> 원소 인덱스, 넷 -> 노드 인덱스', 설계 MOD5 3.3, 카드 IT-2c).

진입점: `ss_circuit_field`(`@compute_block`, writer `ss_circuit`) -- `ss_circuit_field(snapshot, donors=, counters=)`, 추가 인자 없음.
reads `device.{ss_dev, element_class, kind, pins, bulk, passive_value, dc_colour}`, `node.{ac_ground_class, dc_colour, port_direction}`; writes `graph.ss_circuit`(key
`METRICS_KEY`) = `SsCircuit`. 소신호 회로의 **조립 자리는 이 블록 하나**다 -- `metrics_ss`·`ss_nodal`·`metrics_aux` 는 이 필드를 READS 로 읽고 다시 조립하지 않는다(같은 입력 ->
필드 하나, graph 단일 정본).

* 노드 순서 = (`node.dc_colour`, 이름), 소자 순서 = (`device.dc_colour`, 이름) -- 구조 색이 정준 순서라 선형계 행·스탬프 순서가 이름 치환에 불변(색 없는 이름만 이름순).
* `ss_circuit(nodes, ground_nets, input_nets, devices, passive_values) -> SsCircuit` (블록이 부르는 순수 조립 함수, 호출 자리 하나):
  `nodes` = S1 노드 넷 이름 tuple(위치 = 노드 인덱스), `devices` = ((이름, element_class, kind, pins, bulk 넷 또는 None, SsDevice 또는 None), ...).
  - MOS: `MosSmallSignal(d, g, s, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb)` -- 값은 `ss_dev`, b = S1 `bulk` 넷.
  - 수동소자 kind 저항·커패시터(metrics `LOOP_CUT_KINDS` 어휘 -- 소신호 2단자 원소 종류): 값은 `passive_values` 에서만
    (spec 선언 ∪ θ 저항 ∪ 보상 θ, 기본값 없음). 값이 없으면 스탬프하지 않고 `missing` 에 이름을 적는다 -- 회로가 불완전하므로
    부르는 쪽이 모든 소신호 metric 을 정의 불가로 낸다(근사로 채우지 않는다). DC 전도 경로를 이루는 수동소자 = 저항뿐(`is_dc_conducting_passive`, 용량은 DC 에서 개방).
  - 이상 전류원: 소신호 개방(스탬프 없음 -- 이상 전류원의 소신호 어드미턴스는 0).
  - 그 밖(이상 전압원·저항·커패시터 밖 수동 kind·bulk 미정 MOS): `StructureUnresolvedError`(reason `unsupported_rule_branch`,
    rule_branch `ss_element_kind`) -- 소신호 레코드에 그 원소 모형이 없다(9회로에 없음, 생기면 레코드와 함께 넓힌다).
* `ground_nets` = 모든 뷰에서 교류접지(레일 ∪ gate 전용 미구동 넷 -- S1 `ac_ground_class` 비 None), `input_nets` = 입력 포트 넷.
  뷰마다 고정 노드 집합은 이것과 뷰 선언에서 정한다(`metrics_ss`).
"""
from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import StructureUnresolvedError, compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, ELEMENT_SOURCE, MOS_TERMINAL_NAMES, UNSUPPORTED_RULE_BRANCH
from gmid_engine.sizing import CURRENT_SOURCE, METRICS_KEY, RESISTOR, SS_CIRCUIT_WRITER

from .records import LOOP_CUT_KINDS, Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit
from .ss_types import SsCircuit

BRANCH_SS_ELEMENT = "ss_element_kind"
CODE_PASSIVE_MISSING = "passive_value_undeclared"      # 값 없는 수동소자가 있어 회로가 불완전한 때의 정의 불가 사유(metrics_ss·metrics_aux·ss_nodal 이 같은 낱말을 읽는다)
READS = (
    ("device", "ss_dev"), ("device", "element_class"), ("device", "kind"), ("device", "pins"), ("device", "bulk"),
    ("device", "passive_value"), ("device", "dc_colour"),
    ("node", "ac_ground_class"), ("node", "dc_colour"), ("node", "port_direction"),
)
WRITES = (("graph", "ss_circuit"),)


def is_dc_conducting_passive(kind):
    """수동소자 kind 가 DC 전도 경로를 이루는가 -- 저항뿐이다(커패시터는 DC 에서 개방). 소신호 회로 조립과 노달 계가 같은 정의를 읽는다."""
    return kind == RESISTOR


def _unsupported(name, element_class, kind):
    raise StructureUnresolvedError(devices=(name,), detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                            "rule_branch": BRANCH_SS_ELEMENT,
                                                            "element_class": element_class, "kind": kind})


def ss_circuit(nodes, ground_nets, input_nets, devices, passive_values):
    index = {net: i for i, net in enumerate(nodes)}
    values = dict(passive_values)
    mos, resistors, capacitors, r_names, c_names, missing = [], [], [], [], [], []
    for name, element_class, kind, pins, bulk_net, ss in devices:
        pin = dict(pins)
        if element_class == ELEMENT_MOS:
            if bulk_net is None or ss is None:
                _unsupported(name, element_class, kind)
            d, g, s = (index[pin[t]] for t in MOS_TERMINAL_NAMES)
            mos.append(MosSmallSignal(d, g, s, index[bulk_net], ss.gm, ss.gmb, ss.gds, ss.cgs, ss.cgd, ss.cgb, ss.cdb,
                                      ss.csb, label=name))
        elif element_class == ELEMENT_PASSIVE and kind in LOOP_CUT_KINDS:
            if values.get(name) is None:
                missing.append(name)
                continue
            a, b = (index[net] for _t, net in pins)
            if is_dc_conducting_passive(kind):
                resistors.append(Resistor(a, b, values[name], label=name))
                r_names.append(name)
            else:
                capacitors.append(Capacitor(a, b, values[name], label=name))
                c_names.append(name)
        elif not (element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE):
            _unsupported(name, element_class, kind)
    circuit = SmallSignalCircuit(tuple(mos), tuple(resistors), tuple(capacitors))
    return SsCircuit(tuple(nodes), circuit, tuple(r_names), tuple(c_names), tuple(sorted(ground_nets)),
                     tuple(sorted(input_nets)), tuple(sorted(missing)))


@compute_block(SS_CIRCUIT_WRITER, reads=READS, writes=WRITES)
def ss_circuit_field(projection):
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    pins = dict(projection.column("device", "pins"))
    bulk = {m: None if b is None else b.net for m, b in projection.column("device", "bulk")}      # bulk 미정(None) MOS 는 `ss_circuit` 이 거부한다
    ss_values = dict(projection.column("device", "ss_dev"))
    ground = tuple(n for n, c in projection.column("node", "ac_ground_class") if c is not None)
    node_orbit = dict(projection.column("node", "dc_colour"))
    device_orbit = dict(projection.column("device", "dc_colour"))
    nodes = tuple(sorted((n for n, _c in projection.column("node", "ac_ground_class")), key=lambda n: (node_orbit.get(n, -1), n)))
    inputs = tuple(n for n, d in projection.column("node", "port_direction") if d == INPUT_DIRECTION)
    devices = tuple((name, classes[name], kinds[name], pins[name], bulk.get(name), ss_values.get(name))
                    for name in sorted(classes, key=lambda n: (device_orbit.get(n, -1), n)))
    return {("graph", "ss_circuit"): {METRICS_KEY: ss_circuit(nodes, ground, inputs, devices, projection.column("device", "passive_value"))}}
