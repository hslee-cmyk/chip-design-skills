"""θ 스키마(DOF 표) 계산 블록 (설계 3.1 5, 계획 DEC-70 결정변수, DEC-88, DEC-92, N3.7 DOF 입력).

진입점: `dc_theta_schema`(`@compute_block`) -- `dc_theta_schema(snapshot, engine_passives)`. θ 무관(S0 당 1회).
writes S0 수준 필드 `graph/kernel: theta_schema`(key `KERNEL_KEY` -- 옛 `graph/dc: dc_theta_schema` 를 옮긴 것, writer 그대로, 설계 40 §2.4.7·§2.4.8 v1.9.1 D8).
reads 에 커널 컨텍스트 블록(`kernel_fields`)이 쓴 `graph/kernel: resistor_values`(spec 에 값이 선언된 DC 경로 저항 -- 그 이름이 `declared_resistors`)·`l_ties` 가 든다.

성분 (kind, key):
* `ln_idu`(쓰기 소자 -- DEC-88 반전 좌표 ln IDu, IDu = ID·L/W), `L`(MOS -- **L 동치류당 하나**(DEC-17, LR1, 설계 40 §3.2-1): `l_ties`(필드) =
  ((멤버, 주인), ...) = S1v derived 동치류의 비주인 멤버는 성분이 없고(주인의 L 을 `size_and_seal` 이 물려준다), 동치류에 들지 않은
  MOS 는 소자마다 하나. status 가 derived 가 아닌 동치류(proposed·review_needed)는 `build_kernel_context` 가 `l_ties` 에 넣지 않아 소자마다 L),
* `y`(W4 키마다, [0, 1] 창 안 위치), `current`(원소 단위 KCL 독립 기저), `resistance`(DC 경로 저항 중 spec 값 미선언).
* [DEC-92] `capacitance`(spec mode engine 커패시터), `ss_resistance`(spec mode engine 저항 중 DC 전류 0 -- 잎 가지치기
  `basis.pruned` -- 이고 영점 상쇄 구조 규칙이 값을 정하지 못한 것). 둘은 DC 동작점을 바꾸지 않으므로(커패시터는 DC 엣지가
  아니고, 가지치기 저항은 전류 0 이라 강하 0) DC 블록이 읽지 않는다 -- 소신호 회로(metrics `ss_evaluate`)에만 들어간다.
`declared_resistors` = `resistor_values` 필드의 저항 이름, `engine_passives` = spec 값 mode 가 engine 인 수동소자 이름 tuple(extras).
DC 경로(가지치기 안 된) engine 저항은 지금처럼 `resistance` 다(값 미선언 DC 저항 규칙, DEC-70).

영점 상쇄 구조 규칙(DEC-92 (3)(a), `zero_cancel`): 가지치기된 engine 저항 R 마다 연결만으로 --
1. 수동 망 N(R): R 에서 시작해 '내부 넷'(레일·포트 아님, 단자가 모두 수동소자, MOS bulk 아님)을 건너 닿는 수동소자를 모은다.
   망이 닿은 내부 넷 밖 넷 = 경계 넷.
2. 망에 커패시터가 없으면 `ZC_NO_CAPACITOR`, R 밖 저항이 있으면 `ZC_MULTIPLE_RESISTORS`(Σgm 를 어느 저항에 둘지 미정),
   R 의 두 단자 중 경계 넷이 정확히 하나(= 저항 끝 넷 E)가 아니면 `ZC_RESISTOR_END`.
3. S = source 가 교류접지(`ac_ground_class` 있음)인 MOS(CS 셀) 중 {gate, drain} = {E, 나머지 경계 넷 하나} 인 것 -- 망이
   그 셀의 gate–drain 을 잇는(되먹임/앞먹임으로 우회하는) 셀. 직렬 R–C 의 임피던스 R + 1/sC 는 R·C 순서와 무관하므로 E 가 셀의
   drain 이든 gate 든 같은 규칙이다(계획 문구 '저항 끝 넷을 출력으로'는 R 이 출력 쪽에 있는 배치의 표현). 비면 `ZC_NO_CELL`,
   E 가 어떤 셀에는 drain·다른 셀에는 gate 면 `ZC_MIXED_DIRECTION`.
4. 위가 모두 통과하면 R 은 θ 가 아니고 봉인 스냅샷에서 R = 1/Σ_{c∈S} gm_c(metrics `ss_evaluate` 가 `ss_dev` gm 으로 계산),
   아니면 R 은 `ss_resistance` θ(DEC-92 (3)(b) 폴백). 회로별 S 는 J7 ratify 대상 -- 판정은 `zero_cancel` 에 남는다.

θ 전류 정의역(`current_cone`): KCL 기저 행 중 MOS 행마다 (MOS, 항) -- 전도 MOS 전류 > 0 을 θ 의 선형 부등식으로 옮긴
것이다(평가 실패가 아니라 정의역 밖, `check_theta` 가 거부). 기저 원소가 MOS 자신이면 그 행 = θ_I > 0 상자 하한.
`fixed` = 행이 읽는 값 선언 이상원 값.
"""
from gmid_engine.core import compute_block
from gmid_engine.graph import ELEMENT_MOS, ELEMENT_PASSIVE

from .s2_values import (
    CAPACITOR,
    COORD_WRITER,
    DC_KEY,
    DC_THETA_SCHEMA_WRITER,
    KERNEL_KEY,
    REL_INPUT_POINT,
    REL_WINDOW,
    RESISTOR,
    THETA_CAPACITANCE,
    THETA_CURRENT,
    THETA_L,
    THETA_LN_IDU,
    THETA_RESISTANCE,
    THETA_SS_RESISTANCE,
    THETA_Y,
    ZC_MIXED_DIRECTION,
    ZC_MULTIPLE_RESISTORS,
    ZC_NO_CAPACITOR,
    ZC_NO_CELL,
    ZC_RESISTOR_END,
    ThetaSchema,
    ZeroCancel,
)

