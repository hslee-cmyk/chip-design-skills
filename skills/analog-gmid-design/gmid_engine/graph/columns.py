"""DC 기둥 -- 레일 쌍 사이 가지 그래프의 노드-단순 경로 열거 (설계 design_mod3_structure_u2_u5 1.2 단계 5~7, DEC-71 (1)(3)).

진입점: `s1_columns` -- core `@compute_block`(writer `S1_COLUMNS_WRITER`, reads `COLUMNS_READS`, extras `(column_limit,)`,
writes `graph.columns`·`graph.column_pairs`·`graph.column_orphans`).

    snapshot = s1_columns(snapshot, column_limit)      # column_limit = int 또는 None(상한 없음)

* 레일 쌍 (r1, r2), r1 < r2 이름순, 모든 쌍(J13-c 기본안)마다 가지 그래프(노드 = 가지 끝 넷, 엣지 = 가지)에서 r1 -> r2
  노드-단순 경로를 DFS 로 열거한다. 내부 노드는 레일이 아니다. 이웃 순서 = (반대 넷, 가지 id). 양 끝이 같은 가지는 경로에
  들 수 없다.
* `Column(id, rails, branch_order, parallel_expansion, status=derived, evidence)` -- `parallel_expansion` = 경로 위 segment
  원소 수의 곱(병렬 소자를 따로 셀 때의 경로 수; 회로의 '따로 센' 기둥 수 = 이 값의 합). evidence.basis 에 기댄 J 기본안
  (J13-a 병렬 합침, J13-b 가지치기 순서, J13-c 레일 쌍, 경로에 이상원 가지가 있으면 J13-d).
* `column_pairs` = ((r1, r2, 기둥 수), ...) -- 0 인 쌍도 기록(정지 아님, J13-c).
* `column_orphans` = 어느 쌍의 기둥에도 들지 않는 가지 `ColumnOrphan(branch, review_needed)`(정지 아님).
* 하단/상단 레일 구분은 전위(supplies)가 필요해 여기서 하지 않는다(GB7 `rail_v` 소비자 몫 -- supplies 변경이 이 블록을 다시
  돌리지 않게).
* 열거 수가 `column_limit` 를 넘으면 그 자리에서 멈추고 `column_enumeration_over_budget` 정지(core
  `StructureUnresolvedError`, detail reason `unsupported_rule_branch`, `limit`). 상한은 build_s1 인자(열린 결정 O1 기본안).
"""
import math

from gmid_engine.core import StructureUnresolvedError, compute_block, sorted_items

from .s1_values import (
    BRANCH_COLUMN_BUDGET,
    COLUMN_RULE,
    COLUMNS_READS,
    COLUMNS_WRITES,
    GRAPH_KEY,
    J_IDEAL_SOURCE,
    J_PARALLEL_MERGE,
    J_PRUNE_ORDER,
    J_RAIL_PAIRS,
    S1_COLUMNS_WRITER,
    STATUS_DERIVED,
    STATUS_REVIEW_NEEDED,
    UNSUPPORTED_RULE_BRANCH,
    Column,
    ColumnOrphan,
    Evidence,
)


@compute_block(S1_COLUMNS_WRITER, reads=COLUMNS_READS, writes=COLUMNS_WRITES)
def s1_columns(projection):
    (limit,) = projection.extras
    branches = projection.value("graph", GRAPH_KEY, "branches")
    rails = tuple(net for net, flag in projection.column("node", "is_rail") if flag)
    by_id = {b.id: b for b in branches}
    neighbors = {}
    for b in branches:
        a, z = b.ends
        if a != z:
            neighbors.setdefault(a, []).append((z, b.id))
            neighbors.setdefault(z, []).append((a, b.id))
    for entries in neighbors.values():
        entries.sort()
    rail_set = frozenset(rails)
    columns = []
    pairs = []
    for i, r1 in enumerate(rails):
        for r2 in rails[i + 1:]:
            paths = _paths(neighbors, rail_set, r1, r2, limit, len(columns))
            pairs.append((r1, r2, len(paths)))
            for path in paths:
                members = tuple(by_id[x] for x in path)
                basis = (J_PARALLEL_MERGE, J_PRUNE_ORDER, J_RAIL_PAIRS) + (
                    (J_IDEAL_SOURCE,) if any(b.has_ideal_source for b in members) else ())
                expansion = math.prod(len(seg.elements) for b in members for seg in b.segments)
                columns.append(Column(len(columns), (r1, r2), path, expansion, STATUS_DERIVED,
                                      Evidence(COLUMN_RULE, (r1, r2), (), basis)))
    covered = frozenset(x for c in columns for x in c.branch_order)
    orphans = tuple(ColumnOrphan(b.id, STATUS_REVIEW_NEEDED) for b in branches if b.id not in covered)
    return {("graph", "columns"): {GRAPH_KEY: tuple(columns)},
            ("graph", "column_pairs"): {GRAPH_KEY: tuple(pairs)},
            ("graph", "column_orphans"): {GRAPH_KEY: orphans}}


def _paths(neighbors, rails, start, goal, limit, already):
    """start -> goal 노드-단순 경로(가지 id tuple)들. 내부 노드는 레일 아님. 누적 수가 limit 를 넘으면 정지."""
    found = []
    visited = {start}
    trail = []

    def walk(net):
        for other, branch in neighbors.get(net, ()):
            if other == goal:
                found.append(tuple(trail) + (branch,))
                if limit is not None and already + len(found) > limit:
                    raise StructureUnresolvedError(detail={
                        "reason": UNSUPPORTED_RULE_BRANCH, "rule_branch": BRANCH_COLUMN_BUDGET, "limit": limit,
                        "rails": (start, goal)})
            elif other not in rails and other not in visited:
                visited.add(other)
                trail.append(branch)
                walk(other)
                trail.pop()
                visited.discard(other)

    walk(start)
    return found
