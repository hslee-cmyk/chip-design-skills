"""평가 커널 컨텍스트 -- S0 당 1회: S1 을 S2 권한표로 넓히고 θ 무관 계획 블록과 커널 구조 파생 블록을 돌린다 (계획 N3.5 평가 커널 컨텍스트,
WP-23 (3) 루프 불변 입력은 S0 수준 필드로, 설계 3.1, 40 §2.4.7 `KernelContext` 행·§2.4.8 v1.9.1 D8).

진입점: `build_kernel_context(s1graph, inputs, lut, *, donors, counters) -> KernelContext`.
`donors`·`counters` = 필수 키워드(기본값 없음) -- 호출자가 `search.open_run()` 으로 만든 실행 하나의 블록 결과 색인·계수(단계 B 는 `StageAResult` 의 두 칸을 넘긴다).
7개 블록에 넘기고 `KernelContext.donors`·`.counters` 에 참조로 둔다.
종속 멤버 선택 순위는 인자가 아니라 graph 필드(`device.theta_class`·S1v `graph.views`·`graph.dependent_facts`)가 정한다(TB-1).

순서: 인자 검사 -> `supplies_declaration`(graph, 레일 집합과 대조) + S1 키의 supplies 지문 대조 -> `lift_s1` ->
`dc_rails` -> `dc_region_decl`(S0 `device.region_decl`, 의도 영역 선언 술어 필드 -- 쓰기 계획 앞) -> graph 대칭 블록 `s1_symmetry`(구조 색·궤도·전류 부호 -- S1 이 같은 선언 표시로 이미 계산했으면 재사용, 표시 = `symmetry_marks(inputs)`)
-> `dc_current_basis`(값 선언 이상 전류원; `off` 소자는 열거에서 뺀다) -> `theta_class`(S0 `device.theta_class`, `DcInputs` 유무 칸 셋) -> `dc_writer_plan`(W3 넷, 입력 DC 선언 여부; `off` 소자는 쓰기 계획에서 뺀다; `device.dc_self_referential` 도 쓴다) -> `dc_scc_order` ->
`kernel_fields`(writer `kernel_context`: `graph/kernel: fixed_values·resistor_values·l_ties` -- L 동치류는 S1v 필드 `graph/s1v: l_classes` 에서 읽는다(derived 와
ratified(`l_owner` 사실) 만 L 공유), S1v 필드가 없으면 소자마다 L) -> `dc_theta_schema`(`graph/kernel: theta_schema` -- engine 수동소자, DEC-92).
계획 블록의 정지(`StructureUnresolvedError`)·KCL 선언 충돌(`InfeasibleTargetError`)은 그대로 전파된다(탐색 전 정지).
모든 블록은 입력 버전이 같으면 재사용이라 같은 실행 안에서 같은 S0 수준 스냅샷 위의 다음 호출은 계산 0 이다(디스크 스냅샷·실행 사이 재사용은 없다).
결과 `KernelContext(base, inputs, lut, donors, counters)` 는 참조만 담는다 -- θ 스키마·고정 노드·저항 값·L 묶음은 `base` 의 `graph/kernel` 필드, 계획 블록 입력 버전은
`base.block_version(writer)`(writer = `PLAN_WRITERS`)로 읽는다(사본 없음).
* `lut.w_keys` 에 S1 MOS kind 가 모두 있어야 하고 그 (kind, w_key) 슬라이스가 LUT 에 있어야 한다(`ValueError`).
* 노드 목표 넷은 S1 노드여야 한다(`ValueError` -- spec 로더가 이미 거부하는 경우라 계약 위반).
* `inputs.engine_elements` 이름은 S1 원소여야 한다(`ValueError`, 같은 이유). 그중 수동소자만 `dc_theta_schema` 로 간다.
* L 동치류가 S1 원소가 아니거나 MOS 만의 서로소 묶음이 아니면 `ValueError`(`kernel_fields`).
"""
from gmid_engine.core import fp_of
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE, ELEMENT_SOURCE, S1_SYMMETRY_WRITER, S1Graph, s1_symmetry, supplies_declaration

from .current_basis import dc_current_basis
from .kernel_fields import kernel_fields
from .region_decl import dc_region_decl
from .s2_lift import lift_s1
from .s2_values import (
    CURRENT_SOURCE,
    DC_CURRENT_BASIS_WRITER,
    DC_RAILS_WRITER,
    DC_REGION_DECL_WRITER,
    DC_SCC_ORDER_WRITER,
    DC_THETA_SCHEMA_WRITER,
    DC_WRITER_PLAN_WRITER,
    KERNEL_CONTEXT_WRITER,
    THETA_CLASS_WRITER,
    DcInputs,
    KernelContext,
    LutAccess,
)
from .scc_order import dc_scc_order
from .symmetry_marks import symmetry_marks
from .theta_class import theta_class
from .theta_schema import dc_theta_schema
from .w0_rails import dc_rails
from .writer_plan import dc_writer_plan

PLAN_WRITERS = (DC_RAILS_WRITER, DC_REGION_DECL_WRITER, S1_SYMMETRY_WRITER, DC_CURRENT_BASIS_WRITER, THETA_CLASS_WRITER, DC_WRITER_PLAN_WRITER, DC_SCC_ORDER_WRITER,
                KERNEL_CONTEXT_WRITER, DC_THETA_SCHEMA_WRITER)


def build_kernel_context(s1graph, inputs, lut, *, donors, counters):
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
    base = lift_s1(s1graph)
    base = dc_rails(base, supplies, donors=donors, counters=counters)
    base = s1_symmetry(base, supplies, symmetry_marks(inputs), donors=donors, counters=counters)     # S1 의 대칭 블록 -- 같은 표시면 재사용(계산 0)
    base = dc_region_decl(base, tuple(inputs.regions), donors=donors, counters=counters)        # S0 술어 필드 -- 소자 열거 뿌리(전류 기저·쓰기 계획·θ 스키마)가 `off` 를 뺀다
    base = dc_current_basis(base, sources, donors=donors, counters=counters)
    base = theta_class(base, inputs.has_gbw_target, inputs.has_rout_limit, inputs.has_settling, donors=donors, counters=counters)      # S0 θ 분류 -- 쓰기 계획의 종속 멤버 순위 입력
    base = dc_writer_plan(base, tuple(sorted(targets)), inputs.input_dc_v is not None, donors=donors, counters=counters)
    base = dc_scc_order(base, donors=donors, counters=counters)
    base = kernel_fields(base, tuple(sorted(targets.items())), inputs.input_dc_v, tuple(inputs.element_values), donors=donors, counters=counters)
    engine_passives = tuple(n for n in sorted(inputs.engine_elements) if classes[n] == ELEMENT_PASSIVE)
    base = dc_theta_schema(base, engine_passives, donors=donors, counters=counters)
    return KernelContext(base, inputs, lut, donors, counters)
