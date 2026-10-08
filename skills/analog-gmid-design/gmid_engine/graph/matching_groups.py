"""레이아웃 matching 분류 -- 차동쌍 후보(matching_offset)·matching 그룹·제외 기록 (SYNTHESIS Q8 (i)(iii), 사용자 승인
2026-10-07, 정의는 CONTRACT 4.5a).

진입점: `s1_matching_groups` -- core `@compute_block`(writer `S1_MATCHING_GROUPS_WRITER`, reads `MATCHING_GROUPS_READS`,
writes `graph.rel_matching_offset`·`graph.matching_groups`·`graph.matching_dispositions`).

    snapshot = s1_matching_groups(snapshot)

규칙은 S1 필드(가지·DC 역할·교류접지 분류·포트 방향·pins·dc_nets)만 쓴다. 소자·넷 이름은 결정론적 순서에만 쓴다.

* 구조 정의(모두 CONTRACT 4.5a 와 같은 말):
  - G = `node.ac_ground_class` 가 있는 넷(레일 ∪ gate 전용 비입력 넷).
  - 가지 넷 = `graph.branches` 의 가지 하나의 ends ∪ segment 넷. MOS 의 가지 = 그 MOS 를 원소로 갖는 가지(MOS 는 가지치기
    대상이 아니라 정확히 하나).
  - 블록 = 레일 아닌 가지 끝 넷을 공유하는 가지끼리 이은 연결 성분(DC 전도 그래프에서 레일을 지운 성분).
  - 바이어스 넷 B = 바이어스 블록들의 넷. 바이어스 블록(최대 고정점) = 입력 포트 넷이 없고 블록 안 diode 아닌 MOS 의 gate 가
    모두 G 또는 바이어스 블록 넷인 블록.
  - 루프 신호 넷 L = 방향 그래프(노드 = G 밖 넷, MOS 마다 g→d·g→s·s→d, DC 를 통하는 수동소자(`dc_nets` 있음)마다 양방향,
    커패시터·이상원 엣지 없음)의 강연결 성분 중 넷 2개 이상, 성분 안 MOS 엣지가 있고, 어느 가지 넷 하나에도 다 들지 않는 것.
* 차동쌍 후보 `rel_matching_offset`: 같은 (kind, 비레일 source) MOS 묶음 중 gate 넷이 2개 이상으로 갈리는 것에서 바이어스
  형제(dc_role diode_reference·bias_current_source / gate ∈ G / gate 가 자기 가지 넷)를 먼저 빼고, 남은 멤버의 gate 가 2개
  이상이면 RelEdge(남은 멤버 정확히 2 -> derived, 3 이상 -> review_needed). 뺀 소자는 `bias_sibling` 기록.
* gs 미러 후보(gate 비레일 `graph.gs_groups` 묶음): diode 멤버가 있고 diode 블록 밖 멤버(소비 소자)가 있으면 gate ∈ B ->
  소비 소자 `bias_distribution`, gate ∈ L -> `feedback_shared`(제외 기록) 후 diode 쪽 멤버·같은 블록 소비 소자끼리 2개 이상이면
  mirror. 그 밖은 묶음 전체 mirror. 같은 블록 소비 소자가 2개 이상이면 세분(J14 1번): drain = derived 차동쌍 공통 source
  -> 꼬리(diode 와 `mirror_tail_ratio`, disposition 에서 빠짐), drain = diode 넷 -> 그룹 없음, drain 이 대응 넷 짝인 둘 ->
  `mirror_consumer_symmetric`, 해당 없으면 옛 `mirror_consumer_block`. 대응 넷 = derived 2멤버 차동쌍 drain 에서 가지 서명이
  같은 가지 쌍을 따라 퍼뜨린 짝(CONTRACT 4.5a).
* `branch_symmetric`: derived 그룹(mirror·diff_pair, 새로 찾은 branch_symmetric 포함)을 seed 로, 멤버마다 같은 kind 이고
  source == 멤버 drain(비레일)인 MOS 를 gate 넷별로 모아 source 넷이 2개 이상이면 새 그룹 -- 고정점까지.
"""
from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import compute_block, sorted_items

