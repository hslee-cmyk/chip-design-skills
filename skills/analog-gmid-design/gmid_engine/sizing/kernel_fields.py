"""커널 컨텍스트 구조 파생 계산 블록 -- 고정 노드·DC 경로 저항 선언값·L 묶음을 S0 수준 필드 `graph/kernel` 에 쓴다
(설계 40 §2.4.7 `KernelContext` 행·§2.4.8 '커널 컨텍스트 구조 파생', v1.9.1 D8; 계획 N3.5 평가 커널 컨텍스트, WP-23 (3)).

진입점: `kernel_fields`(`@compute_block`, writer `kernel_context`) -- `kernel_fields(snapshot, targets, input_dc_v, element_values)`. θ 무관(S0 당 1회).

* extras: `targets` = ((넷, V), ...) spec 노드 목표(W3), `input_dc_v` = 선언 입력 DC(V) 또는 None, `element_values` = ((원소, 값 또는 None), ...) spec 원소 값.
* writes(key `KERNEL_KEY`):
  - `fixed_values` = ((넷, V), ...) 넷 이름순 -- W3 노드 목표 + (입력 DC 가 선언되면) 목표가 없는 입력 포트의 입력 DC.
  - `resistor_values` = ((저항, Ω), ...) 이름순 -- spec 에 값이 선언된 DC 경로 저항(S1 `dc_pruned` 잎 가지치기 저항 제외).
  - `l_ties` = ((멤버, 주인), ...) 정렬 -- S1v L 동치류(`graph/s1v: l_classes`) 중 derived·ratified 의 비주인 멤버(LR1 L 공유; θ 스키마에는 동치류당 주인 L 하나).
    S1v 필드가 없는 스냅샷(구조만 -- S1v 를 만들지 않은 실행)이면 빈 tuple(소자마다 L).
* L 동치류가 S1 원소가 아니거나 MOS 만의 서로소 묶음이 아니면(MOS 아님·주인이 다른 동치류 멤버·두 동치류 멤버) `ValueError`(계약 위반).
"""
from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, GRAPH_KEY, S1V_KEY, STATUS_DERIVED, STATUS_RATIFIED

from .s2_values import KERNEL_CONTEXT_WRITER, KERNEL_KEY, RESISTOR

READS = (("device", "element_class"), ("device", "kind"), ("node", "port_direction"), ("graph", "dc_pruned"), ("graph", "l_classes"))
WRITES = (("graph", "fixed_values"), ("graph", "resistor_values"), ("graph", "l_ties"))


def _l_ties(l_classes, classes):
    pairs = tuple((m, c.owner) for c in l_classes if c.status in (STATUS_DERIVED, STATUS_RATIFIED) for m in c.members if m != c.owner)
    stray = sorted({n for pair in pairs for n in pair} - set(classes))
    if stray:
        raise ValueError("build_kernel_context: L 동치류 멤버가 S1 원소가 아니다 " + repr(stray))
    ties = tuple(sorted(pairs))
    members = [m for m, _o in ties]
    owners = {o for _m, o in ties}
    bad = sorted({n for pair in ties for n in pair if classes[n] != ELEMENT_MOS} | (owners & set(members))
                 | {m for m in members if members.count(m) > 1})
    if bad:
        raise ValueError("build_kernel_context: L 동치류가 MOS 만의 서로소 묶음이 아니다(MOS 아님·주인이 다른 동치류 멤버·두 동치류 멤버) "
                         + repr(bad))
    return ties


@compute_block(KERNEL_CONTEXT_WRITER, reads=READS, writes=WRITES)
def kernel_fields(projection):
    targets, input_dc_v, element_values = projection.extras
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    values = dict(element_values)
    pruned = {e for e, _round in projection.value("graph", GRAPH_KEY, "dc_pruned")}
    resistors = tuple((n, values[n]) for n in sorted(classes)
                      if classes[n] == ELEMENT_PASSIVE and kinds[n] == RESISTOR and n not in pruned and values.get(n) is not None)
    l_classes = dict(projection.column("graph", "l_classes")).get(S1V_KEY, ())
    fixed = dict(targets)
    if input_dc_v is not None:
        for net, direction in projection.column("node", "port_direction"):
            if direction == INPUT_DIRECTION and net not in fixed:
                fixed[net] = float(input_dc_v)
    return {("graph", "fixed_values"): {KERNEL_KEY: tuple(sorted(fixed.items()))}, ("graph", "resistor_values"): {KERNEL_KEY: resistors},
            ("graph", "l_ties"): {KERNEL_KEY: _l_ties(l_classes, classes)}}
