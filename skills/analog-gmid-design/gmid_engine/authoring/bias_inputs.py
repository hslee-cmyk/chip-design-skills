"""외부 바이어스 입력 선언 `bias_inputs` 와 gate 전용 넷 게이트 (Q6, SYNTHESIS T15 (1), 2026-10-08 사용자 승인).

진입점: `bias_input_declaration(doc, devices, passives, sources, rails, ports) -> tuple[str]` (넷 이름순).

`bias_inputs` 는 선택 최상위 키: 넷 이름 문자열의 list. connectivity 를 바꾸지 않는 선언이다(`connectivity_fp` 에 들어가지 않는다).
**gate 전용 넷** = MOS gate 단자에만 나타나고 다른 어떤 단자에도 없는 넷 -- MOS drain/source/선언 bulk, 수동소자·이상원
terminals, 레일 선언(supply_nets), 포트 어디에도 없는 넷(구동 소자가 topology 안에 없다 = 외부에서 바이어스를 받아야 한다).
넷 이름은 보지 않는다(선언 집합과 단자 구조로만 판정).
거부(모두 모아 `SchemaRejectedError` 한 번, detail `gate="bias_inputs"`):
* `bias_inputs_type` -- JSON list 가 아니다. `bias_input_entry` -- 원소가 비어 있지 않은 문자열이 아니다.
* `bias_input_duplicate` -- 같은 넷을 두 번 선언했다.
* `gate_only_undeclared` -- gate 전용 넷인데 선언에 없다.
* `bias_input_not_gate_only` -- 선언한 넷이 gate 전용이 아니다(레일·포트·드레인/소스/벌크/2단자 단자에 있거나 gate 에도 없다).
`rails`·`ports` 선언이 거부돼 입력이 없으면 호출자(`load_topology`)가 이 검사를 `not_evaluated` 에 남기고 부르지 않는다.
"""
from ._rejection import reject, require_object
from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .topology_model import SchemaHit

BIAS_INPUTS_KEY = "bias_inputs"


def gate_only_nets(devices, passives, sources, rails, ports):
    """gate 전용 넷 frozenset (위 정의)."""
    non_gate = set(two_terminal_nets(passives + sources)) | set(rails.nets) | {p.net for p in ports}
    for x in devices:
        non_gate.update((x.d, x.s))
        if x.bulk is not None:
            non_gate.add(x.bulk)
    return frozenset(x.g for x in devices) - non_gate


def bias_input_declaration(doc, devices, passives, sources, rails, ports):
    require_object("bias_inputs", doc)
    declared = doc.get(BIAS_INPUTS_KEY, [])
    if not isinstance(declared, list):
        reject("bias_inputs", BIAS_INPUTS_KEY,
               (SchemaHit("bias_inputs_type", BIAS_INPUTS_KEY, "bias_inputs 는 넷 이름 문자열의 list 여야 한다: "
                          + type(declared).__name__),))
    hits = []
    nets = []
    for i, net in enumerate(declared):
        where = BIAS_INPUTS_KEY + "[" + str(i) + "]"
        if not isinstance(net, str) or not net:
            hits.append(SchemaHit("bias_input_entry", where, "바이어스 입력 넷은 비어 있지 않은 문자열이어야 한다: " + repr(net)))
        elif net in nets:
            hits.append(SchemaHit("bias_input_duplicate", where, "바이어스 입력 넷 " + repr(net) + " 을 두 번 선언했다", (net,)))
        else:
            nets.append(net)
    only = gate_only_nets(devices, passives, sources, rails, ports)
    for net in sorted(set(nets) - only):
        hits.append(SchemaHit("bias_input_not_gate_only", BIAS_INPUTS_KEY,
                              "선언한 바이어스 입력 넷 " + repr(net) + " 이 gate 전용이 아니다(gate 에 없거나 레일·포트·"
                              "drain/source/bulk/2단자 단자에도 있다)", (net,)))
    for net in sorted(only - set(nets)):
        hits.append(SchemaHit("gate_only_undeclared", BIAS_INPUTS_KEY,
                              "넷 " + repr(net) + " 은 MOS gate 단자에만 있는 gate 전용 넷인데 bias_inputs 에 선언되지 않았다"
                              "(외부 바이어스 입력이면 선언한다)", (net,)))
    if hits:
        reject("bias_inputs", BIAS_INPUTS_KEY, hits)
    return tuple(sorted(nets))