from .s1_values import (
    DISPOSITION_BIAS_DISTRIBUTION,
    DISPOSITION_BIAS_SIBLING,
    DISPOSITION_FEEDBACK_SHARED,
    DOMAIN_DC_TO_SS,
    ELEMENT_MOS,
    ELEMENT_PASSIVE,
    GRAPH_KEY,
    J_BRANCH_SYMMETRIC,
    J_DIFF_PAIR,
    J_MATCH_CLASS,
    MATCH_BRANCH_SYMMETRIC,
    MATCH_DIFF_PAIR,
    MATCH_MIRROR,
    MATCHING_GROUPS_READS,
    MATCHING_GROUPS_WRITES,
    MIRROR_RULE_CONSUMER_BLOCK,
    MIRROR_RULE_CONSUMER_SYMMETRIC,
    MIRROR_RULE_DIODE_BLOCK,
    MIRROR_RULE_SIGNAL_CROSS_BLOCK,
    MIRROR_RULE_TAIL_RATIO,
    MIRROR_RULE_WHOLE,
    MOS_DRAIN,
    MOS_GATE,
    MOS_SOURCE,
    REL_MATCHING_OFFSET,
    ROLE_BIAS,
    ROLE_DIODE,
    S1_MATCHING_GROUPS_WRITER,
    SIBLING_RULE_GROUND_GATE,
    SIBLING_RULE_OWN_BRANCH_GATE,
    SIBLING_RULE_ROLE,
    STATUS_DERIVED,
    STATUS_PROPOSED,
    STATUS_REVIEW_NEEDED,
    Evidence,
    MatchingDisposition,
    MatchingGroup,
    RelEdge,
)


@compute_block(S1_MATCHING_GROUPS_WRITER, reads=MATCHING_GROUPS_READS, writes=MATCHING_GROUPS_WRITES)
def s1_matching_groups(projection):
    rails = frozenset(net for net, flag in projection.column("node", "is_rail") if flag)
    grounded = frozenset(net for net, cls in projection.column("node", "ac_ground_class") if cls is not None)
    inputs = frozenset(net for net, direction in projection.column("node", "port_direction")
                       if direction == INPUT_DIRECTION)
    element_class = projection.column("device", "element_class")
    mos = tuple(name for name, cls in element_class if cls == ELEMENT_MOS)
    kind = dict(projection.column("device", "kind"))
    pins = {name: dict(p) for name, p in projection.column("device", "pins")}
    is_diode = dict(projection.column("device", "is_diode"))
    roles = dict(projection.column("device", "dc_role"))
    dc_nets = dict(projection.column("device", "dc_nets"))
    resistive = tuple(dc_nets[name] for name, cls in element_class if cls == ELEMENT_PASSIVE and dc_nets[name])
    branches = projection.value("graph", GRAPH_KEY, "branches")
    branch_of, branch_nets, block_of = _dc_places(branches, rails)

    offset, dispositions = _diff_pairs(mos, kind, pins, roles, grounded, rails, branch_of, branch_nets)
    bias = _bias_nets(mos, pins, is_diode, grounded, inputs, block_of, branch_of, branch_nets)
    loop = _loop_nets(mos, pins, resistive, grounded, branch_nets)
    pairs = tuple(r for r in offset if r.status == STATUS_DERIVED)
    split = (frozenset(r.evidence.nets[0] for r in pairs),                 # 꼬리 넷 = derived 차동쌍 공통 source
             frozenset(pins[m][MOS_GATE] for m in mos if is_diode[m]),    # diode 넷
             _counterparts(pairs, branches, pins, dict(element_class), kind, rails))
    groups = []
    for g in projection.value("graph", GRAPH_KEY, "gs_groups"):
        if g.gate not in rails:
            groups.extend(_classify_mirror(g, is_diode, block_of, bias, loop, dispositions, pins, split))
    groups.extend(MatchingGroup(MATCH_DIFF_PAIR, r.members, r.status,
                                Evidence(MATCH_DIFF_PAIR, r.evidence.nets, (), (J_DIFF_PAIR,))) for r in offset)
    groups.extend(_branch_symmetric(groups, mos, kind, pins, rails))
    return {("graph", "rel_matching_offset"): {GRAPH_KEY: offset},
            ("graph", "matching_groups"): {GRAPH_KEY: tuple(groups)},
            ("graph", "matching_dispositions"): {GRAPH_KEY: tuple(dispositions)}}


