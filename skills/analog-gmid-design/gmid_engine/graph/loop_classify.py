"""루프 분류 (설계 41 §1.8 '분류', 계획 N3.2-2 (0)~(4)).

진입점: `classify_loops(cycles, forward, cells, dist, view_id) -> ClassifiedLoops`.

사이클마다 **앞 번호에 해당하면 뒤 번호는 보지 않는 순서**로 판정한다 (자기 엣지 (0)은 열거에서 이미 제외, 교류접지·여기 포트를 지나는 경로 (1)도 그래프에서
제외됐다):
* (1.5) **바이어스 SCC**: 사이클의 노드가 이 뷰 순방향 집합 F 에 하나도 없다. 루프 뷰를 만들지 않고 DC 루프로만 기록한다.
* (2) **Miller형**: 사이클 안에 **커패시터를 포함한 수동소자만의 극대 구간**이 있고 그 구간의 양 끝 노드가 모두 F 위다. 복귀 경로 거리에 의존하지
  않는다. (3-b)도 만족하면 **둘 다** 단다.
* (3-a) 어느 순방향 경로에도 없는 능동 셀(셀이 CS·CG·CD 인데 순방향이 아님)을 포함: library 발동 0 이라 만나면 `loop_active_cell_off_forward`
  (review_needed)로 보고하고 루프 뷰로도 센다.
* (3-b) **복귀 경로에 능동 셀이 있고 뒤에서 앞으로 돌아오는** 루프: 복귀 경로 = 뷰 입력에서의 0-1 BFS 거리가 **늘지 않는**(동률 포함) 엣지의 극대 연속 구간.
  경로의 시작 거리가 끝 거리보다 커야 한다(뒤 블록 -> 앞 블록). 배타 (가) 복귀 경로가 수동소자만이면 (3-b) 가 아니다, (나) 복귀 경로가 수동소자 없이 능동
  셀(소자) 둘로만 닫히면 J12-h 판정 전까지 (3-b) 로 보지 않고 `기록만`(사유 '수동소자 없는 2능동셀 루프').
* (4) 나머지: 전역 되먹임·교차결합 -- `기록만`(`loop_record_only`, 항상 DEC-59 정지).
classes 는 tuple 이다(둘 이상이면 모두 단다).
"""
import dataclasses

from .s1v_values import (
    PAIR,
    CELL_CD,
    CELL_CG,
    CELL_CS,
    EDGE_CAPACITOR,
    EDGE_PASS,
    F_LOOP_3A,
    F_LOOP_RECORD_ONLY,
    LOOP_BIAS_SCC,
    LOOP_MILLER,
    LOOP_RECORD_ONLY,
    LOOP_VIEW,
    PASSIVE_EDGES,
    SEVERITY_REVIEW,
    SEVERITY_UNSUPPORTED,
    Finding,
)

REASON_TWO_ACTIVE = "two_active_cells_without_passive"
REASON_GLOBAL = "global_feedback_or_cross_coupled"


@dataclasses.dataclass(frozen=True)
class ClassifiedLoops:
    """`entries` = 사이클마다 (classes tuple, 기록 사유 문자열), `findings` = 기록."""

    entries: tuple
    findings: tuple


def _rotate_to_boundary(cycle, flags):
    """flags[i] 가 False 인 엣지에서 시작하도록 회전. 모두 True 면 그대로(전체가 한 구간)."""
    for i, flag in enumerate(flags):
        if not flag:
            return cycle[i:] + cycle[:i], flags[i:] + flags[:i], True
    return cycle, flags, False


def _runs(cycle, flags):
    """flag 가 True 인 극대 연속 엣지 구간들(원형)."""
    rotated, rflags, split = _rotate_to_boundary(cycle, flags)
    runs = []
    current = []
    for edge, flag in zip(rotated, rflags):
        if flag:
            current.append(edge)
        elif current:
            runs.append(tuple(current))
            current = []
    if current:
        runs.append(tuple(current))
    return runs if split else [tuple(cycle)]


def _is_miller(cycle, forward):
    flags = tuple(e.etype in PASSIVE_EDGES for e in cycle)
    return any(any(e.etype == EDGE_CAPACITOR for e in run) and run[0].src in forward and run[-1].dst in forward
               for run in _runs(cycle, flags) if all(e.etype in PASSIVE_EDGES for e in run))


def _devices(edges):
    names = set()
    for e in edges:
        if e.etype == EDGE_PASS:
            names.update(e.element)
        elif e.etype not in PASSIVE_EDGES:
            names.add(e.element)
    return names


def _returns(cycle, dist):
    flags = tuple(e.dst in dist and e.src in dist and dist[e.dst] <= dist[e.src] for e in cycle)
    return [run for run in _runs(cycle, flags) if all(dist.get(e.dst, 0) <= dist.get(e.src, 0) for e in run)
            and dist.get(run[0].src, 0) > dist.get(run[-1].dst, 0)]


def _three_b(cycle, dist):
    """(3-b) 만족 여부와 (나) 배타 때문에 기록만이 된 여부."""
    qualified = False
    two_active = False
    for run in _returns(cycle, dist):
        active = [e for e in run if e.etype not in PASSIVE_EDGES]
        if not active:
            continue
        has_passive = any(e.etype in PASSIVE_EDGES for e in run)
        if not has_passive and len(_devices(run)) == len(PAIR):
            two_active = True
        else:
            qualified = True
    return qualified, two_active and not qualified


def classify_loops(cycles, forward, cells, dist, view_id):
    kind = {c.dev: (c.kind, c.forward) for c in cells.cells}
    entries = []
    findings = []
    for cycle in cycles:
        nodes = {e.src for e in cycle}
        if not nodes & forward:
            entries.append(((LOOP_BIAS_SCC,), ""))
            continue
        classes = []
        reason = ""
        if _is_miller(cycle, forward):
            classes.append(LOOP_MILLER)
        off_forward = sorted(n for n in _devices(cycle) if n in kind and kind[n][0] in (CELL_CS, CELL_CG, CELL_CD) and not kind[n][1])
        three_b, record_two = _three_b(cycle, dist)
        if off_forward:
            findings.append(Finding(F_LOOP_3A, SEVERITY_REVIEW, view_id, tuple(off_forward),
                                    "순방향 경로에 없는 능동 셀을 지나는 루프 (3-a)", ("N3.2-2", "DEC-76")))
        if off_forward or three_b:
            classes.append(LOOP_VIEW)
        if not classes:
            reason = REASON_TWO_ACTIVE if record_two else REASON_GLOBAL
            classes.append(LOOP_RECORD_ONLY)
            findings.append(Finding(F_LOOP_RECORD_ONLY, SEVERITY_UNSUPPORTED, view_id, tuple(sorted(nodes)), reason,
                                    ("N3.2-2 (4)", "DEC-59")))
        entries.append((tuple(classes), reason))
    return ClassifiedLoops(tuple(entries), tuple(findings))
