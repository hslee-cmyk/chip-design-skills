"""MOD7 물리 행 하나의 finger 순서 -- Euler 판정·거울대칭 trail·최소 crossover (design_mod7_layout.md 3절 4단계).

진입점: `row_euler(transistors, matching_pairs, pair_sensitivity) -> dict`.

복사 함수를 이 순서로 부른다(W 불변 -- finger 수를 바꾸지 않는다):
  소자 연결(source·drain 넷)로 diffusion 섬(연결 성분)을 나누고, 섬마다
  `build_graph` -> `check_euler_condition` -> (섬 안 matching 쌍이 있으면 `mirror_symmetric_trail`) -> `hierholzer`,
  Euler 불가면 `find_min_crossover_layout`(쌍 = 섬 안 matching 쌍, `pair_sensitivity` = 쌍별 "offset"/"ratio").
섬 사이 경계와 crossover 경계는 segment 경계다. 결과는 `canonical_row` 로 정규화(복사본 set 순회 결정론 결함 보정).
"""
from .canonical_rows import canonical_row
from .crossover import find_min_crossover_layout
from .euler_condition import check_euler_condition
from .euler_graph import build_graph
from .euler_trail import hierholzer
from .mirror_trail import mirror_symmetric_trail


def _components(transistors):
    """source·drain 넷으로 이어진 소자 묶음들(각 묶음은 이름 정렬, 묶음은 첫 이름 정렬)."""
    by_net = {}
    for t in transistors:
        by_net.setdefault(t.source, []).append(t.name)
        by_net.setdefault(t.drain, []).append(t.name)
    by_name = {t.name: t for t in transistors}
    seen = set()
    out = []
    for name in sorted(by_name):
        if name in seen:
            continue
        stack = [name]
        comp = set()
        while stack:
            cur = stack.pop()
            if cur in comp:
                continue
            comp.add(cur)
            t = by_name[cur]
            stack.extend(by_net[t.source])
            stack.extend(by_net[t.drain])
        seen |= comp
        out.append(tuple(by_name[n] for n in sorted(comp)))
    return out


def row_euler(transistors, matching_pairs, pair_sensitivity):
    """`transistors`(같은 kind, `n_fingers` 확정)의 한 물리 행 배치.

    반환 dict: `transistor_sequence`·`node_sequence`·`segments`(list of {transistor_sequence, node_sequence})·
    `crossover_after`(segment 경계 직전 finger index)·`method`("euler"|"mirror"|"crossover")·`crossover_count`·`n_components`.
    """
    segments = []
    methods = set()
    crossover_count = 0
    components = _components(transistors)
    for comp in components:
        names = {t.name for t in comp}
        pairs = [p for p in matching_pairs if p[0] in names and p[1] in names]
        graph = build_graph(list(comp))
        verdict = check_euler_condition(graph)
        if verdict.kind != "impossible":
            trail = mirror_symmetric_trail(list(comp), pairs) if pairs else None
            if trail is not None:
                methods.add("mirror")
                segments.append({"transistor_sequence": trail["transistor_sequence"],
                                 "node_sequence": trail["node_sequence"]})
                continue
            nodes, seq = hierholzer(graph, verdict.start)
            methods.add("euler")
            segments.append({"transistor_sequence": seq, "node_sequence": nodes})
            continue
        sens = {p: pair_sensitivity[p] for p in pairs} if pairs else None
        layout = find_min_crossover_layout(list(comp), matching_pairs=pairs, pair_sensitivity=sens)
        methods.add("crossover")
        crossover_count += layout["crossover_count"]
        segments.extend(layout["segments"])
    crossover_after = []
    cursor = -1
    for seg in segments[:-1]:
        cursor += len(seg["transistor_sequence"])
        crossover_after.append(cursor)
    row = {
        "transistor_sequence": [name for seg in segments for name in seg["transistor_sequence"]],
        "segments": segments,
        "crossover_after": crossover_after,
    }
    row = canonical_row(row, transistors)
    row["method"] = "crossover" if "crossover" in methods else ("mirror" if "mirror" in methods else "euler")
    row["crossover_count"] = crossover_count
    row["n_components"] = len(components)
    return row
