"""S2 열 -> 정수 인덱스 소신호 회로 (7a design 4.5 단계 5 '소자 이름 -> 원소 인덱스, 넷 -> 노드 인덱스', 설계 MOD5 3.3).

진입점: `ss_circuit(nodes, ground_nets, input_nets, devices, passive_values) -> SsCircuit`.

* `nodes` = S1 노드 넷 이름 tuple(정렬) -- 노드 인덱스 = 위치(이름 리터럴 없음, 이름 순서는 재번호 불변 I-7 이라 결과 무관).
* `devices` = ((이름, element_class, kind, pins, bulk 넷 또는 None, SsDevice 또는 None), ...) 이름순.
  - MOS: `MosSmallSignal(d, g, s, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb)` -- 값은 `ss_dev`, b = S1 `bulk` 넷.
  - 수동소자 kind 저항·커패시터(metrics `LOOP_CUT_KINDS` 어휘 -- 소신호 2단자 원소 종류): 값은 `passive_values` 에서만
    (spec 선언 ∪ θ 저항 ∪ 보상 θ, 기본값 없음). 값이 없으면 스탬프하지 않고 `missing` 에 이름을 적는다 -- 회로가 불완전하므로
    부르는 쪽이 모든 소신호 metric 을 정의 불가로 낸다(근사로 채우지 않는다).
  - 이상 전류원: 소신호 개방(스탬프 없음 -- 이상 전류원의 소신호 어드미턴스는 0).
  - 그 밖(이상 전압원·저항·커패시터 밖 수동 kind·bulk 미정 MOS): `StructureUnresolvedError`(reason `unsupported_rule_branch`,
    rule_branch `ss_element_kind`) -- 소신호 레코드에 그 원소 모형이 없다(9회로에 없음, 생기면 레코드와 함께 넓힌다).
* `ground_nets` = 모든 뷰에서 교류접지(레일 ∪ gate 전용 미구동 넷 -- S1 `ac_ground_class` 비 None), `input_nets` = 입력 포트 넷.
  뷰마다 고정 노드 집합은 이것과 뷰 선언에서 정한다(`metrics_ss`).
"""
from gmid_engine.core import StructureUnresolvedError
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, ELEMENT_SOURCE, MOS_TERMINAL_NAMES, UNSUPPORTED_RULE_BRANCH
from gmid_engine.sizing import CURRENT_SOURCE

from .records import LOOP_CUT_KINDS, Capacitor, MosSmallSignal, Resistor, SmallSignalCircuit
from .ss_types import SsCircuit

BRANCH_SS_ELEMENT = "ss_element_kind"


def _unsupported(name, element_class, kind):
    raise StructureUnresolvedError(devices=(name,), detail={"reason": UNSUPPORTED_RULE_BRANCH,
                                                            "rule_branch": BRANCH_SS_ELEMENT,
                                                            "element_class": element_class, "kind": kind})


def ss_circuit(nodes, ground_nets, input_nets, devices, passive_values):
    index = {net: i for i, net in enumerate(nodes)}
    values = dict(passive_values)
    resistor_kind = LOOP_CUT_KINDS[0]
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
            if kind == resistor_kind:
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
