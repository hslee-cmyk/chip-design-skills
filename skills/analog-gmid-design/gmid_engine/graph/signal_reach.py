"""신호 넷 최소 고정점과 순방향 집합 (설계 41 §1.3, 계획 N3.2-3 '신호 경로 도달성').

진입점: `signal_reach(model, ground, seeds, sense) -> Reach`.

* 신호 넷 S = `seeds`(여기 포트 넷)에서 시작해 아래 세 규칙을 더 늘지 않을 때까지 반복한 최소 고정점. `ground`(교류접지) 넷은
  넣지 않는다.
  (a) 신호 넷을 gate 로 받는 소자의 drain·source 넷  (b) 신호 넷을 source 로 받는 소자의 drain 넷
  (c) 신호 넷에 붙은 2단자 수동소자(저항·커패시터)의 반대쪽 단자 넷. 이상 전류원은 소신호에서 열린 경로라 넣지 않는다.
* 이 세 규칙이 만드는 방향 엣지는 `Reach.edges`((from, to) 정렬 tuple, 중복 없음)로 함께 낸다 -- 셀 분류 전에 계산되므로
  구동 종류 -> 엣지 -> 순방향 -> 셀 순환이 없다(plan 규칙 3).
* 순방향 집합 F = S 중 `sense` 넷으로 이 엣지를 따라 도달하는 넷(= 여기에서 도달하고 출력으로 역도달). `sense` 가 교류접지면 도달할
  수 없어 F 는 비다.
"""
import dataclasses

from gmid_engine.core import sorted_items


@dataclasses.dataclass(frozen=True)
class Reach:
    """`signal` = 신호 넷, `forward` = 순방향 넷, `edges` = 신호 엣지 (from, to) 정렬 tuple."""

    signal: frozenset
    forward: frozenset
    edges: tuple


def _successors(model, net):
    out = []
    for m in model.by_gate.get(net, ()):
        out.extend((m.d, m.s))
    for m in model.by_source.get(net, ()):
        out.append(m.d)
    for p in model.by_passive.get(net, ()):
        out.append(p.b if p.a == net else p.a)
    return out


def signal_reach(model, ground, seeds, sense):
    seen = {net for net in seeds if net not in ground}
    edges = set()
    pending = sorted(seen)
    while pending:
        net = pending.pop()
        for nxt in _successors(model, net):
            if nxt in ground or nxt == net:
                continue
            edges.add((net, nxt))
            if nxt not in seen:
                seen.add(nxt)
                pending.append(nxt)
    reverse = {}
    for src, dst in edges:
        reverse.setdefault(dst, []).append(src)
    forward = {net for net in sense if net in seen}
    pending = sorted(forward)
    while pending:
        net = pending.pop()
        for prev in reverse.get(net, ()):
            if prev not in forward:
                forward.add(prev)
                pending.append(prev)
    return Reach(frozenset(seen), frozenset(forward), sorted_items(edges))