READS = (
    ("device", "dc_coord"), ("node", "dc_writer"), ("graph", "dc_current_basis"), ("device", "element_class"),
    ("device", "kind"), ("device", "pins"), ("device", "bulk"), ("node", "terminals"), ("node", "is_rail"),
    ("node", "port_direction"), ("node", "ac_ground_class"), ("graph", "resistor_values"), ("graph", "l_ties"),
)
WRITES = (("graph", "theta_schema"),)


def _internal_nets(projection, classes):
    """수동 망을 이어 주는 내부 넷: 레일·포트가 아니고, 단자가 모두 수동소자이며 MOS bulk 가 아닌 넷."""
    rails = {n for n, r in projection.column("node", "is_rail") if r}
    ports = {n for n, d in projection.column("node", "port_direction") if d is not None}
    bulks = {b.net for _m, b in projection.column("device", "bulk") if b.net is not None}
    out = set()
    for net, terminals in projection.column("node", "terminals"):
        if net in rails or net in ports or net in bulks or not terminals:
            continue
        if all(classes[element] == ELEMENT_PASSIVE for element, _t in terminals):
            out.add(net)
    return out


def _zero_cancel(resistor, projection, classes, kinds, pins, internal):
    terminals = dict(projection.column("node", "terminals"))
    elements, boundary, seen_nets = {resistor}, set(), set()
    stack = sorted(set(pins[resistor].values()))
    while stack:
        net = stack.pop()
        if net in seen_nets:
            continue
        seen_nets.add(net)
        if net not in internal:
            boundary.add(net)
            continue
        for element, _t in terminals[net]:
            if element not in elements:
                elements.add(element)
                stack.extend(sorted(set(pins[element].values()) - seen_nets))
    ends = sorted(set(pins[resistor].values()) & boundary)
    end = ends[0] if len(ends) == 1 else None
    far = tuple(sorted(boundary - set(ends)))
    if not any(kinds[e] == CAPACITOR for e in elements):
        return ZeroCancel(resistor, end, far, (), ZC_NO_CAPACITOR)
    if any(kinds[e] == RESISTOR for e in elements if e != resistor):
        return ZeroCancel(resistor, end, far, (), ZC_MULTIPLE_RESISTORS)
    if end is None:
        return ZeroCancel(resistor, end, far, (), ZC_RESISTOR_END)
    grounded = {n for n, c in projection.column("node", "ac_ground_class") if c is not None}
    cells, sides = [], set()
    for name in sorted(n for n, c in classes.items() if c == ELEMENT_MOS):
        p = pins[name]
        if p["s"] not in grounded:
            continue
        if p["d"] == end and p["g"] in far:
            cells.append(name)
            sides.add("d")
        elif p["g"] == end and p["d"] in far:
            cells.append(name)
            sides.add("g")
    if not cells:
        return ZeroCancel(resistor, end, far, (), ZC_NO_CELL)
    if len(sides) > 1:
        return ZeroCancel(resistor, end, far, tuple(cells), ZC_MIXED_DIRECTION)
    return ZeroCancel(resistor, end, far, tuple(cells), None)


@compute_block(DC_THETA_SCHEMA_WRITER, reads=READS, writes=WRITES)
def dc_theta_schema(projection):
    (engine_passives,) = projection.extras
    declared_resistors = tuple(name for name, _value in projection.value("graph", KERNEL_KEY, "resistor_values"))
    l_ties = projection.value("graph", KERNEL_KEY, "l_ties")       # 빈 tuple = L 동치류 없음(소자마다 L)
    classes = dict(projection.column("device", "element_class"))
    kinds = dict(projection.column("device", "kind"))
    pins = {name: dict(p) for name, p in projection.column("device", "pins")}
    basis = projection.value("graph", DC_KEY, "dc_current_basis")
    components = set()
    for name, coord in projection.column("device", "dc_coord"):
        if coord.role == COORD_WRITER:
            components.add((THETA_LN_IDU, name))
    tied = {member for member, _owner in l_ties}
    components.update((THETA_L, name) for name, cls in classes.items() if cls == ELEMENT_MOS and name not in tied)
    components.update((THETA_Y, w.y_key) for _net, w in projection.column("node", "dc_writer")
                      if w.relation in (REL_WINDOW, REL_INPUT_POINT) and w.y_key is not None)    # 입력 점은 두 포트가 같은 y 키 하나
    components.update((THETA_CURRENT, name) for name in basis.free)
    components.update((THETA_RESISTANCE, name) for name, _a, _b in basis.ends
                      if classes[name] == ELEMENT_PASSIVE and kinds[name] == RESISTOR and name not in declared_resistors)
    engine = sorted(n for n in engine_passives if classes.get(n) == ELEMENT_PASSIVE)
    components.update((THETA_CAPACITANCE, n) for n in engine if kinds[n] == CAPACITOR)
    pruned = set(basis.pruned)
    internal = _internal_nets(projection, classes) if any(n in pruned for n in engine) else set()
    zero_cancel = tuple(_zero_cancel(n, projection, classes, kinds, pins, internal)
                        for n in engine if kinds[n] == RESISTOR and n in pruned)
    components.update((THETA_SS_RESISTANCE, z.resistor) for z in zero_cancel if z.reason is not None)
    rows = dict(basis.rows)
    cone = tuple((m, rows[m]) for m in sorted(basis.mos))
    schema = ThetaSchema(tuple(sorted(components)), cone, tuple(basis.fixed), zero_cancel)
    return {("graph", "theta_schema"): {KERNEL_KEY: schema}}
