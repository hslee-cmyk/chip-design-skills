"""MOD7 Euler 조건 판정 `check_euler_condition`(+`EulerVerdict`) -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations

from dataclasses import dataclass

from .euler_graph import StackGraph


def _degrees(g: StackGraph) -> dict:
    return {n: len(g.adjacency[n]) for n in g.nodes}


def _is_connected_ignoring_isolated(g: StackGraph) -> bool:
    active = [n for n in g.nodes if g.adjacency[n]]
    if not active:
        return True
    seen = {active[0]}
    stack = [active[0]]
    while stack:
        v = stack.pop()
        for edge_id, u in g.adjacency[v]:
            if u not in seen:
                seen.add(u)
                stack.append(u)
    return seen.issuperset(active)


@dataclass
class EulerVerdict:
    kind: str                # 'circuit' | 'path' | 'impossible'
    odd_nodes: list
    connected: bool
    start: str | None = None
    end: str | None = None


def check_euler_condition(g: StackGraph) -> EulerVerdict:
    """PDF/pptx가 명시한 3가지 오일러 조건을 그대로 판정한다:
    0개 홀수차수 → circuit(닫힌 한붓그리기), 2개 → path(열린 한붓그리기), 4개 이상 → impossible.
    연결성도 함께 확인한다(차수 조건을 만족해도 그래프가 끊겨 있으면 한 줄 diffusion으로 불가능).

    검사하지 않는 것: 입력 `g`가 실제 회로 connectivity를 정확히 반영하는지는 검사하지
    않는다 -- PMOS/NMOS kind 동질성 같은 입력 유효성은 `build_graph()`가 이미 보장했다고
    가정하고, 이 함수는 주어진 그래프의 차수/연결성만 판정한다.
    영역: 없음(배치)
    """
    degrees = _degrees(g)
    odd_nodes = sorted(n for n, d in degrees.items() if d % 2 == 1)
    connected = _is_connected_ignoring_isolated(g)

    if not connected:
        return EulerVerdict("impossible", odd_nodes, connected)
    if len(odd_nodes) == 0:
        # ⚠️ 2026-07-27 실제 사고: `g.nodes`가 set이라 `next(iter(...))`의 결과가 프로세스마다
        # 다르다(문자열 hash가 PYTHONHASHSEED로 랜덤화되는 CPython 기본 동작 때문 -- 실측
        # 확인: 동일 입력을 별도 프로세스 3번 실행해 서로 다른 3가지 transistor_sequence를
        # 얻었다). 같은 입력이 실행마다 다른 배치로 나오면 audit_row_split()의 interdigitation/
        # common-centroid 판정도 실행마다 뒤집힐 수 있어 검증 게이트로서 신뢰할 수 없다 --
        # `sorted()`로 시작 노드를 고정해 재현 가능하게 만든다(어떤 시작 노드를 고르든 Euler
        # circuit 자체의 유효성엔 영향이 없으므로, 고정한다고 판정 결과가 왜곡되지 않는다).
        start = min((n for n in g.nodes if g.adjacency[n]), default=None)
        return EulerVerdict("circuit", odd_nodes, connected, start=start, end=start)
    if len(odd_nodes) == 2:
        return EulerVerdict("path", odd_nodes, connected, start=odd_nodes[0], end=odd_nodes[1])
    return EulerVerdict("impossible", odd_nodes, connected)