def _dc_places(branches, rails):
    """(원소 -> 가지 id, 가지 id -> 가지 넷 frozenset, 원소 -> 블록 번호). 블록 = 비레일 끝 넷으로 이은 가지 연결 성분."""
    branch_of = {}
    branch_nets = {}
    by_end = {}
    for b in branches:
        nets = set(b.ends)
        for seg in b.segments:
            nets.update(seg.nets)
            for element in seg.elements:
                branch_of[element] = b.id
        branch_nets[b.id] = frozenset(nets)
        for net in b.ends:
            if net not in rails:
                by_end.setdefault(net, []).append(b.id)
    block = {}
    for b in branches:
        if b.id in block:
            continue
        block[b.id] = b.id
        stack = [b.id]
        while stack:
            here = stack.pop()
            for net in branch_nets[here]:
                for other in by_end.get(net, ()):
                    if other not in block:
                        block[other] = b.id
                        stack.append(other)
    return branch_of, branch_nets, {element: block[bid] for element, bid in branch_of.items()}


def _diff_pairs(mos, kind, pins, roles, grounded, rails, branch_of, branch_nets):
    """차동쌍 후보 RelEdge tuple 과 bias_sibling 기록 list."""
    buckets = {}
    for name in mos:
        if pins[name][MOS_SOURCE] not in rails:
            buckets.setdefault((kind[name], pins[name][MOS_SOURCE]), []).append(name)
    offset = []
    dispositions = []
    for (_, source), names in sorted_items(buckets):
        if len({pins[n][MOS_GATE] for n in names}) > 1:
            excluded = tuple((n, _sibling_rule(n, pins, roles, grounded, branch_of, branch_nets)) for n in names)
            rest = tuple(n for n, rule in excluded if rule is None)
            gates = sorted_items({pins[n][MOS_GATE] for n in rest})
            if len(gates) > 1:
                status = STATUS_DERIVED if len(rest) - 1 == 1 else STATUS_REVIEW_NEEDED
                offset.append(RelEdge(REL_MATCHING_OFFSET, DOMAIN_DC_TO_SS, rest, status,
                                      Evidence(REL_MATCHING_OFFSET, (source,) + gates, (), (J_DIFF_PAIR,))))
            dispositions.extend(
                MatchingDisposition(DISPOSITION_BIAS_SIBLING, (n,), STATUS_PROPOSED,
                                    Evidence(rule, (source, pins[n][MOS_GATE]), rest, (J_DIFF_PAIR, J_MATCH_CLASS)))
                for n, rule in excluded if rule is not None)
    return tuple(offset), dispositions


def _sibling_rule(name, pins, roles, grounded, branch_of, branch_nets):
    """바이어스 형제면 그 근거 rule 이름, 아니면 None(검사 순서 = 아래 순서)."""
    gate = pins[name][MOS_GATE]
    if roles[name].role in (ROLE_DIODE, ROLE_BIAS):
        return SIBLING_RULE_ROLE
    if gate in grounded:
        return SIBLING_RULE_GROUND_GATE
    if gate in branch_nets[branch_of[name]]:
        return SIBLING_RULE_OWN_BRANCH_GATE
    return None


