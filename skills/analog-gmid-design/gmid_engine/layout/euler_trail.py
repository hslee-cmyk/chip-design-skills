"""MOD7 Hierholzer 순회 `hierholzer` -- 옛 stick_diagram.py 본문 복사(L10).

복사 정의의 SD 행·AST 해시·본문 리터럴 집합은 `_copy_manifest.py`. 정의 본문(docstring·주석 포함)은
수정 금지 -- 바꾸려면 복사를 끊고 새 정의로 쓰며 manifest 항목을 지운다.
"""
from __future__ import annotations


from .euler_graph import StackGraph


def hierholzer(g: StackGraph, start: str) -> tuple[list, list]:
    """오일러 경로/회로가 존재한다는 전제 하에 실제 순회 순서를 구한다(반복문 버전, 재귀 깊이 문제 없음).

    반환: (node_sequence, transistor_sequence) — transistor_sequence[i]는
    node_sequence[i]에서 node_sequence[i+1]로 갈 때 쓰인 트랜지스터 이름이다
    (길이는 node_sequence보다 1 짧다)."""
    adj = {n: list(v) for n, v in g.adjacency.items()}
    used = set()
    stack = [(start, None)]           # (node, 여기 도착할 때 쓴 edge_id)
    circuit = []                       # 역순으로 쌓인다

    while stack:
        v, arrive_edge = stack[-1]
        advanced = False
        while adj[v]:
            edge_id, u = adj[v].pop()
            if edge_id in used:
                continue
            used.add(edge_id)
            stack.append((u, edge_id))
            advanced = True
            break
        if not advanced:
            circuit.append(stack.pop())

    circuit.reverse()
    node_sequence = [c[0] for c in circuit]
    transistor_sequence = [g.edges[c[1]][0] for c in circuit[1:]]
    return node_sequence, transistor_sequence
