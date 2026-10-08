"""루프 끊는 점 후보 (설계 41 §1.8 '끊는 점', 계획 N3.2-2 '끊는 점').

진입점: `loop_cut_candidates(cycle, cells, dist) -> tuple`  (((소자, gate 넷), ...) 사이클 위치 순, 중복 없음. 후보가 없으면 빈 tuple).

끊는 점 후보 = 루프 위에서 **gate 엣지(gate->drain 또는 gate->source)를 가진 CS 셀의 gate**. CS 셀이 루프를 source->drain 엣지로 지나가면 그 gate 는 루프 밖이라
끊어도 루프가 열리지 않으므로 후보가 아니다. **복귀 경로**(거리가 늘지 않는 엣지의 극대 연속 구간)가 있으면 후보는 **각 복귀 구간 바로 다음 첫 gate** 이고,
복귀 구간이 없으면 사이클의 모든 후보다. 구간이 여럿이면 후보도 여럿이 되는데, 그중 어느 것을 쓸지는 사이클 표현(이름 정렬 첫 노드에서 시작)에 의존하지 않도록
**뷰의 모든 루프에서 가장 많이 나타나는 후보**로 `view_analysis` 가 고른다(이름 전단사 불변). 후보가 없으면 `loop_no_cut_candidate` review_needed.
"""
from .s1v_values import CELL_CS, EDGE_GATE_DRAIN, EDGE_GATE_SOURCE


def _is_candidate(edge, kind):
    return edge.etype in (EDGE_GATE_DRAIN, EDGE_GATE_SOURCE) and kind.get(edge.element) == CELL_CS


def _return_ends(cycle, dist):
    """복귀 구간(거리가 늘지 않는 엣지의 극대 연속 구간, 원형)이 끝나는 엣지 위치들."""
    reverse = [e.src in dist and e.dst in dist and dist[e.dst] <= dist[e.src] for e in cycle]
    if all(reverse):
        return []
    return [i for i, flag in enumerate(reverse) if flag and not reverse[(i + 1) % len(cycle)]]


def loop_cut_candidates(cycle, cells, dist):
    kind = {c.dev: c.kind for c in cells.cells}
    ends = _return_ends(cycle, dist)
    starts = [(i + 1) % len(cycle) for i in ends] or [0]
    found = []
    for start in starts:
        for step in range(len(cycle)):
            edge = cycle[(start + step) % len(cycle)]
            if _is_candidate(edge, kind):
                if (edge.element, edge.src) not in found:
                    found.append((edge.element, edge.src))
                break
    return tuple(found)