def _bias_nets(mos, pins, is_diode, grounded, inputs, block_of, branch_of, branch_nets):
    """바이어스 넷 B = 바이어스 블록들의 넷 합집합. 바이어스 블록(최대 고정점) = 입력 포트 넷이 없고, 블록 안 비 diode MOS 의
    gate 가 모두 G 또는 (지금) 바이어스 블록 넷인 블록 -- 전부 바이어스 블록에서 시작해 어긋나는 블록을 빼며 반복."""
    nets_of = {}
    for element, bid in branch_of.items():
        nets_of.setdefault(block_of[element], set()).update(branch_nets[bid])
    gates_of = {}
    for name in mos:
        if not is_diode[name]:
            gates_of.setdefault(block_of[name], set()).add(pins[name][MOS_GATE])
    alive = {block for block, nets in nets_of.items() if not nets & inputs}
    changed = True
    while changed:
        changed = False
        held = grounded.union(*(nets_of[block] for block in alive))
        for block in sorted_items(alive):
            if not gates_of.get(block, set()) <= held:
                alive.discard(block)
                changed = True
    return frozenset().union(*(nets_of[block] for block in alive))


def _loop_nets(mos, pins, resistive, grounded, branch_nets):
    """루프 신호 넷 L: 영향 방향 그래프의 강연결 성분 중 MOS 엣지를 품고 한 가지에 갇히지 않는 성분의 넷."""
    adjacency = {}
    mos_edges = set()

    def add(u, v):
        if u != v and u not in grounded and v not in grounded:
            adjacency.setdefault(u, set()).add(v)
            adjacency.setdefault(v, set())
            return True
        return False

    for name in mos:
        p = pins[name]
        for u, v in ((p[MOS_GATE], p[MOS_DRAIN]), (p[MOS_GATE], p[MOS_SOURCE]), (p[MOS_SOURCE], p[MOS_DRAIN])):
            if add(u, v):
                mos_edges.add((u, v))
    for a, b in resistive:
        add(a, b)
        add(b, a)
    loop = set()
    for component in _strong_components(adjacency):
        inside = frozenset(component)
        if (len(inside) > 1 and any((u, v) in mos_edges for u in inside for v in adjacency[u] if v in inside)
                and not any(inside <= nets for nets in branch_nets.values())):
            loop.update(inside)
    return frozenset(loop)


