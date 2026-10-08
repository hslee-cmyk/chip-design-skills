"""평가 커널 컨텍스트 -- S0 당 1회: S1 을 S2 권한표로 옮기고 θ 무관 계획 블록을 돌린다 (계획 N3.5 평가 커널 컨텍스트,
WP-23 (3) 루프 불변 입력은 컨텍스트에, 설계 3.1).

진입점: `build_kernel_context(s1graph, inputs, lut, l_classes=()) -> KernelContext`. `l_classes` = `graph.build_s1v` 의 `S1v.l_classes`(derived 만 L 공유로 쓴다).

순서: 인자 검사 -> `supplies_declaration`(graph, 레일 집합과 대조) + S1 키의 supplies 지문 대조 -> `lift_s1` ->
`dc_rails` -> `dc_struct_colour`(구조 색) -> `dc_current_basis`(값 선언 이상 전류원) -> `dc_writer_plan`(W3 넷, 입력 DC 선언 여부) -> `dc_scc_order` ->
`dc_theta_schema`(값 선언 저항, engine 수동소자 -- DEC-92). 계획 블록의 정지(`StructureUnresolvedError`)·KCL 선언 충돌(`InfeasibleTargetError`)은
그대로 전파된다(탐색 전 정지).
* `lut.w_keys` 에 S1 MOS kind 가 모두 있어야 하고 그 (kind, w_key) 슬라이스가 LUT 에 있어야 한다(`ValueError`).
* 노드 목표 넷은 S1 노드여야 한다(`ValueError` -- spec 로더가 이미 거부하는 경우라 계약 위반).
* `inputs.engine_elements` 이름은 S1 원소여야 한다(`ValueError`, 같은 이유). 그중 수동소자만 `dc_theta_schema` 로 간다.
"""
from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import fp_of
from gmid_engine.graph import (ELEMENT_MOS, ELEMENT_PASSIVE, ELEMENT_SOURCE, GRAPH_KEY, STATUS_DERIVED, S1Graph,
                               supplies_declaration)

from .current_basis import dc_current_basis
from .s2_lift import lift_s1
from .s2_values import (
    CURRENT_SOURCE,
    DC_CURRENT_BASIS_WRITER,
    DC_KEY,
    DC_RAILS_WRITER,
    DC_SCC_ORDER_WRITER,
    DC_STRUCT_COLOUR_WRITER,
    DC_THETA_SCHEMA_WRITER,
    DC_WRITER_PLAN_WRITER,
    RESISTOR,
    DcInputs,
    KernelContext,
    LutAccess,
)
from .scc_order import dc_scc_order
from .struct_colour import dc_struct_colour
from .theta_schema import dc_theta_schema
from .w0_rails import dc_rails
from .writer_plan import dc_writer_plan

PLAN_WRITERS = (DC_RAILS_WRITER, DC_STRUCT_COLOUR_WRITER, DC_CURRENT_BASIS_WRITER, DC_WRITER_PLAN_WRITER, DC_SCC_ORDER_WRITER,
                DC_THETA_SCHEMA_WRITER)


def build_kernel_context(s1graph, inputs, lut, l_classes=()):
    if not isinstance(s1graph, S1Graph):
        raise TypeError("build_kernel_context: s1graph 는 graph.build_s1 결과 S1Graph 여야 한다")
    if not isinstance(inputs, DcInputs) or not isinstance(lut, LutAccess):
        raise TypeError("build_kernel_context: inputs 는 DcInputs, lut 는 LutAccess 여야 한다")
    rails = frozenset(net for net, is_rail in s1graph.column("node", "is_rail") if is_rail)
    supplies = supplies_declaration(dict(inputs.supplies_v), rails)
    if fp_of(supplies) != s1graph.key.supplies_v_fp:
        raise ValueError("build_kernel_context: S1 을 만든 supplies_v 와 inputs.supplies_v 가 다르다(bulk 기본 규칙 불일치)")
    classes = dict(s1graph.column("device", "element_class"))
    kinds = dict(s1graph.column("device", "kind"))
    w_keys = dict(lut.w_keys)
    for kind in sorted({kinds[n] for n, c in classes.items() if c == ELEMENT_MOS}):
        if kind not in w_keys or (kind, w_keys[kind]) not in lut.memo.lut.slice_map:
            raise ValueError("build_kernel_context: LUT 폭 슬라이스가 없는 kind " + repr(kind))
    nodes = {net for net, _r in s1graph.column("node", "is_rail")}
    targets = dict(inputs.node_targets)
    unknown = sorted(set(targets) - nodes)
    if unknown:
        raise ValueError("build_kernel_context: 노드 목표 넷이 S1 노드가 아니다 " + repr(unknown))
    stray = sorted(set(inputs.engine_elements) - set(classes))
    if stray:
        raise ValueError("build_kernel_context: engine 원소가 S1 원소가 아니다 " + repr(stray))
    values = dict(inputs.element_values)
    sources = tuple((n, values.get(n)) for n in sorted(classes)
                    if classes[n] == ELEMENT_SOURCE and kinds[n] == CURRENT_SOURCE)
    pruned = {e for e, _round in s1graph.value("graph", GRAPH_KEY, "dc_pruned")}
    resistors = tuple((n, values[n]) for n in sorted(classes)
                      if classes[n] == ELEMENT_PASSIVE and kinds[n] == RESISTOR and n not in pruned
                      and values.get(n) is not None)
    base = lift_s1(s1graph)
    base = dc_rails(base, supplies)
    base = dc_struct_colour(base)
    base = dc_current_basis(base, sources)
    base = dc_writer_plan(base, tuple(sorted(targets)), inputs.input_dc_v is not None)
    base = dc_scc_order(base)
    engine_passives = tuple(n for n in sorted(inputs.engine_elements) if classes[n] == ELEMENT_PASSIVE)
    classes_of_l = tuple((m, c.owner) for c in l_classes if c.status == STATUS_DERIVED for m in c.members if m != c.owner)
    stray_l = sorted({n for pair in classes_of_l for n in pair} - set(classes))
    if stray_l:
        raise ValueError("build_kernel_context: L 동치류 멤버가 S1 원소가 아니다 " + repr(stray_l))
    base = dc_theta_schema(base, tuple(n for n, _v in resistors), engine_passives)
    fixed = dict(targets)
    if inputs.input_dc_v is not None:
        for net, direction in s1graph.column("node", "port_direction"):
            if direction == INPUT_DIRECTION and net not in fixed:
                fixed[net] = float(inputs.input_dc_v)
    schema = base.value("graph", DC_KEY, "dc_theta_schema")
    versions = tuple((w, base.block_version(w)) for w in PLAN_WRITERS)
    return KernelContext(base, inputs, lut, schema, tuple(sorted(fixed.items())), resistors, versions, tuple(sorted(classes_of_l)))