def _strong_components(adjacency):
    """강연결 성분 tuple(Tarjan, 반복형, 노드·이웃 이름순 -- 결정론)."""
    index = {}
    low = {}
    on_stack = set()
    stack = []
    components = []
    counter = 0
    for root in sorted(adjacency):
        if root in index:
            continue
        work = [(root, iter(sorted_items(adjacency[root])))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        while work:
            node, neighbours = work[-1]
            advanced = False
            for other in neighbours:
                if other not in index:
                    index[other] = low[other] = counter
                    counter += 1
                    stack.append(other)
                    on_stack.add(other)
                    work.append((other, iter(sorted_items(adjacency[other]))))
                    advanced = True
                    break
                if other in on_stack:
                    low[node] = min(low[node], index[other])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    top = stack.pop()
                    on_stack.discard(top)
                    component.append(top)
                    if top == node:
                        break
                components.append(tuple(sorted(component)))
    return tuple(components)


def _classify_mirror(g, is_diode, block_of, bias, loop, dispositions, pins, split):
    """gs 미러 후보 하나 -> mirror 그룹 tuple(제외 기록은 dispositions 에 덧붙인다)."""
    nets = (g.gate, g.source)
    diodes = tuple(m for m in g.members if is_diode[m])
    diode_blocks = frozenset(block_of[m] for m in diodes)
    consumers = tuple(m for m in g.members if diodes and block_of[m] not in diode_blocks)
    if not consumers:
        return (MatchingGroup(MATCH_MIRROR, g.members, STATUS_DERIVED, Evidence(MIRROR_RULE_WHOLE, nets, diodes)),)
    if g.gate in bias:
        excluded = DISPOSITION_BIAS_DISTRIBUTION
    elif g.gate in loop:
        excluded = DISPOSITION_FEEDBACK_SHARED
    else:
        return (MatchingGroup(MATCH_MIRROR, g.members, STATUS_DERIVED,
                              Evidence(MIRROR_RULE_SIGNAL_CROSS_BLOCK, nets, diodes, (J_MATCH_CLASS,))),)
    out = []
    home = tuple(m for m in g.members if m not in consumers)
    if len(home) > 1:
        out.append(MatchingGroup(MATCH_MIRROR, home, STATUS_DERIVED,
                                 Evidence(MIRROR_RULE_DIODE_BLOCK, nets, diodes, (J_MATCH_CLASS,))))
    by_block = {}
    for m in consumers:
        by_block.setdefault(block_of[m], []).append(m)
    tails = []
    for members in sorted_items(tuple(ms) for ms in by_block.values()):
        if len(members) > 1:
            tail, rest = _split_consumer_block(members, nets, diodes, pins, split, out)
            tails.extend(tail)
            if len(rest) > 1:
                out.append(MatchingGroup(MATCH_MIRROR, rest, STATUS_DERIVED,
                                         Evidence(MIRROR_RULE_CONSUMER_BLOCK, nets, diodes, (J_MATCH_CLASS,))))
    if tails:
        out.append(MatchingGroup(MATCH_MIRROR, tuple(sorted(diodes + tuple(tails))), STATUS_DERIVED,
                                 Evidence(MIRROR_RULE_TAIL_RATIO, nets, diodes, (J_MATCH_CLASS,))))
    left = tuple(m for m in consumers if m not in tails)
    if left:
        dispositions.append(MatchingDisposition(excluded, left, STATUS_PROPOSED,
                                                Evidence(excluded, nets, diodes, (J_MATCH_CLASS,))))
    return tuple(out)


def _split_consumer_block(members, nets, diodes, pins, split, out):
    """같은 블록 소비 소자(2개 이상) 세분(J14 1번, CONTRACT 4.5a): 꼬리(drain = derived 차동쌍 공통 source) -> 돌려줌,
    diode 넷 drain -> 그룹 없음(제외 기록만), drain 이 대응 넷 쌍인 두 소자 -> 대칭쌍 그룹(out 에 추가).
    하나도 해당 없으면 묶음 그대로(옛 consumer_block). (꼬리 tuple, consumer_block 으로 남길 tuple) 반환."""
    tail_nets, diode_nets, partner = split
    tails = tuple(m for m in members if pins[m][MOS_DRAIN] in tail_nets)
    fed = tuple(m for m in members if m not in tails and pins[m][MOS_DRAIN] in diode_nets)
    open_ = tuple(m for m in members if m not in tails and m not in fed)
    by_drain = {}
    for m in open_:
        by_drain.setdefault(pins[m][MOS_DRAIN], []).append(m)
    paired = []
    for drain, ms in sorted_items(by_drain):
        other = partner.get(drain)
        if other in by_drain and drain < other and len(ms) - 1 == 0 and len(by_drain[other]) - 1 == 0:
            pair = tuple(sorted(ms + by_drain[other]))
            paired.extend(pair)
            out.append(MatchingGroup(MATCH_MIRROR, pair, STATUS_DERIVED,
                                     Evidence(MIRROR_RULE_CONSUMER_SYMMETRIC, nets + (drain, other), diodes,
                                              (J_MATCH_CLASS,))))
    if not (tails or fed or paired):
        return tails, members
    return tails, tuple(m for m in open_ if m not in paired)


def _counterparts(pairs, branches, pins, element_class, kind, rails):
    """대응 넷 사상 {넷: 짝 넷}(CONTRACT 4.5a). seed = derived 2멤버 차동쌍의 두 drain. 두 가지의 걷는 넷 열이 길이와
    segment 원소 (분류, kind) 다중집합 열이 같고, 같은 자리 넷이 같거나(끝 자리만) 대응이며 대응 자리가 하나 이상이면 나머지
    다른 자리 넷끼리 대응으로 더한다 -- 고정점까지. 레일은 대응시키지 않는다. 한 넷이 두 넷에 대응되면(충돌) 관련 넷을 모두 뺀다."""
    partner = {}
    clash = set()

    def link(a, b):
        if a == b or a in clash or b in clash or partner.get(a) == b:
            return False
        if a in partner or b in partner:
            clash.update(x for x in (a, b, partner.get(a), partner.get(b)) if x is not None)
            return False
        partner[a] = b
        partner[b] = a
        return True

    for r in pairs:
        a, b = r.members
        link(pins[a][MOS_DRAIN], pins[b][MOS_DRAIN])
    walks = []
    for br in branches:
        seq = [br.ends[0]]
        sig = []
        for seg in br.segments:
            seq.append(seg.nets[1] if seg.nets[0] == seq[-1] else seg.nets[0])
            sig.append(tuple(sorted((element_class[e], kind[e]) for e in seg.elements)))
        walks.append((tuple(seq), tuple(sig)))
        walks.append((tuple(reversed(seq)), tuple(reversed(sig))))
    changed = True
    while changed:
        changed = False
        for i, (w1, s1) in enumerate(walks):
            for w2, s2 in walks[i + 1:]:
                if s1 == s2 and w1 != w2 and w1 != tuple(reversed(w2)):
                    changed = _match_walks(w1, w2, partner, clash, rails, link) or changed
    return {a: b for a, b in partner.items() if a not in clash and b not in clash}


def _match_walks(w1, w2, partner, clash, rails, link):
    """두 걷는 넷 열(같은 길이)이 대응 조건을 만족하면 다른 자리 넷끼리 link, 새로 더한 것이 있으면 True."""
    last = len(w1) - 1
    known = False
    for i, (a, b) in enumerate(zip(w1, w2)):
        if a == b:
            if 0 < i < last:
                return False
        elif a in rails or b in rails or a in clash or b in clash:
            return False
        elif a in partner or b in partner:
            if partner.get(a) != b:
                return False
            known = True
    if not known:
        return False
    added = False
    for a, b in zip(w1, w2):
        added = link(a, b) or added
    return added


def _branch_symmetric(seeds, mos, kind, pins, rails):
    """derived seed 위 stack 전파 고정점 -> branch_symmetric 그룹 tuple(찾은 순서)."""
    by_source = {}
    for name in mos:
        by_source.setdefault((kind[name], pins[name][MOS_SOURCE]), []).append(name)
    seen = {frozenset(s.members) for s in seeds}
    queue = [s for s in seeds if s.status == STATUS_DERIVED]
    found = []
    for seed in queue:
        uppers = {}
        for m in seed.members:
            drain = pins[m][MOS_DRAIN]
            if drain not in rails:
                for u in by_source.get((kind[m], drain), ()):
                    if u not in seed.members:
                        uppers.setdefault(pins[u][MOS_GATE], set()).add(u)
        for gate, devices in sorted_items(uppers):
            sources = sorted_items({pins[u][MOS_SOURCE] for u in devices})
            members = tuple(sorted(devices))
            if len(sources) > 1 and frozenset(members) not in seen:
                seen.add(frozenset(members))
                group = MatchingGroup(MATCH_BRANCH_SYMMETRIC, members, STATUS_DERIVED,
                                      Evidence(MATCH_BRANCH_SYMMETRIC, (gate,) + sources, seed.members,
                                               (J_BRANCH_SYMMETRIC,)))
                found.append(group)
                queue.append(group)
    return tuple(found)
